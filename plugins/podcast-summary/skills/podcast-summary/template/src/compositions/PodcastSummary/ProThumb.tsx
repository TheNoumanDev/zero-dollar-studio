import React from "react";
import { AbsoluteFill, Img, staticFile } from "remotion";
import { FONTS } from "../../config/theme";

// One-face podcast thumbnails in the layouts big podcast channels use. Three layouts:
//  - "fo":    white background, face big at one edge, 3 lines of heavy black text with red keywords.
//  - "tweet": white background, face at one edge, a quote card in the style of a verified post.
//  - "dark":  blurred dark set, face big, white caps + one yellow highlight box.
// Text is `*word*` for the accent colour. Cutouts live in public/summary-thumbs/<clip>/.

export type ProThumbProps = {
  clip: string;
  layout: "fo" | "tweet" | "dark";
  person: string;
  /** Face side: the person stands at this edge, text on the other. */
  side?: "left" | "right";
  flip?: boolean;
  /** Person height in px and how far below the frame bottom it starts. */
  h?: number;
  bottom?: number;
  /** px the person is pushed past their edge (default 30). */
  inset?: number;
  lines: string[];
  /** tweet layout: name + avatar file */
  name?: string;
  avatar?: string;
  /** dark layout: the line index drawn in the yellow box */
  boxLine?: number;
};

const RED = "#E3122C";
const YEL = "#FFE81A";

const rich = (s: string, accent: string) =>
  s.split(/(\*[^*]+\*)/).map((p, i) => (p.startsWith("*") ? <span key={i} style={{ color: accent }}>{p.slice(1, -1)}</span> : <span key={i}>{p}</span>));

export const ProThumb: React.FC<ProThumbProps> = ({ clip, layout, person, side = "right", flip, h = 760, bottom = -40, lines, name, avatar, boxLine = 1, inset = 30 }) => {
  const f = (n: string) => staticFile(`summary-thumbs/${clip}/${n}`);
  const dark = layout === "dark";
  const textSide: React.CSSProperties = side === "right" ? { left: 40, right: 560 } : { right: 40, left: 560 };
  const longest = Math.max(...lines.map((l) => l.replace(/\*/g, "").length));
  const size = Math.min(dark ? 120 : 112, (680 / (longest * 0.62)));
  return (
    <AbsoluteFill style={{ background: dark ? "#0d0907" : "#ffffff", overflow: "hidden" }}>
      {dark ? (
        <>
          <Img src={f("bg.jpg")} style={{ position: "absolute", width: "100%", height: "100%", objectFit: "cover", filter: "blur(14px) brightness(0.35) saturate(1.2)", scale: 1.15 }} />
          <AbsoluteFill style={{ background: side === "right" ? "linear-gradient(90deg, rgba(0,0,0,0.75) 0%, rgba(0,0,0,0) 65%)" : "linear-gradient(270deg, rgba(0,0,0,0.75) 0%, rgba(0,0,0,0) 65%)" }} />
        </>
      ) : (
        <AbsoluteFill style={{ background: "radial-gradient(ellipse at 50% 40%, #ffffff 0%, #ffffff 55%, #ececec 100%)" }} />
      )}

      <Img
        src={f(person)}
        style={{ position: "absolute", bottom, [side]: -inset, height: h, scale: flip ? "-1 1" : undefined, filter: dark ? "brightness(1.12) contrast(1.05)" : "drop-shadow(0 10px 30px rgba(0,0,0,0.18))" }}
      />

      {layout === "tweet" ? (
        <div style={{ position: "absolute", ...textSide, top: "50%", translate: "0 -50%", background: "#fff", borderRadius: 34, padding: "30px 38px 36px", boxShadow: "0 14px 50px rgba(0,0,0,0.22)", border: "2px solid #e6e6e6" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 16, marginBottom: 16 }}>
            {avatar ? <Img src={f(avatar)} style={{ width: 92, height: 92, borderRadius: "50%", objectFit: "cover", objectPosition: "50% 15%" }} /> : null}
            <div style={{ fontFamily: FONTS.caption, fontWeight: 800, fontSize: 46, color: "#111" }}>{name}</div>
            <svg width={40} height={40} viewBox="0 0 24 24"><path fill="#1D9BF0" d="M22.5 12.5c0-1.58-.88-2.95-2.15-3.6.15-.44.23-.91.23-1.4 0-2.21-1.71-4-3.82-4-.47 0-.92.08-1.34.25C14.82 2.42 13.53 1.5 12 1.5s-2.82.92-3.42 2.25c-.42-.17-.87-.25-1.34-.25-2.11 0-3.82 1.79-3.82 4 0 .49.08.96.23 1.4-1.27.65-2.15 2.02-2.15 3.6 0 1.5.8 2.8 1.97 3.48-.03.24-.05.48-.05.72 0 2.21 1.71 4 3.82 4 .47 0 .92-.09 1.34-.25.6 1.33 1.89 2.25 3.42 2.25s2.82-.92 3.42-2.25c.42.16.87.25 1.34.25 2.11 0 3.82-1.79 3.82-4 0-.24-.02-.48-.05-.72 1.17-.68 1.97-1.98 1.97-3.48zM10.3 16.8 6.6 13.1l1.4-1.4 2.3 2.3 5.6-5.6 1.4 1.4-7 7z" /></svg>
          </div>
          <div style={{ fontFamily: FONTS.caption, fontWeight: 800, fontSize: size * 1.02, lineHeight: 1.06, color: "#111", letterSpacing: -1 }}>
            {lines.map((l, i) => <div key={i}>{rich(l, RED)}</div>)}
          </div>
        </div>
      ) : (
        <div style={{ position: "absolute", ...textSide, top: "50%", translate: "0 -50%", display: "flex", flexDirection: "column", alignItems: side === "right" ? "flex-start" : "flex-end", textAlign: side === "right" ? "left" : "right" }}>
          {lines.map((l, i) =>
            dark && i === boxLine ? (
              <div key={i} style={{ background: YEL, color: "#111", fontFamily: FONTS.caption, fontWeight: 900, fontSize: size, lineHeight: 1, padding: "8px 18px 12px", margin: "8px 0", textTransform: "uppercase", letterSpacing: -2, whiteSpace: "nowrap" }}>{l.replace(/\*/g, "")}</div>
            ) : (
              <div key={i} style={{ fontFamily: FONTS.caption, fontWeight: 900, fontSize: size, lineHeight: 1.0, color: dark ? "#fff" : "#111", textTransform: dark ? "uppercase" : undefined, letterSpacing: -2, whiteSpace: "nowrap", textShadow: dark ? "0 6px 24px rgba(0,0,0,0.7)" : undefined }}>{rich(l, dark ? YEL : RED)}</div>
            ),
          )}
        </div>
      )}
    </AbsoluteFill>
  );
};
