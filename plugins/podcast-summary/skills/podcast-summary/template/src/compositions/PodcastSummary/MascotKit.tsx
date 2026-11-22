import React from "react";
import { Img, staticFile } from "remotion";
import { Eyes, Face, HairBack, MASCOTS, Mouth, Nose, Pose } from "./Mascots";

// Each person on the stage, described as data (script.json cast[who].look): a real photo (AI talking face or real
// mouth shapes), or a code-drawn mascot built from a few fields. Same 400 × 560 box as Mascots.tsx.

export type Look = {
  skin: string;
  hair: string;
  /** Hair shape. "cap" = a cap over short hair (capColor). */
  style: "short" | "curly" | "long" | "bald" | "spiky" | "side" | "bun" | "cap" | "wavy" | "buzz";
  beard?: "none" | "stubble" | "full" | "mustache" | "goatee";
  glasses?: "none" | "round" | "square" | "shades";
  top: string;
  topStyle?: "tee" | "shirt" | "hoodie" | "kurta" | "jacket";
  accent?: string;
  capColor?: string;
  /** beard colour when it differs from the hair (grey beard on dark hair) */
  beardColor?: string;
  female?: boolean;
  iris?: string;
  /** A real-photo cut-out instead of a drawn mascot (tools/summary/photomouths.py). The other fields are then unused. */
  photo?: Photo;
};

/** levels: real mouth shapes mouth0…N-1.png (tools/summary/photomouths.py), picked by loudness. Without levels or ai,
 *  a jaw-drop puppet (bust.png + jaw.png + mx/my/mw/jaw); it tends to look broken, so prefer the other two. */
/** ai: AI talking-face frames (tools/summary/aiface.py: JoyVASA + LivePortrait from their real voice), the most
 *  natural option. segs map each of their lines (composition time) to an offset in their voice track; outside their
 *  lines the still mouth0.png shows. */
export type AiFace = { dir: string; fps: number; n: number; segs: { start: number; end: number; off: number; dir?: string; n?: number }[] };
export type Photo = { src: string; w: number; h: number; levels?: number; mx?: number; my?: number; mw?: number; jaw?: number; ai?: AiFace };

// Real photo, jaw on its own layer dropping with the voice over a dark mouth (cut-out puppet style: it reads as
// animation, not footage). Fitted into the same 400 × 560 box as the drawn mascots, feet (shoulders) on the bottom.
const fromPhoto = (p: Photo, id: string): React.FC<{ pose: Pose }> => {
  const Body: React.FC<{ pose: Pose }> = ({ pose }) => {
    const k = Math.min(400 / p.w, 560 / p.h);
    if (p.ai) {
      const a = p.ai;
      const seg = a.segs.find((g) => g.start <= pose.t && pose.t < g.end);
      // A seg may point at frames from a later partial run (re-cut lines: aiface.py incr).
      const idx = seg ? Math.max(0, Math.min((seg.n ?? a.n) - 1, Math.round((pose.t - seg.start + seg.off) * a.fps))) : -1;
      const src = seg && idx >= 0 ? `${seg.dir ?? a.dir}/${String(idx).padStart(5, "0")}.webp` : `${p.src}/mouth0.png`;
      const bob = Math.sin(pose.t * 1.6) * 3;
      return (
        <g transform={`translate(${(400 - p.w * k) / 2},${560 - p.h * k + bob}) scale(${k})`}>
          <foreignObject width={p.w} height={p.h}>
            <Img src={staticFile(src)} style={{ width: p.w, height: p.h, display: "block" }} />
          </foreignObject>
        </g>
      );
    }
    if (p.levels) {
      // Real mouths: closed below a small threshold, then evenly up the loudness range.
      const m = Math.max(0, Math.min(1, pose.mouth));
      const lvl = m < 0.12 ? 0 : Math.min(p.levels - 1, 1 + Math.floor(((m - 0.12) / 0.88) * (p.levels - 1)));
      const bob = Math.sin(pose.t * 1.6) * 3;
      return (
        <g transform={`translate(${(400 - p.w * k) / 2},${560 - p.h * k + bob}) scale(${k})`}>
          <image href={staticFile(`${p.src}/mouth${lvl}.png`)} width={p.w} height={p.h} />
        </g>
      );
    }
    const { mx = 0, my = 0, mw = 0, jaw = 0 } = p;
    const open = Math.max(0, Math.min(1, pose.mouth)) * jaw;
    const bob = Math.sin(pose.t * 1.6) * 3;
    const clip = `mouth-${id}`;
    return (
      <g transform={`translate(${(400 - p.w * k) / 2},${560 - p.h * k + bob}) scale(${k})`}>
        <image href={staticFile(`${p.src}/bust.png`)} width={p.w} height={p.h} />
        {open > 0.5 ? (
          <>
            <clipPath id={clip}>
              <ellipse cx={mx} cy={my + open / 2} rx={mw * 0.46} ry={open / 2 + 1} />
            </clipPath>
            <g clipPath={`url(#${clip})`}>
              <rect x={mx - mw} y={my - 2} width={mw * 2} height={open + 6} fill="#1c0a0c" />
              {open > jaw * 0.45 ? <rect x={mx - mw * 0.3} y={my - 1} width={mw * 0.6} height={open * 0.18} rx={2} fill="#d9d0c4" opacity={0.85} /> : null}
              <ellipse cx={mx} cy={my + open * 0.95} rx={mw * 0.28} ry={open * 0.3} fill="#7a2f35" opacity={0.8} />
            </g>
          </>
        ) : null}
        <image href={staticFile(`${p.src}/jaw.png`)} width={p.w} height={p.h} y={open} />
      </g>
    );
  };
  return Body;
};

