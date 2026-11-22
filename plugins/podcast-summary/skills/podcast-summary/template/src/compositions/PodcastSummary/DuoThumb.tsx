import React from "react";
import { AbsoluteFill, Img, staticFile } from "remotion";
import { FONTS } from "../../config/theme";

// Two-person podcast thumbnail: host cut out on the left, guest on the right, both
// facing in, the episode's big line stacked in the middle. `*word*` = accent colour, `boxLine` = yellow box line.
// Cutouts live in public/summary-thumbs/<clip>/ (bg.jpg + the people PNGs).

export type DuoThumbProps = {
  clip: string;
  left: { file: string; h: number; bottom?: number; x?: number; flip?: boolean };
  right: { file: string; h: number; bottom?: number; x?: number; flip?: boolean };
  lines: string[];
  boxLine?: number;
  /** "dark" = blurred set; "light" = white */
  theme?: "dark" | "light";
  /** small line above the title */
  kicker?: string;
  textTop?: number;
  /** text column inset from each side in px (default 390) */
  inset?: number;
};

const YEL = "#FFE81A";
const RED = "#E3122C";
const ink = "#0B0D17";

export const DuoThumb: React.FC<DuoThumbProps> = ({ clip, left, right, lines, boxLine = -1, theme = "dark", kicker, textTop, inset = 390 }) => {
  const f = (n: string) => staticFile(`summary-thumbs/${clip}/${n}`);
  const dark = theme === "dark";
  const longest = Math.max(...lines.map((l) => l.replace(/\*/g, "").length));
  const size = Math.min(130, (1280 - 2 * inset - 20) / (longest * 0.6));
  const accent = dark ? YEL : RED;
  const rich = (s: string) =>
    s.split(/(\*[^*]+\*)/).map((p, i) => (p.startsWith("*") ? <span key={i} style={{ color: accent }}>{p.slice(1, -1)}</span> : <span key={i}>{p}</span>));
  const person = (p: DuoThumbProps["left"], side: "left" | "right") => (
    <Img
      src={f(p.file)}
      style={{ position: "absolute", bottom: p.bottom ?? -30, [side]: p.x ?? -40, height: p.h, scale: p.flip ? "-1 1" : undefined, filter: dark ? "brightness(1.15) contrast(1.06) drop-shadow(0 0 30px rgba(0,0,0,0.6))" : "drop-shadow(0 10px 30px rgba(0,0,0,0.18))" }}
    />
  );
  return (
    <AbsoluteFill style={{ background: dark ? "#0d0907" : "#fff", overflow: "hidden" }}>
      {dark ? (
        <>
          <Img src={f("bg.jpg")} style={{ position: "absolute", width: "100%", height: "100%", objectFit: "cover", filter: "blur(14px) brightness(0.3) saturate(1.2)", scale: 1.15 }} />
          <AbsoluteFill style={{ background: "radial-gradient(ellipse at 50% 45%, rgba(255,200,60,0.16) 0%, rgba(0,0,0,0) 50%)" }} />
        </>
      ) : (
        <AbsoluteFill style={{ background: "radial-gradient(ellipse at 50% 40%, #ffffff 0%, #ffffff 55%, #e9e9e9 100%)" }} />
      )}
      {person(left, "left")}
      {person(right, "right")}
      <div style={{ position: "absolute", left: inset, right: inset, top: textTop ?? "50%", translate: textTop == null ? "0 -50%" : undefined, display: "flex", flexDirection: "column", alignItems: "center", textAlign: "center", fontFamily: FONTS.caption, fontWeight: 900, textTransform: "uppercase", letterSpacing: -2 }}>
        {kicker ? <div style={{ fontSize: 40, color: dark ? "#fff" : "#111", letterSpacing: 1, marginBottom: 6, textShadow: dark ? "0 4px 14px rgba(0,0,0,0.8)" : undefined }}>{kicker}</div> : null}
        {lines.map((l, i) =>
          i === boxLine ? (
            <div key={i} style={{ background: YEL, color: "#111", fontSize: size, lineHeight: 1, padding: "6px 18px 12px", margin: "6px 0", whiteSpace: "nowrap", rotate: "-2deg", boxShadow: "0 8px 24px rgba(0,0,0,0.5)" }}>{l.replace(/\*/g, "")}</div>
          ) : (
            <div key={i} style={{ fontSize: size, lineHeight: 1, color: dark ? "#fff" : "#111", whiteSpace: "nowrap", ...(dark ? { WebkitTextStroke: `10px ${ink}`, paintOrder: "stroke fill" as const, textShadow: "0 6px 24px rgba(0,0,0,0.8)" } : {}) }}>{rich(l)}</div>
          ),
        )}
      </div>
    </AbsoluteFill>
  );
};
