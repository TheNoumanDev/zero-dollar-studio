import React from "react";
import { interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { FONTS } from "../../config/theme";
import { useScale } from "../../lib/animation";
import type { Plan } from "./types";

const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const FADE = 0.2;

/**
 * Optional text watermark (your handle), top-left below the platform's top UI.
 * It steps aside (fades) while the hook card or a top graphic (stat, callout, quote, emoji) is on screen.
 */
export const Watermark: React.FC<{ text: string; plan: Plan; until: number }> = ({ text, plan, until }) => {
  const frame = useCurrentFrame();
  const { fps, height } = useVideoConfig();
  const u = useScale();
  const t = frame / fps;
  if (!text || t > until) return null;

  const busy: [number, number][] = [
    [0, 2.7], // hook card
    ...plan.graphics.filter((g) => g.type !== "kinetic").map((g) => [g.t, g.t + g.dur] as [number, number]),
  ];
  // Visibility: 0 inside a busy window, ramping back over FADE seconds either side.
  const visible = Math.min(
    1,
    ...busy.map(([a, b]) => 1 - Math.min(interpolate(t, [a - FADE, a], [0, 1], clamp), interpolate(t, [b, b + FADE], [1, 0], clamp))),
  );
  if (visible <= 0) return null;

  return (
    <div
      style={{
        position: "absolute",
        top: height * 0.115,
        left: 36 * u,
        background: "rgba(11,13,23,0.5)",
        borderRadius: 999,
        padding: `${12 * u}px ${36 * u}px`,
        fontFamily: FONTS.caption,
        fontWeight: 800,
        fontSize: 60 * u,
        color: "#fff",
        opacity: 0.9 * visible,
      }}
    >
      {text}
    </div>
  );
};