const darker = (hex: string, k = 0.86) => {
  const n = parseInt(hex.slice(1), 16);
  const c = [(n >> 16) & 255, (n >> 8) & 255, n & 255].map((v) => Math.round(v * k));
  return `#${c.map((v) => v.toString(16).padStart(2, "0")).join("")}`;
};

const Top: React.FC<{ l: Look }> = ({ l }) => {
  const s = l.topStyle ?? "tee";
  const edge = darker(l.top, 0.78);
  const accent = l.accent ?? edge;
  return (
    <>
      <path d="M54,560 C54,420 110,352 160,346 C176,370 224,370 240,346 C290,352 346,420 346,560 Z" fill={l.top} />
      {s === "tee" ? <path d="M160,346 C176,370 224,370 240,346" fill="none" stroke={edge} strokeWidth={10} strokeLinecap="round" /> : null}
      {s === "shirt" ? (
        <>
          <path d="M150,346 L200,404 L250,346" fill="none" stroke={accent} strokeWidth={8} strokeLinejoin="round" />
          <path d="M200,404 L200,560" stroke={edge} strokeWidth={4} />
        </>
      ) : null}
      {s === "kurta" ? <path d="M200,352 L200,440 M186,372 l14,0 M186,400 l14,0" stroke={accent} strokeWidth={5} strokeLinecap="round" /> : null}
      {s === "hoodie" ? (
        <>
          <path d="M120,372 C140,330 260,330 280,372 C250,394 150,394 120,372 Z" fill={edge} />
          <path d="M180,392 l-6,70 M220,392 l6,70" stroke={accent} strokeWidth={5} strokeLinecap="round" />
        </>
      ) : null}
      {s === "jacket" ? (
        <>
          <path d="M160,346 C176,370 224,370 240,346 L230,560 L170,560 Z" fill={accent} />
          <path d="M150,350 L184,430 L170,560 M250,350 L216,430 L230,560" fill="none" stroke={edge} strokeWidth={8} strokeLinejoin="round" />
        </>
      ) : null}
    </>
  );
};

const Hair: React.FC<{ l: Look; front: boolean }> = ({ l, front }) => {
  const h = l.hair;
  const hi = darker(h, 1.5);
  if (!front) return l.style === "long" ? <HairBack fill={h} to={430} /> : l.style === "bun" ? <circle cx={200} cy={40} r={44} fill={h} /> : null;
  switch (l.style) {
    case "bald":
      return <path d="M98,196 C94,160 100,138 112,124 L118,176 Z M302,196 C306,160 300,138 288,124 L282,176 Z" fill={h} opacity={0.7} />;
    case "buzz":
      return <path d="M100,176 C96,96 146,58 200,58 C254,58 304,96 300,176 C288,140 262,118 200,116 C138,118 112,140 100,176 Z" fill={h} opacity={0.85} />;
    case "curly": {
      const c: React.ReactNode[] = [];
      for (let i = 0; i <= 12; i++) {
        const a = Math.PI * (1.05 + (i * 0.9) / 12);
        c.push(<circle key={i} cx={200 + 108 * Math.cos(a)} cy={178 + 100 * Math.sin(a)} r={24 + (i % 3) * 3} fill={h} />);
      }
      [[150, 92], [200, 80], [250, 92], [176, 112], [226, 112]].forEach(([x, y], i) => c.push(<circle key={`t${i}`} cx={x} cy={y} r={26} fill={h} />));
      return <>{c}</>;
    }
    case "spiky":
      return <path d="M96,176 C92,120 110,92 130,80 L124,40 L162,70 L176,22 L202,64 L230,20 L242,68 L282,40 L276,86 C296,104 306,140 304,176 C290,140 264,124 200,122 C136,124 110,140 96,176 Z" fill={h} />;
    case "side":
      return (
        <>
          <path d="M100,184 C94,96 146,50 206,50 C268,50 310,96 300,184 C290,136 262,112 214,110 C170,124 128,134 100,184 Z" fill={h} />
          <path d="M124,96 C184,66 262,76 296,140" fill="none" stroke={hi} strokeWidth={5} strokeLinecap="round" opacity={0.6} />
        </>
      );
    case "wavy":
      return <path d="M94,200 C84,96 144,46 206,48 C272,50 318,100 306,200 C300,170 292,150 278,136 C268,150 252,146 240,130 C226,146 206,146 192,130 C176,148 154,148 140,132 C124,146 108,166 94,200 Z" fill={h} />;
    case "cap":
      return (
        <>
          <path d="M100,180 C98,150 104,132 116,122 L120,170 Z M300,180 C302,150 296,132 284,122 L280,170 Z" fill={h} />
          <path d="M96,140 C96,80 146,48 200,48 C254,48 304,80 304,140 Z" fill={l.capColor ?? "#222"} />
          <path d="M96,138 C150,128 250,128 304,138 C320,142 330,150 336,160 C290,150 150,148 96,150 Z" fill={darker(l.capColor ?? "#222", 0.7)} />
        </>
      );
    case "long":
    case "bun":
    case "short":
    default:
      return <path d="M98,186 C92,98 142,54 202,54 C262,54 310,98 302,186 C292,146 264,120 230,116 C210,128 180,130 160,120 C130,124 108,148 98,186 Z" fill={h} />;
  }
};

