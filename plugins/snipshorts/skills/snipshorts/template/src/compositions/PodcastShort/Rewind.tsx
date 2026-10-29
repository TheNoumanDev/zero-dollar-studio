import React from "react";
import { AbsoluteFill, Easing, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { FONTS } from "../../config/theme";
import { useScale } from "../../lib/animation";

const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

/** Video filter for the rewind: desaturate + blur + jitter around the cut out of the cold open. */
export const rewindVideoStyle = (t: number, at: number | null | undefined): React.CSSProperties => {
  if (at == null) return {};
  const k = interpolate(t, [at - 0.35, at, at + 0.15, at + 0.45], [0, 1, 1, 0], clamp);
  if (k === 0) return {};
  return {
    filter: `saturate(${1 - 0.8 * k}) blur(${4 * k}px) contrast(${1 + 0.3 * k})`,
    translate: `${Math.sin(t * 120) * 14 * k}px ${Math.cos(t * 97) * 6 * k}px`,
  };
};

/** Tape-rewind overlay after the cold open: scanlines, ⏪ and the label ("HOW IT STARTED"). */
export const Rewind: React.FC<{ at: number; label: string }> = ({ at, label }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const u = useScale();
  const t = frame / fps;
  if (t < at - 0.4 || t > at + 1.6) return null;
  const k = interpolate(t, [at - 0.35, at, at + 0.15, at + 0.45], [0, 1, 1, 0], clamp);
  const labelIn = interpolate(t, [at - 0.1, at + 0.15], [0, 1], { ...clamp, easing: Easing.out(Easing.back(2)) });
  const labelOut = interpolate(t, [at + 1.2, at + 1.6], [0, 1], { ...clamp, easing: Easing.in(Easing.cubic) });
  const roll = (t * 2400) % 60;
  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      <AbsoluteFill
        style={{
          opacity: k * 0.55,
          backgroundImage: `repeating-linear-gradient(0deg, rgba(255,255,255,0.18) 0px, rgba(255,255,255,0.18) ${3 * u}px, transparent ${3 * u}px, transparent ${12 * u}px)`,
          backgroundPosition: `0 ${roll * u}px`,
        }}
      />
      <AbsoluteFill style={{ background: "#fff", opacity: interpolate(t, [at - 0.05, at, at + 0.12], [0, 0.7, 0], clamp) }} />
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", opacity: 1 - labelOut }}>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 30 * u,
            background: "rgba(11,13,23,0.85)",
            border: `${6 * u}px solid #FFE600`,
            borderRadius: 28 * u,
            padding: `${24 * u}px ${54 * u}px`,
            scale: labelIn,
            rotate: "-3deg",
          }}
        >
          <span style={{ fontSize: 160 * u, color: "#FFE600", lineHeight: 1 }}>⏪</span>
          <span style={{ fontFamily: FONTS.caption, fontWeight: 900, fontSize: 135 * u, color: "#fff", textTransform: "uppercase" }}>{label}</span>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
