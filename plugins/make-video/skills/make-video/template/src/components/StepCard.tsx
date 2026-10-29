import React from "react";
import { Easing, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { FONTS } from "../config/theme";
import { useScale } from "../lib/animation";

const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

/** One step of a tutorial: shown from `at` (s) until the next step starts. */
export type Step = { at: number; title: string };

/**
 * "STEP 2/4" pill + a segmented progress bar + the step's title, pinned to the top of the frame.
 * Viewers see how far along they are (and that the end is close), which keeps them watching tutorials.
 * The current segment fills over the step's duration; the pill pops and the title slides on each change.
 */
export const StepCard: React.FC<{
  steps: Step[];
  /** Hide after this time (s); default: never. */
  until?: number;
  accent?: string;
  /** Distance from the top in design px (1080×1920 keeps it under the platform UI at 220). */
  top?: number;
}> = ({ steps, until = Infinity, accent = "#FF7A45", top = 240 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const u = useScale();
  const t = frame / fps;
  let i = -1;
  steps.forEach((s, k) => {
    if (t >= s.at) i = k;
  });
  if (i < 0 || t > until) return null;
  const step = steps[i]!;
  const end = steps[i + 1]?.at ?? (Number.isFinite(until) ? until : step.at + 5);
  const since = t - step.at;
  const enter = interpolate(since, [0, 0.35], [0, 1], { ...clamp, easing: Easing.out(Easing.back(1.8)) });
  const slide = interpolate(since, [0.05, 0.45], [1, 0], { ...clamp, easing: Easing.out(Easing.cubic) });
  const exit = Number.isFinite(until) ? interpolate(t, [until - 0.3, until], [1, 0], clamp) : 1;
  const fill = interpolate(t, [step.at, end], [0, 1], clamp);

  return (
    <div style={{ position: "absolute", left: 60 * u, right: 60 * u, top: top * u, opacity: exit }}>
      <div style={{ display: "flex", alignItems: "center", gap: 24 * u }}>
        <div
          style={{
            background: accent,
            color: "#141414",
            fontFamily: FONTS.caption,
            fontWeight: 900,
            fontSize: 50 * u,
            letterSpacing: 2 * u,
            padding: `${8 * u}px ${28 * u}px`,
            borderRadius: 999,
            scale: 0.6 + 0.4 * enter,
            whiteSpace: "nowrap",
            boxShadow: `0 ${6 * u}px ${18 * u}px rgba(0,0,0,0.35)`,
          }}
        >
          STEP {i + 1}/{steps.length}
        </div>
        <div style={{ flex: 1, display: "flex", gap: 12 * u }}>
          {steps.map((_, k) => (
            <div key={k} style={{ flex: 1, height: 18 * u, borderRadius: 999, background: "rgba(255,255,255,0.18)", overflow: "hidden" }}>
              <div style={{ width: `${(k < i ? 1 : k === i ? fill : 0) * 100}%`, height: "100%", background: accent, borderRadius: 999 }} />
            </div>
          ))}
        </div>
      </div>
      <div
        style={{
          marginTop: 20 * u,
          fontFamily: FONTS.display,
          fontWeight: 700,
          fontSize: 104 * u,
          lineHeight: 1.05,
          color: "#fff",
          textShadow: `0 ${4 * u}px ${20 * u}px rgba(0,0,0,0.55)`,
          opacity: 1 - slide,
          translate: `${slide * 80 * u}px 0`,
        }}
      >
        {step.title}
      </div>
    </div>
  );
};
