import React from "react";

// Shared pieces for code-drawn mascots, in a 400 × 560 box (head at the top, shoulders to the bottom edge).
// MascotKit builds a mascot from a `look` in script.json; add hand-drawn ones to MASCOTS (keyed by cast id).
// Only lines a person really said are ever played over their mascot, in their own unaltered voice.

export type Pose = {
  /** 0 closed … 1 wide, from the audio loudness of this frame (0 when the other person talks). */
  mouth: number;
  blink: boolean;
  /** Seconds, for idle motion. */
  t: number;
};

export const Eyes: React.FC<{ y: number; iris: string; skin: string; blink: boolean; squint?: boolean }> = ({ y, iris, skin, blink, squint }) => (
  <>
    {[-1, 1].map((s) => {
      const x = 200 + s * 42;
      if (blink) return <path key={s} d={`M${x - 18},${y + 2} Q${x},${y + 10} ${x + 18},${y + 2}`} fill="none" stroke="#2a1a14" strokeWidth={6} strokeLinecap="round" />;
      return (
        <g key={s}>
          <ellipse cx={x} cy={y} rx={19} ry={squint ? 15 : 21} fill="#fff" />
          <circle cx={x + 2} cy={y + 2} r={11} fill={iris} />
          <circle cx={x + 2} cy={y + 2} r={6} fill="#120c0a" />
          <circle cx={x + 6} cy={y - 3} r={3.5} fill="#fff" />
          {squint ? <path d={`M${x - 21},${y - 8} Q${x},${y - 20} ${x + 21},${y - 8} L${x + 21},${y - 24} L${x - 21},${y - 24} Z`} fill={skin} /> : null}
        </g>
      );
    })}
  </>
);

/** Closed: a smile. Open: a dark oval that grows with the voice, teeth on top. */

export const Mouth: React.FC<{ y: number; open: number; lip: string; teeth?: boolean }> = ({ y, open, lip, teeth }) => {
  if (open < 0.08) return <path d={`M170,${y} Q200,${y + 24} 230,${y} Q200,${y + 12} 170,${y} Z`} fill={lip} stroke={lip} strokeWidth={6} strokeLinejoin="round" />;
  const h = 6 + 24 * open;
  const w = 24 - 4 * open;
  return (
    <g>
      <ellipse cx={200} cy={y + 6 + h / 2} rx={w} ry={h / 2 + 2} fill={lip} />
      <ellipse cx={200} cy={y + 8 + h * 0.75} rx={w * 0.6} ry={h * 0.22} fill="#d9646b" />
      {teeth ? <rect x={200 - w * 0.75} y={y + 6} width={w * 1.5} height={Math.min(7, h * 0.3)} rx={3} fill="#fff" /> : null}
    </g>
  );
};

export const Mic: React.FC<{ x: number; y: number; flip?: boolean }> = ({ x, y, flip }) => (
  <g transform={`translate(${x},${y}) scale(${flip ? -1 : 1},1) rotate(-18)`}>
    <rect x={-120} y={40} width={150} height={14} rx={7} fill="#2b2f3a" />
    <rect x={-34} y={-70} width={68} height={150} rx={34} fill="#1d2029" stroke="#3a3f4d" strokeWidth={5} />
    {[-40, -20, 0, 20].map((d) => <line key={d} x1={-28} y1={d} x2={28} y2={d} stroke="#2f3442" strokeWidth={5} />)}
  </g>
);



export const HairBack: React.FC<{ fill: string; to: number; width?: number }> = ({ fill, to, width = 128 }) => (
  <path d={`M${200 - width},200 C${200 - width - 14},110 ${200 - 70},40 200,40 C${200 + 70},40 ${200 + width + 14},110 ${200 + width},200 C${200 + width + 10},${to - 80} ${200 + width - 6},${to} ${200 + width - 40},${to} L${200 - width + 40},${to} C${200 - width + 6},${to} ${200 - width - 10},${to - 80} ${200 - width},200 Z`} fill={fill} />
);

export const Face: React.FC<{ skin: string; shade: string; narrow?: number }> = ({ skin, shade, narrow = 0 }) => (
  <>
    <ellipse cx={96 + narrow} cy={208} rx={18} ry={27} fill={shade} />
    <ellipse cx={304 - narrow} cy={208} rx={18} ry={27} fill={shade} />
    <path d={`M${96 + narrow},190 C${94 + narrow},108 140,72 200,72 C260,72 ${306 - narrow},108 ${304 - narrow},190 C${306 - narrow},262 262,314 200,316 C138,314 ${94 + narrow},262 ${96 + narrow},190 Z`} fill={skin} />
  </>
);

export const Nose: React.FC<{ shade: string }> = ({ shade }) => <path d="M198,214 q-9,26 4,31" fill="none" stroke={shade} strokeWidth={6} strokeLinecap="round" />;

/** Hand-drawn mascots by cast id (`React.FC<{ pose: Pose }>` in the 400 × 560 box). They win over a `look`, not over a photo. */
export const MASCOTS: Record<string, React.FC<{ pose: Pose }>> = {};
