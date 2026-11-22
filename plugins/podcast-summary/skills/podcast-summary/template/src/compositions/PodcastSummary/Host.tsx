import React from "react";
import { AbsoluteFill, Easing, Img, interpolate, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { FONTS } from "../../config/theme";
import { useScale } from "../../lib/animation";

// Your reaction cam: a round face in the corner that changes with each scene's `react`, plus a speech bubble for
// each `comment`. Faces are YOUR OWN images, one per reaction: public/<dir>/<reaction>.png (e.g. host/smile.png,
// host/laugh.png). Without a host in script.json only the bubbles show. 16:9: always on, bottom right.
// 9:16: pops in for a comment and leaves after it.

const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

export type HostConfig = {
  /** Folder in public/ with one image per reaction. */
  dir: string;
  /** The reactions you have images for; the first is the resting face. */
  faces: string[];
  /** Optional blink image name, shown for a moment every ~3 s on the resting face. */
  blink?: string;
};

export type HostCue = { at: number; until: number; react?: string; comment?: string };

export const Host: React.FC<{ cues: HostCue[]; until: number; host?: HostConfig | null }> = ({ cues, until, host }) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const wide = width > height;
  const u = useScale() * (wide ? 0.66 : 1);
  const t = frame / fps;
  if (t > until) return null;
  const cue = cues.find((c) => t >= c.at && t < c.until);
  const since = cue ? t - cue.at : 99;
  const enter = interpolate(t, [0.3, 0.8], [0, 1], { ...clamp, easing: Easing.out(Easing.back(1.6)) });
  const exit = interpolate(t, [until - 0.35, until], [0, 1], { ...clamp, easing: Easing.in(Easing.cubic) });
  const pop = 1 + 0.08 * Math.max(0, 1 - since / 0.25) * Math.sin(Math.min(1, since / 0.25) * Math.PI);

  const bubbleIn = cue?.comment ? interpolate(since, [0.25, 0.5], [0, 1], { ...clamp, easing: Easing.out(Easing.back(2)) }) : 0;
  // A comment stays up ~3.5 s at most, so long scenes get a clean picture between remarks.
  const bubbleEnd = cue ? Math.min(cue.until, cue.at + 3.8) : 0;
  const bubbleOut = cue?.comment ? interpolate(t, [bubbleEnd - 0.35, bubbleEnd - 0.15], [0, 1], clamp) : 0;
  const vis = wide
    ? 1
    : cue?.comment
      ? interpolate(since, [0, 0.3], [0, 1], { ...clamp, easing: Easing.out(Easing.back(1.8)) }) *
        (1 - interpolate(t, [bubbleEnd - 0.1, bubbleEnd + 0.2], [0, 1], { ...clamp, easing: Easing.in(Easing.cubic) }))
      : 0;
  if (vis <= 0.001 && !(cue?.comment && !host)) return null;

  const size = host ? 520 * u : 0;
  const bottom = 250 * u;
  const camLeft = wide ? width - size - 60 * u : 50 * u;
  let face = host ? (cue?.react && host.faces.includes(cue.react) ? cue.react : host.faces[0]) : "";
  if (host?.blink && face === host.faces[0] && t % 3.3 < 0.12) face = host.blink;
  const bob = Math.sin(t * 2.2) * 6 * u;

  return (
    <AbsoluteFill style={{ pointerEvents: "none", opacity: 1 - exit }}>
      {host ? (
        <div style={{ position: "absolute", left: camLeft, bottom, scale: (wide ? enter : vis) * pop, translate: `0 ${bob}px`, transformOrigin: wide ? "right bottom" : "left bottom" }}>
          <div style={{ width: size, height: size, borderRadius: "50%", overflow: "hidden", background: "radial-gradient(circle at 50% 35%, #FFE600, #FF9F1C)", border: `${10 * u}px solid #fff`, boxShadow: `0 ${14 * u}px ${30 * u}px rgba(0,0,0,0.55)` }}>
            <Img src={staticFile(`${host.dir}/${face}.png`)} style={{ width: "100%", height: "100%", objectFit: "cover", objectPosition: "50% 15%" }} />
          </div>
        </div>
      ) : null}
      {cue?.comment && since >= 0.25 && bubbleOut < 1 ? (
        <div
          style={{
            position: "absolute",
            ...(wide
              ? { right: 60 * u, bottom: bottom + size + 50 * u, maxWidth: 760 * u, borderRadius: `${34 * u}px ${34 * u}px ${6 * u}px ${34 * u}px` }
              : { left: 50 * u + size * 0.82, bottom: bottom + size * 0.55, maxWidth: width * 0.62, borderRadius: `${34 * u}px ${34 * u}px ${34 * u}px ${6 * u}px` }),
            background: "#fff",
            color: "#0B0D17",
            border: `${6 * u}px solid #0B0D17`,
            padding: `${18 * u}px ${30 * u}px`,
            fontFamily: FONTS.caption,
            fontWeight: 800,
            fontSize: 76 * u,
            lineHeight: 1.12,
            scale: bubbleIn * (1 - bubbleOut),
            transformOrigin: wide ? "right bottom" : "left bottom",
            boxShadow: `0 ${10 * u}px ${24 * u}px rgba(0,0,0,0.35)`,
          }}
        >
          {cue.comment}
        </div>
      ) : null}
    </AbsoluteFill>
  );
};
