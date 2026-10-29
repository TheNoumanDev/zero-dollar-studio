import React from "react";
import { Audio } from "@remotion/media";
import { AbsoluteFill, CalculateMetadataFunction, Img, interpolate, Sequence, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { FONTS } from "../../config/theme";
import { mix, springIn } from "../../lib/animation";
import { captionPages, Captions } from "./Captions";
import { BustRig, PoseSprite, talkLevel } from "./rig";
import { buildShots, Shot } from "./shots";
import type { EpisodeData, EpisodeLine, SetDef, Transition, Word } from "./types";

/**
 * A cartoon episode, built entirely from data: series/<series>/series.json (the bible),
 * stories/<slug>/script.json (lines + optional shot direction), and what the pipeline
 * writes into public/<slug>/ (episode.json, captions.json, voice/music/sfx WAVs).
 * Register one <Composition> per episode with `defaultProps={{ slug }}` and
 * `calculateMetadata={calculateEpisodeMetadata}` (see the cartoonsmith skill).
 * For a one-off gag shot, copy this folder and add it in `buildShots`.
 */
export type EpisodeProps = {
  slug: string;
  /** Filled in by calculateEpisodeMetadata. */
  data?: EpisodeData | null;
  captions?: Word[];
};

export const calculateEpisodeMetadata: CalculateMetadataFunction<EpisodeProps> = async ({ props }) => {
  const res = await fetch(staticFile(`${props.slug}/episode.json`));
  if (!res.ok) throw new Error(`public/${props.slug}/episode.json is missing: run tools/make-episode.sh stories/${props.slug} <CompositionId>`);
  const data = (await res.json()) as EpisodeData;
  const cap = await fetch(staticFile(`${props.slug}/captions.json`));
  const captions = cap.ok ? ((await cap.json()) as Word[]) : [];
  return { durationInFrames: data.durationInFrames, fps: data.fps, width: data.width, height: data.height, props: { ...props, data, captions } };
};

const toFrame = (ms: number, fps: number) => Math.round((ms / 1000) * fps);

/** The set: a painted background if the bible has one, else a flat stand-in from its colours. */
const SetBg: React.FC<{ seriesId: string; set: SetDef; zoom: number; blur: number; focus: string }> = ({ seriesId, set, zoom, blur, focus }) => {
  const wall = set.wall ?? "#F3E3C3";
  const floor = set.floor ?? "#B98B5E";
  const accent = set.accent ?? "#8FC1D4";
  return (
    <AbsoluteFill style={{ overflow: "hidden" }}>
      <AbsoluteFill style={{ scale: zoom, transformOrigin: focus, filter: blur ? `blur(${blur}px)` : undefined }}>
        {set.image ? (
          <Img src={staticFile(`${seriesId}/${set.image}`)} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
        ) : (
          <AbsoluteFill>
            <AbsoluteFill style={{ background: `linear-gradient(${wall}, ${wall} 60%, ${floor} 60%)` }} />
            <div style={{ position: "absolute", left: "8%", top: "12%", width: "22%", height: "30%", background: accent, border: "1.2vh solid #6B4A2B", borderRadius: 8 }} />
            {[0.18, 0.31, 0.44].map((y) => (
              <div key={y} style={{ position: "absolute", left: "60%", width: "32%", top: `${y * 100}%`, height: "1.6vh", background: "#6B4A2B" }} />
            ))}
            <div style={{ position: "absolute", left: 0, right: 0, top: "60%", height: "1.2vh", background: "rgba(0,0,0,0.18)" }} />
          </AbsoluteFill>
        )}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

/** How a shot comes in: cut, crossfade, wipe or iris. */
const TransIn: React.FC<{ kind: Transition; children: React.ReactNode }> = ({ kind, children }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const n = Math.round(0.3 * fps);
  if (kind === "cut" || frame >= n) return <AbsoluteFill>{children}</AbsoluteFill>;
  const t = frame / n;
  const e = t * t * (3 - 2 * t);
  if (kind === "fade") return <AbsoluteFill style={{ opacity: e }}>{children}</AbsoluteFill>;
  const m =
    kind === "iris"
      ? `radial-gradient(circle at 50% 50%, #000 ${e * 120}%, transparent ${e * 120 + 8}%)`
      : `linear-gradient(90deg, #000 ${e * 120 - 20}%, transparent ${e * 120}%)`;
  return <AbsoluteFill style={{ maskImage: m, WebkitMaskImage: m }}>{children}</AbsoluteFill>;
};

/** Where the camera leans at `ms`: toward the last speaker in frame (−1 left … +1 right), eased over 0.5 s. */
const leanAt = (lines: EpisodeLine[], xs: Record<string, number>, ms: number) => {
  const said = lines.filter((l) => l.speaker in xs && l.startMs <= ms);
  if (!said.length) return 0;
  const side = (who: string) => (xs[who] - 0.5) * 2;
  const cur = said[said.length - 1];
  const prev = said.length > 1 ? side(said[said.length - 2].speaker) : 0;
  const k = Math.min(1, (ms - cur.startMs) / 500);
  return prev + (side(cur.speaker) - prev) * k * k * (3 - 2 * k);
};

const ShotView: React.FC<{ shot: Shot; data: EpisodeData }> = ({ shot, data }) => {
  const frame = useCurrentFrame();
  const { fps, width: W, height: H } = useVideoConfig();
  const { series, lines } = data;
  const portrait = H > W;
  const ground = portrait ? H * 0.8 : H;
  const offsetMs = shot.fromMs;
  const ms = offsetMs + (frame / fps) * 1000;
  const set = series.sets[shot.set] ?? { name: shot.set };
  const push = interpolate(frame, [0, 4 * fps], [1, 1.04], { extrapolateRight: "clamp" });
  const aspect = (who: string) => {
    const r = series.characters[who]?.rig;
    return r ? r.width / r.height : 0.9;
  };
  const byLoudness = data.language !== "en";
  const n = shot.members.length;
  const xs: Record<string, number> = {};
  shot.members.forEach((who, i) => {
    xs[who] = n === 1 ? 0.5 : n === 2 ? (i === 0 ? 0.29 : 0.71) : 0.1 + (0.8 * (i + 0.5)) / n;
  });

  const poseOf = shot.framing === "pose" && shot.pose && series.characters[shot.focus]?.poses.indexOf(shot.pose) !== -1;
  if (poseOf) {
    return (
      <AbsoluteFill style={{ scale: push, transformOrigin: "50% 80%" }}>
        <SetBg seriesId={series.id} set={set} zoom={1} blur={0} focus="50% 60%" />
        <PoseSprite
          src={`${series.id}/cast/${shot.focus}/poses/${shot.pose}.png`}
          x={0.5}
          ground={portrait ? ground : H * 0.97}
          height={(portrait ? 0.6 : 0.85) * ground * (series.characters[shot.focus]?.scale ?? 1)}
          talk={talkLevel(lines, shot.focus, ms, fps)}
        />
      </AbsoluteFill>
    );
  }

  const close = n === 1;
  const lean = close ? 0 : leanAt(lines, xs, ms);
  const fit = (who: string) => {
    const a = aspect(who);
    const h = close ? Math.min(0.88 * ground, (0.8 * W) / a) : n === 2 ? Math.min(0.72 * ground, (0.44 * W) / a) : Math.min(0.66 * ground, (0.92 * W) / n / a);
    return h * (series.characters[who]?.scale ?? 1);
  };
  return (
    <AbsoluteFill
      style={{
        scale: push * (1 + Math.abs(lean) * 0.03),
        translate: `${-lean * W * 0.02}px 0`,
        transformOrigin: `${50 + lean * 20}% 60%`,
      }}
    >
      <SetBg seriesId={series.id} set={set} zoom={close ? 1.5 : n === 2 ? 1.15 : 1.05} blur={close ? 3 : n === 2 ? 1.5 : 0} focus={`${30 + 40 * (xs[shot.focus] ?? 0.5)}% 55%`} />
      {shot.members.map((who) =>
        series.characters[who] ? (
          <BustRig
            key={who}
            who={who}
            member={series.characters[who]}
            seriesId={series.id}
            lines={lines}
            offsetMs={offsetMs}
            byLoudness={byLoudness}
            height={fit(who)}
            x={xs[who]}
            ground={ground}
          />
        ) : null,
      )}
    </AbsoluteFill>
  );
};

const Outro: React.FC<{ text: string; series: string }> = ({ text, series }) => {
  const frame = useCurrentFrame();
  const { fps, width } = useVideoConfig();
  const t = springIn(frame, fps, 0, 0.5);
  const u = Math.min(width, 1920) / 1920;
  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", background: `rgba(20,16,24,${0.8 * t})` }}>
      <div style={{ fontFamily: FONTS.display, fontWeight: 700, color: "#FFD84D", fontSize: 110 * u * (width < 1200 ? 1.6 : 1), textAlign: "center", lineHeight: 1.1, padding: "0 8%", scale: mix(t, 0.8, 1), opacity: t, WebkitTextStroke: `${10 * u}px #1d1d1f`, paintOrder: "stroke fill" }}>
        {text}
        <div style={{ fontSize: 56 * u * (width < 1200 ? 1.6 : 1), color: "#fff", marginTop: 24 * u }}>{series}</div>
      </div>
    </AbsoluteFill>
  );
};

export const Episode: React.FC<EpisodeProps> = ({ slug, data, captions }) => {
  const frame = useCurrentFrame();
  const { fps, width: W, height: H } = useVideoConfig();
  const shots = React.useMemo(() => (data ? buildShots(data) : []), [data]);
  const pages = React.useMemo(() => captionPages(captions ?? [], H > W ? 3 : 4), [captions, H, W]);
  if (!data) return <AbsoluteFill style={{ background: "#222", color: "#fff", fontSize: 40, padding: 60 }}>No episode data for {slug}.</AbsoluteFill>;
  const outroF = toFrame(data.outroStartMs, fps);
  const portrait = H > W;
  return (
    <AbsoluteFill style={{ background: "#000" }}>
      {shots.map((s, i) => {
        const from = toFrame(s.fromMs, fps);
        const next = shots[i + 1];
        // Each shot runs on under the next one while that one transitions in; the last one runs under the outro.
        const tail = next && next.transitionIn !== "cut" ? Math.round(0.3 * fps) : 0;
        const until = next ? toFrame(next.fromMs, fps) + tail : data.durationInFrames;
        return (
          <Sequence key={i} from={from} durationInFrames={Math.max(1, until - from)} premountFor={fps}>
            <TransIn kind={i === 0 ? "cut" : s.transitionIn}>
              <ShotView shot={s} data={data} />
            </TransIn>
          </Sequence>
        );
      })}
      {frame < outroF ? <Captions pages={pages} cast={data.series.characters} top={portrait ? H * 0.13 : H * 0.8} size={portrait ? W * 0.085 : H * 0.06} /> : null}
      <Sequence from={outroF}>
        <Outro text={data.outro.text ?? ""} series={data.series.title} />
      </Sequence>
      <Audio src={staticFile(`${slug}/voice.wav`)} />
      <Audio src={staticFile(`${slug}/music.wav`)} volume={0.9} />
      <Audio src={staticFile(`${slug}/sfx.wav`)} volume={0.8} />
    </AbsoluteFill>
  );
};