const Beard: React.FC<{ l: Look }> = ({ l }) => {
  const b = l.beard ?? "none";
  const c = l.beardColor ?? darker(l.hair, 0.9);
  if (b === "none") return null;
  return (
    <>
      {b === "stubble" || b === "full" ? (
        <path d="M100,214 C106,288 148,322 200,324 C252,322 294,288 300,214 C292,262 264,292 232,296 L168,296 C136,292 108,262 100,214 Z" fill={c} opacity={b === "full" ? 0.85 : 0.3} />
      ) : null}
      {b === "goatee" ? <ellipse cx={200} cy={304} rx={24} ry={14} fill={c} opacity={0.8} /> : null}
      {b !== "stubble" ? <path d="M168,254 Q200,240 232,254" fill="none" stroke={c} strokeWidth={9} strokeLinecap="round" opacity={0.9} /> : null}
    </>
  );
};

const Glasses: React.FC<{ l: Look }> = ({ l }) => {
  const g = l.glasses ?? "none";
  if (g === "none") return null;
  const round = g === "round";
  const fill = g === "shades" ? "#14141a" : "rgba(255,255,255,0.08)";
  return (
    <g fill={fill} stroke="#1c1c22" strokeWidth={6}>
      {[158, 242].map((x) => (round ? <circle key={x} cx={x} cy={204} r={30} /> : <rect key={x} x={x - 32} y={180} width={64} height={46} rx={10} />))}
      <path d="M188,200 q12,-8 24,0 M126,198 L100,192 M274,198 L300,192" fill="none" />
    </g>
  );
};

/** A mascot from a Look: hair behind, top, neck, face, hair, beard, face details, glasses. */
export const fromLook = (l: Look): React.FC<{ pose: Pose }> => {
  const Built: React.FC<{ pose: Pose }> = ({ pose }) => {
    const shade = darker(l.skin);
    const brow = -6 * pose.mouth;
    return (
      <g>
        <Hair l={l} front={false} />
        <rect x={170} y={290} width={60} height={72} rx={18} fill={shade} />
        <Top l={l} />
        <Face skin={l.skin} shade={shade} />
        <Hair l={l} front />
        <Beard l={l} />
        <path d={`M140,${168 + brow} q24,-10 44,-2 M216,${166 + brow} q20,-8 44,2`} fill="none" stroke={darker(l.hair, l.style === "bald" ? 0.7 : 1)} strokeWidth={l.female ? 6 : 8} strokeLinecap="round" />
        <Eyes y={204} iris={l.iris ?? "#3b2a20"} skin={l.skin} blink={pose.blink} />
        {l.female ? <path d="M134,190 l-8,-8 M266,190 l8,-8" stroke="#1a1210" strokeWidth={4} strokeLinecap="round" /> : null}
        <Nose shade={shade} />
        <Mouth y={266} open={pose.mouth} lip={l.female ? "#b4485a" : "#8a3c34"} teeth />
        <Glasses l={l} />
      </g>
    );
  };
  return Built;
};

const built = new Map<string, React.FC<{ pose: Pose }>>();

/** The hand-drawn mascot if there is one, else one built from the cast's look (cached per look). */
export const mascotOf = (who: string, look?: Look): React.FC<{ pose: Pose }> | undefined => {
  // A real photo wins over everything, even a hand-drawn mascot of the same person.
  if (look?.photo) {
    const key = `photo:${who}:${look.photo.src}`;
    if (!built.has(key)) built.set(key, fromPhoto(look.photo, who));
    return built.get(key);
  }
  if (MASCOTS[who]) return MASCOTS[who];
  if (!look) return undefined;
  const key = `${who}:${JSON.stringify(look)}`;
  if (!built.has(key)) built.set(key, fromLook(look));
  return built.get(key);
};
