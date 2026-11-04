import React from "react";
import { Easing, interpolate, random, useCurrentFrame, useVideoConfig } from "remotion";

// Code-drawn effects, no image or video assets: the same seed always draws the same frame.
//   <Particles kind="burst" x={540} y={960} start={1.2} />   sparks, confetti, smoke or a magic ring
//   <DrawOn kind="circle" x={140} y={1200} w={800} h={220} start={2} />   a mark drawn on like a pen stroke

export type ParticleKind = "burst" | "confetti" | "smoke" | "ring";
export type DrawKind = "underline" | "circle" | "arrow" | "check";

const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const PALETTE = ["#FFE600", "#FF5CDB", "#3DFFB0", "#5CC8FF", "#FF8A3D"];

/** How long each kind stays on screen, in seconds. */
export const PARTICLE_SECONDS: Record<ParticleKind, number> = { burst: 0.8, confetti: 1.8, smoke: 1.6, ring: 0.9 };

export const Particles: React.FC<{
  kind: ParticleKind;
  /** Centre in px. */
  x: number;
  y: number;
  /** Start time in seconds (composition time). */
  start: number;
  color?: string;
  /** 1 = sized for a 1080-wide frame. */
  scale?: number;
  seed?: string;
}> = ({ kind, x, y, start, color, scale = 1, seed = "fx" }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const life = PARTICLE_SECONDS[kind];
  const p = (frame / fps - start) / life;
  if (p < 0 || p > 1) return null;
  const r = (i: number, k: string) => random(`${seed}-${kind}-${start}-${i}-${k}`);
  const s = scale;

  if (kind === "ring") {
    // A shockwave: two glowing rings and a flash, like a spell going off.
    const grow = Easing.out(Easing.cubic)(p);
    const c = color ?? "#B98CFF";
    return (
      <div style={{ position: "absolute", inset: 0, pointerEvents: "none" }}>
        {[0, 0.18].map((lag, i) => {
          const q = Math.max(0, Math.min(1, (p - lag) / (1 - lag)));
          const rad = (60 + Easing.out(Easing.cubic)(q) * 420) * s;
          return (
            <div
              key={i}
              style={{
                position: "absolute",
                left: x - rad,
                top: y - rad,
                width: rad * 2,
                height: rad * 2,
                borderRadius: "50%",
                border: `${(14 - i * 6) * s * (1 - q)}px solid ${c}`,
                boxShadow: `0 0 ${40 * s}px ${c}, inset 0 0 ${30 * s}px ${c}`,
                opacity: (1 - q) * 0.9,
              }}
            />
          );
        })}
        <div
          style={{
            position: "absolute",
            left: x - 160 * s,
            top: y - 160 * s,
            width: 320 * s,
            height: 320 * s,
            borderRadius: "50%",
            background: `radial-gradient(circle, #fff 0%, ${c} 35%, transparent 70%)`,
            opacity: interpolate(grow, [0, 0.15, 0.5], [0, 0.8, 0], clamp),
          }}
        />
      </div>
    );
  }

  const n = kind === "confetti" ? 46 : kind === "smoke" ? 14 : 28;
  return (
    <div style={{ position: "absolute", inset: 0, pointerEvents: "none" }}>
      {Array.from({ length: n }, (_, i) => {
        const ang = r(i, "a") * Math.PI * 2;
        if (kind === "burst") {
          // Sparks fly out fast, slow down, fall a little and fade: streaks pointing where they travel.
          const speed = (380 + r(i, "v") * 520) * s;
          const d = Easing.out(Easing.cubic)(p) * speed;
          const px = x + Math.cos(ang) * d;
          const py = y + Math.sin(ang) * d + p * p * 160 * s;
          const len = (40 + r(i, "l") * 50) * s * (1 - p);
          const c = color ?? (r(i, "c") < 0.6 ? "#FFE27A" : "#FF9B3D");
          return (
            <div
              key={i}
              style={{
                position: "absolute",
                left: px - len / 2,
                top: py - 3 * s,
                width: len,
                height: 6 * s,
                borderRadius: 6 * s,
                background: `linear-gradient(90deg, transparent, ${c})`,
                boxShadow: `0 0 ${12 * s}px ${c}`,
                rotate: `${ang}rad`,
                opacity: 1 - p,
              }}
            />
          );
        }
        if (kind === "confetti") {
          // Pieces shoot up and out, then flutter down spinning.
          const vx = (Math.cos(ang) * 0.6) * (300 + r(i, "v") * 500) * s;
          const vy = -(500 + r(i, "u") * 700) * s;
          const tt = p * PARTICLE_SECONDS.confetti;
          const px = x + vx * tt + Math.sin(tt * 6 + i) * 30 * s;
          const py = y + vy * tt + 0.5 * 1400 * s * tt * tt;
          const c = PALETTE[i % PALETTE.length];
          const spin = tt * (360 + r(i, "s") * 720);
          return (
            <div
              key={i}
              style={{
                position: "absolute",
                left: px,
                top: py,
                width: 22 * s,
                height: 12 * s,
                background: color && i % 2 ? color : c,
                borderRadius: r(i, "k") < 0.3 ? "50%" : 2 * s,
                rotate: `${spin}deg`,
                scale: `1 ${Math.cos((spin * Math.PI) / 180) || 0.1}`,
                opacity: interpolate(p, [0, 0.05, 0.8, 1], [0, 1, 1, 0], clamp),
              }}
            />
          );
        }
        // smoke: soft puffs that drift up, swell and thin out.
        const drift = (Math.cos(ang) * 280 + (r(i, "w") - 0.5) * 120) * s;
        const rise = -(120 + r(i, "u") * 220) * s;
        const e = Easing.out(Easing.quad)(p);
        const size = (90 + r(i, "z") * 110) * s * (0.6 + e * 1.4);
        const shade = Math.round(110 + r(i, "g") * 80);
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: x + drift * e - size / 2,
              top: y + rise * e - size / 2,
              width: size,
              height: size,
              borderRadius: "50%",
              background: `radial-gradient(circle, ${color ?? `rgb(${shade},${shade},${shade})`} 0%, transparent 70%)`,
              filter: `blur(${8 * s}px)`,
              opacity: interpolate(p, [0, 0.12, 1], [0, 0.55, 0], clamp) * (0.5 + r(i, "o") * 0.5),
            }}
          />
        );
      })}
    </div>
  );
};

