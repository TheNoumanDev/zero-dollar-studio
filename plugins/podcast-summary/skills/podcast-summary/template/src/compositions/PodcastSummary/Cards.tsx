import React from "react";
import { AbsoluteFill, Easing, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { FONTS } from "../../config/theme";
import { useScale } from "../../lib/animation";
import { mono, UI } from "./brand";

// Info cards (top-left, what the speaker is talking about as a number, a ranking or a list) and the end card.

const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const COLORS = { mint: UI.mint, yellow: UI.yellow, orange: UI.orange, purple: UI.purple, green: UI.green, red: UI.red } as const;

export type InfoCardData =
  /** A number that counts up ("~5%", "700", "#1"), a mono label over it and a line under it. Keep `big` to ~8 characters. */
  | { kind: "stat"; label: string; big: string; sub?: string; color?: keyof typeof COLORS; at?: number }
  /** Bars, the `pick` row highlighted. */
  | { kind: "ranking"; title: string; rows: [string, number][]; unit?: string; pick?: number; at?: number }
  /** A short checklist / timeline, one row at a time. */
  | { kind: "list"; title: string; items: string[]; at?: number };

/** "~5%" → { pre: "~", n: 5, post: "%" } so the number can count up; null when there's no number in it. */
const splitNumber = (s: string) => {
  const m = s.match(/^(\D*)(\d[\d,.]*)(.*)$/);
  if (!m) return null;
  return { pre: m[1], n: Number(m[2].replace(/,/g, "")), dec: (m[2].split(".")[1] ?? "").length, post: m[3] };
};

/** One info card, top-left, from `at` (seconds) to `until`. */
export const InfoCard: React.FC<{ card: InfoCardData; at: number; until: number }> = ({ card, at, until }) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const wide = width > height;
  const u = useScale() * (wide ? 0.8 : 0.95);
  const t = frame / fps - at;
  if (t < 0 || frame / fps > until) return null;
  const inK = spring({ frame: t * fps, fps, config: { damping: 16, stiffness: 140 } });
  const outK = interpolate(frame / fps, [until - 0.35, until], [1, 0], clamp);
  const k = Math.min(inK, outK);
  const p = (a: number, d = 0.45) => interpolate(t, [a, a + d], [0, 1], { ...clamp, easing: Easing.out(Easing.cubic) });

  let body: React.ReactNode = null;
  if (card.kind === "stat") {
    const c = COLORS[card.color ?? "mint"];
    const num = splitNumber(card.big);
    const shown = num ? `${num.pre}${(num.n * p(0.15, 0.9)).toFixed(num.dec)}${num.post}` : card.big;
    body = (
      <>
        <div style={mono(30 * u, UI.purple, { letterSpacing: 3 * u, textTransform: "uppercase" })}>{card.label}</div>
        <div style={{ fontFamily: FONTS.display, fontWeight: 700, fontSize: 150 * u, lineHeight: 1, color: c, marginTop: 10 * u, textShadow: `0 0 ${40 * u}px ${c}66`, whiteSpace: "nowrap" }}>{shown}</div>
        {card.sub ? <div style={{ fontFamily: FONTS.display, fontWeight: 700, fontSize: 44 * u, color: UI.text, marginTop: 12 * u, opacity: p(0.5), maxWidth: 640 * u, lineHeight: 1.15 }}>{card.sub}</div> : null}
      </>
    );
  } else if (card.kind === "ranking") {
    const max = Math.max(...card.rows.map((r) => r[1]));
    body = (
      <>
        <div style={mono(28 * u, UI.purple, { letterSpacing: 3 * u, textTransform: "uppercase", marginBottom: 18 * u })}>{card.title}</div>
        {card.rows.map(([name, n], i) => {
          const hot = i === (card.pick ?? 0);
          const g = p(0.2 + i * 0.18, 0.6);
          return (
            <div key={name} style={{ marginTop: 14 * u, opacity: interpolate(g, [0, 0.3], [0, 1], clamp) }}>
              <div style={{ display: "flex", justifyContent: "space-between", fontFamily: FONTS.display, fontWeight: 700, fontSize: (hot ? 44 : 36) * u, color: hot ? UI.yellow : UI.text }}>
                <span>{hot ? "👑 " : ""}{name}</span>
                <span>{(n * g).toFixed(1)}{card.unit ?? ""}</span>
              </div>
              <div style={{ height: (hot ? 14 : 10) * u, borderRadius: 99, background: "#ffffff1a", marginTop: 6 * u }}>
                <div style={{ width: `${(n / max) * 100 * g}%`, height: "100%", borderRadius: 99, background: hot ? UI.yellow : UI.mint }} />
              </div>
            </div>
          );
        })}
      </>
    );
  } else {
    body = (
      <>
        <div style={mono(28 * u, UI.purple, { letterSpacing: 3 * u, textTransform: "uppercase", marginBottom: 8 * u })}>{card.title}</div>
        {card.items.map((it, i) => {
          const g = p(0.3 + i * 0.5, 0.35);
          return (
            <div key={it} style={{ display: "flex", alignItems: "center", gap: 16 * u, marginTop: 16 * u, opacity: g, translate: `${(1 - g) * -30 * u}px 0`, fontFamily: FONTS.display, fontWeight: 700, fontSize: 42 * u, color: UI.text }}>
              <span style={{ width: 16 * u, height: 16 * u, borderRadius: "50%", background: i === card.items.length - 1 ? UI.yellow : UI.mint, flexShrink: 0 }} />
              {it}
            </div>
          );
        })}
      </>
    );
  }

  return (
    <div
      style={{
        position: "absolute",
        left: (wide ? 56 : 50) * (wide ? 1 : u),
        top: wide ? 56 : 230 * u,
        minWidth: (card.kind === "stat" ? 420 : 620) * u,
        maxWidth: 760 * u,
        padding: `${30 * u}px ${38 * u}px`,
        borderRadius: 30 * u,
        background: "rgba(11,18,32,0.86)",
        border: `${3 * u}px solid ${UI.purple}66`,
        boxShadow: `0 ${20 * u}px ${60 * u}px #000a`,
        opacity: k,
        translate: `${(1 - k) * -80 * u}px 0`,
        scale: 0.9 + 0.1 * k,
        transformOrigin: "left top",
      }}
    >
      {body}
    </div>
  );
};

