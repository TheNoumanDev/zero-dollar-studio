import React from "react";
import { Img, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import type { CastMember, EpisodeLine } from "./types";

/**
 * Character rigs for cartoon episodes.
 * - BustRig: a close-up whose mouth follows Rhubarb cues. The base face stays put;
 *   the aligned face for the current mouth shape shows only inside a soft mask
 *   around the mouth (tools/viseme_align.py), so eyes and outline never jump.
 * - PoseSprite: a full-body pose cut-out that breathes, and bounces while its owner talks.
 */

/** The line `who` is in at `ms` (absolute): speaking it, or "all" lines. */
const lineAt = (lines: EpisodeLine[], who: string, ms: number) =>
  lines.find((l) => (l.speaker === who || l.speaker === "all") && ms >= l.startMs && ms < l.endMs);

/** Loudness (0–1) of `who`'s voice at `ms`. */
export const talkLevel = (lines: EpisodeLine[], who: string, ms: number, fps: number) => {
  const line = lineAt(lines, who, ms);
  return line ? (line.envelope[Math.floor(((ms - line.startMs) / 1000) * fps)] ?? 0) : 0;
};

/** The mouth shape at `ms`, or null for the closed base face. */
const shapeAt = (lines: EpisodeLine[], who: string, ms: number, fps: number, byLoudness: boolean) => {
  const line = lineAt(lines, who, ms);
  if (!line) return null;
  const env = talkLevel(lines, who, ms, fps);
  if (!line.mouthCues) {
    // No Rhubarb: open the mouth by loudness alone.
    return env > 0.6 ? "D" : env > 0.32 ? "C" : env > 0.1 ? "B" : null;
  }
  const t = ms - line.startMs;
  let shape = line.mouthCues.find((c) => t >= c.startMs && t < c.endMs)?.shape ?? "X";
  // Rhubarb's phonetic mode (non-English) under-opens open vowels: let loudness pick B/C/D.
  if (byLoudness && (shape === "B" || shape === "C" || shape === "D")) shape = env > 0.6 ? "D" : env > 0.32 ? "C" : "B";
  return shape !== "X" && shape !== "A" ? shape : null;
};

/** The face `who` pulls at `ms`: the line's `expression` for its speaker, `react` for listeners. */
export const expressionAt = (lines: EpisodeLine[], who: string, ms: number) => {
  let cur: EpisodeLine | undefined;
  for (const l of lines) if (l.startMs - 120 <= ms) cur = l;
  if (!cur) return undefined;
  return cur.speaker === who ? cur.expression : cur.react?.[who];
};

export const BustRig: React.FC<{
  who: string;
  member: CastMember;
  seriesId: string;
  lines: EpisodeLine[];
  /** Absolute ms of this Sequence's start, so cues line up with the voice. */
  offsetMs: number;
  /** Non-English: Rhubarb ran in phonetic mode. */
  byLoudness: boolean;
  /** Bust height in px; it's centred at x (0–1 of the frame) with its bottom on `ground` (px). */
  height: number;
  x: number;
  ground: number;
  flip?: boolean;
}> = ({ who, member, seriesId, lines, offsetMs, byLoudness, height, x, ground, flip }) => {
  const frame = useCurrentFrame();
  const { fps, width: W } = useVideoConfig();
  const ms = offsetMs + (frame / fps) * 1000;
  const rig = member.rig;
  const expression = expressionAt(lines, who, ms);
  const usable = expression && rig?.expressions.indexOf(expression) !== -1 ? expression : undefined;
  const shape = usable ? null : shapeAt(lines, who, ms, fps, byLoudness);
  const env = talkLevel(lines, who, ms, fps);
  const w = rig ? (rig.width / rig.height) * height : height * 0.9;
  // Idle breathing, plus a little head bob and tilt while talking.
  const breathe = 1 + 0.008 * Math.sin((frame / fps) * ((2 * Math.PI) / 3.4) + who.length);
  const bob = env * 10 * (height / 900);
  const tilt = env * 1.6 * Math.sin((frame / fps) * 5.3);
  const box: React.CSSProperties = {
    position: "absolute",
    width: w,
    height,
    left: W * x - w / 2,
    top: ground - height * 0.97 + bob,
    scale: `${flip ? -breathe : breathe} ${breathe}`,
    rotate: `${tilt}deg`,
    transformOrigin: "50% 90%",
  };
  if (!rig) {
    // No rig yet (tools/rig_character.sh): a labelled stand-in so the edit can be checked.
    return (
      <div style={{ ...box, borderRadius: "45% 45% 12% 12%", background: member.color, border: "8px solid #222", display: "flex", alignItems: "center", justifyContent: "center", fontSize: height / 8, fontWeight: 700, color: "#222" }}>
        {member.name}
      </div>
    );
  }
  const m = rig.mouth;
  const cx = ((m.x + m.w / 2) / rig.width) * 100;
  const cy = ((m.y + m.h / 2) / rig.height) * 100;
  const mask = `radial-gradient(ellipse ${(m.w / rig.width) * 75}% ${(m.h / rig.height) * 85}% at ${cx}% ${cy}%, #000 55%, transparent 100%)`;
  const img = { position: "absolute" as const, inset: 0, width: "100%", height: "100%" };
  const dir = `${seriesId}/cast/${who}/bust`;
  return (
    <div style={box}>
      <Img src={staticFile(`${dir}/${usable ?? "base"}.png`)} style={img} />
      {shape ? <Img src={staticFile(`${dir}/mouth-${shape}.png`)} style={{ ...img, maskImage: mask, WebkitMaskImage: mask }} /> : null}
    </div>
  );
};

export const PoseSprite: React.FC<{
  src: string;
  /** Feet position: x 0–1 across the frame, `ground` in px. */
  x: number;
  ground: number;
  height: number;
  flip?: boolean;
  /** Voice loudness 0–1 now: squash and tilt with it, so a body without a mouth rig still "talks". */
  talk?: number;
}> = ({ src, x, ground, height, flip, talk = 0 }) => {
  const frame = useCurrentFrame();
  const { fps, width: W } = useVideoConfig();
  const breathe = 1 + 0.012 * Math.sin((frame / fps) * ((2 * Math.PI) / 3));
  const squash = 1 + talk * 0.045;
  const tilt = talk * 3 * Math.sin((frame / fps) * 6);
  return (
    <Img
      src={staticFile(src)}
      style={{
        position: "absolute",
        height,
        left: W * x,
        top: ground - height,
        translate: "-50% 0",
        scale: `${(flip ? -1 : 1) / squash ** 0.5} ${breathe * squash}`,
        rotate: `${tilt}deg`,
        transformOrigin: "50% 100%",
      }}
    />
  );
};