// Hand-drawn paths in a 0-100 box: a slightly wobbly marker stroke rather than geometry.
const PATHS: Record<DrawKind, string> = {
  underline: "M2 70 C 25 62, 55 74, 98 64",
  circle: "M58 6 C 20 2, 0 30, 6 58 C 12 86, 60 98, 86 82 C 104 70, 100 22, 66 8 C 58 5, 44 8, 40 12",
  arrow: "M4 90 C 30 70, 55 45, 88 14 M62 12 L 90 12 L 88 40",
  check: "M8 54 L 36 84 L 94 10",
};

export const DrawOn: React.FC<{
  kind: DrawKind;
  /** Box the mark fills, in px. */
  x: number;
  y: number;
  w: number;
  h: number;
  start: number;
  /** Seconds to hold after the stroke is drawn. */
  hold?: number;
  color?: string;
  stroke?: number;
}> = ({ kind, x, y, w, h, start, hold = 0.9, color = "#FF3B5C", stroke = 12 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps - start;
  const draw = 0.35;
  if (t < 0 || t > draw + hold + 0.25) return null;
  const p = interpolate(t, [0, draw], [0, 1], { ...clamp, easing: Easing.inOut(Easing.cubic) });
  const fade = interpolate(t, [draw + hold, draw + hold + 0.25], [1, 0], clamp);
  // Scale the 0-100 path to the box in px so the stroke keeps its width and the dash reveal stays exact.
  let n = 0;
  const d = PATHS[kind].replace(/-?\d+(\.\d+)?/g, (v) => String((Number(v) / 100) * (n++ % 2 ? h : w)));
  return (
    <svg
      viewBox={`0 0 ${w} ${h}`}
      style={{ position: "absolute", left: x, top: y, width: w, height: h, overflow: "visible", opacity: fade, pointerEvents: "none" }}
    >
      <path
        d={d}
        fill="none"
        stroke={color}
        strokeWidth={stroke}
        strokeLinecap="round"
        strokeLinejoin="round"
        pathLength={1}
        strokeDasharray={1}
        strokeDashoffset={1 - p}
        style={{ filter: `drop-shadow(0 4px 10px rgba(0,0,0,0.5))` }}
      />
    </svg>
  );
};