/** End card: where to watch the full episode (credit the show), then subscribe and your handle. */
export const EndScreen: React.FC<{ at: number; title: string; accent: string; items: string[]; handle?: string }> = ({ at, title, accent, items, handle }) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const wide = width > height;
  const u = useScale() * (wide ? 0.8 : 1);
  const t = frame / fps - at;
  if (t < -0.3) return null;
  const k = interpolate(t, [-0.3, 0.2], [0, 1], clamp);
  const p = (a: number) => interpolate(t, [a, a + 0.35], [0, 1], { ...clamp, easing: Easing.out(Easing.cubic) });
  return (
    <AbsoluteFill style={{ background: `rgba(14,21,37,${0.97 * k})`, justifyContent: "center", alignItems: "center" }}>
      <AbsoluteFill style={{ background: `radial-gradient(circle at 50% 45%, ${UI.purple}55, transparent 60%)`, opacity: k }} />
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 28 * u, opacity: k, textAlign: "center", maxWidth: (wide ? 1500 : 960) * u }}>
        <div style={{ fontFamily: FONTS.display, fontWeight: 700, fontSize: 80 * u, color: UI.text, lineHeight: 1.1 }}>
          {title} <span style={{ color: UI.mint }}>{accent}</span>
        </div>
        {items.map((it, i) => (
          <div key={it} style={{ fontFamily: FONTS.display, fontWeight: 700, fontSize: 50 * u, color: UI.text, opacity: p(0.3 + i * 0.3) }}>
            <span style={{ color: UI.green }}>✓</span> {it}
          </div>
        ))}
        <div style={{ display: "flex", gap: 24 * u, marginTop: 16 * u, scale: p(0.3 + items.length * 0.3) }}>
          <div style={{ fontFamily: FONTS.display, fontWeight: 700, fontSize: 50 * u, color: "#fff", background: "#FF0033", padding: `${16 * u}px ${44 * u}px`, borderRadius: 999 }}>Subscribe</div>
          {handle ? <div style={{ fontFamily: FONTS.display, fontWeight: 700, fontSize: 50 * u, color: UI.ink, background: UI.yellow, padding: `${16 * u}px ${44 * u}px`, borderRadius: 999 }}>{handle}</div> : null}
        </div>
      </div>
    </AbsoluteFill>
  );
};
