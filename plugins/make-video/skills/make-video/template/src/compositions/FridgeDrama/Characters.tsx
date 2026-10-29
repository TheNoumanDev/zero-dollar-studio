import React from "react";
import { interpolate } from "remotion";

type FaceProps = {
  /** 0..1 mouth openness, driven by voice loudness. */
  mouth: number;
  /** -1..1 horizontal gaze, toward whoever is talking. */
  look: number;
  /** 0..1 eyelid closure (blink). */
  blink: number;
  /** 0..1 shock: wider eyes, round mouth. */
  shock: number;
  y: number;
  spread?: number;
};

/** Shared cartoon face, drawn in a 200-unit wide coordinate space. */
const Face: React.FC<FaceProps> = ({ mouth, look, blink, shock, y, spread = 34 }) => {
  const eyeR = 17 + shock * 6;
  const lid = Math.max(blink, 0) * eyeR * 2;
  return (
    <g transform={`translate(100 ${y})`}>
      {[-spread, spread].map((x) => (
        <g key={x} transform={`translate(${x} 0)`}>
          <ellipse rx={eyeR} ry={eyeR * 1.1} fill="#fff" stroke="#1d1d1f" strokeWidth={3} />
          <circle cx={look * 7} cy={2} r={8 - shock * 2} fill="#1d1d1f" />
          <circle cx={look * 7 + 3} cy={-2} r={2.5} fill="#fff" />
          {lid > 0 ? (
            <rect x={-eyeR - 2} y={-eyeR * 1.1 - 2} width={eyeR * 2 + 4} height={lid} fill="currentColor" />
          ) : null}
        </g>
      ))}
      {/* Mouth: a closed smile that opens with the voice. */}
      {mouth < 0.08 && shock < 0.3 ? (
        <path d="M -16 34 Q 0 46 16 34" stroke="#1d1d1f" strokeWidth={5} fill="none" strokeLinecap="round" />
      ) : (
        <ellipse
          cx={0}
          cy={38}
          rx={14 + mouth * 6 - shock * 2}
          ry={4 + Math.max(mouth, shock * 0.9) * 18}
          fill="#5a1414"
          stroke="#1d1d1f"
          strokeWidth={3}
        />
      )}
    </g>
  );
};

type CharProps = Omit<FaceProps, "y" | "spread"> & { size: number };

export const Tomato: React.FC<CharProps> = ({ size, ...face }) => (
  <svg width={size} height={size} viewBox="0 0 200 200" style={{ overflow: "visible", color: "#E53935" }}>
    <ellipse cx={100} cy={115} rx={88} ry={78} fill="#E53935" stroke="#1d1d1f" strokeWidth={4} />
    <ellipse cx={62} cy={82} rx={18} ry={10} fill="#ffffff55" transform="rotate(-30 62 82)" />
    <path
      d="M100 40 L84 22 L96 36 L74 34 L94 44 L82 56 L100 46 L118 56 L106 44 L126 34 L104 36 L116 22 Z"
      fill="#43A047"
      stroke="#1d1d1f"
      strokeWidth={3}
      strokeLinejoin="round"
    />
    <rect x={96} y={18} width={8} height={20} rx={4} fill="#2E7D32" stroke="#1d1d1f" strokeWidth={3} />
    <Face {...face} y={110} />
  </svg>
);

export const Broccoli: React.FC<CharProps> = ({ size, ...face }) => (
  <svg width={size} height={size} viewBox="0 0 200 200" style={{ overflow: "visible", color: "#388E3C" }}>
    <path d="M70 120 L62 196 L138 196 L130 120 Z" fill="#9CCC65" stroke="#1d1d1f" strokeWidth={4} strokeLinejoin="round" />
    {[
      [100, 40, 42], [52, 70, 36], [148, 70, 36], [70, 105, 38], [130, 105, 38], [100, 82, 44],
    ].map(([cx, cy, r], i) => (
      <circle key={i} cx={cx} cy={cy} r={r} fill={i % 2 ? "#388E3C" : "#43A047"} stroke="#1d1d1f" strokeWidth={4} />
    ))}
    <Face {...face} y={88} spread={30} />
  </svg>
);

export const Carrot: React.FC<CharProps> = ({ size, ...face }) => (
  <svg width={size} height={size * 1.3} viewBox="0 0 200 260" style={{ overflow: "visible", color: "#FB8C00" }}>
    {[-28, 0, 28].map((r) => (
      <path key={r} d="M100 60 C 90 30, 95 10, 100 0 C 105 10, 110 30, 100 60 Z" fill="#43A047" stroke="#1d1d1f" strokeWidth={3} transform={`rotate(${r} 100 60)`} />
    ))}
    <path d="M40 70 Q 100 50 160 70 Q 130 200 104 255 Q 100 262 96 255 Q 70 200 40 70 Z" fill="#FB8C00" stroke="#1d1d1f" strokeWidth={4} strokeLinejoin="round" />
    {[130, 170, 205].map((y, i) => (
      <path key={y} d={`M${i % 2 ? 112 : 70} ${y} l 18 -4`} stroke="#E65100" strokeWidth={4} strokeLinecap="round" />
    ))}
    <Face {...face} y={100} spread={28} />
  </svg>
);

/** Natural blink: a short close every few seconds, offset per character. */
export const blinkAt = (frame: number, fps: number, offset: number) => {
  const period = Math.round(3.2 * fps);
  const local = (frame + offset) % period;
  return interpolate(local, [0, 2, 4, 6], [0, 1, 1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
};
