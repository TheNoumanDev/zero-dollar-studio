import React from "react";
import { Easing, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { FONTS } from "../config/theme";
import { useScale } from "../lib/animation";

const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

/** One word of public/<slug>/captions.json (tools/captions.mjs). */
export type KaraokeWord = { text: string; startMs: number; endMs: number; emphasis?: boolean };

/** Split into chunks of up to `perChunk` words, breaking early at a pause or a sentence end. */
const chunk = (words: KaraokeWord[], perChunk: number) => {
  const out: KaraokeWord[][] = [];
  let cur: KaraokeWord[] = [];
  words.forEach((w, i) => {
    cur.push(w);
    const next = words[i + 1];
    const pause = next ? next.startMs - w.endMs > 450 : true;
    if (cur.length >= perChunk || pause || /[.!?]$/.test(w.text.trim())) {
      out.push(cur);
      cur = [];
    }
  });
  if (cur.length) out.push(cur);
  return out;
};

/**
 * Karaoke captions: the current 2–5 word chunk is on screen at once, spoken words turn solid,
 * upcoming words wait in grey, keywords (and words the voice stresses) take the accent colour,
 * and the word being said pops slightly. Viewers can read ahead, which helps on muted autoplay.
 * Position it with `style` (design px are scaled for you); keep it clear of the Reels dead zones
 * (y < 220, y > 1540, and the right-side button rail below y 1000). `tools/qa.py --layout` checks this.
 */
export const Karaoke: React.FC<{
  words: KaraokeWord[];
  perChunk?: number;
  keywords?: string[];
  spokenColor?: string;
  upcomingColor?: string;
  keywordColor?: string;
  fontFamily?: string;
  /** Font size in design px (1920-wide design). */
  size?: number;
  /** Box behind the words (e.g. "rgba(255,255,255,0.92)" for a light card); none by default. */
  background?: string;
  style?: React.CSSProperties;
  /** Outline captions pure magenta for tools/qa.py's layout check. */
  qa?: boolean;
}> = ({
  words,
  perChunk = 4,
  keywords = [],
  spokenColor = "#FFFFFF",
  upcomingColor = "rgba(255,255,255,0.45)",
  keywordColor = "#FFD23F",
  fontFamily = FONTS.caption,
  size = 140,
  background,
  style,
  qa,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const u = useScale();
  const ms = (frame / fps) * 1000;
  const chunks = React.useMemo(() => chunk(words, perChunk), [words, perChunk]);
  const keys = React.useMemo(() => new Set(keywords.map((k) => k.toLowerCase())), [keywords]);
  const clean = (t: string) => t.trim().toLowerCase().replace(/[^\p{L}\p{N}']/gu, "");

  // The chunk on screen: from its first word until the next chunk starts (or 600 ms after its last word).
  const idx = chunks.findIndex((c, i) => {
    const end = chunks[i + 1] ? Math.min(chunks[i + 1]![0]!.startMs, c[c.length - 1]!.endMs + 600) : c[c.length - 1]!.endMs + 600;
    return ms >= c[0]!.startMs - 80 && ms < end;
  });
  if (idx < 0) return null;
  const current = chunks[idx]!;
  const enter = interpolate(ms, [current[0]!.startMs - 80, current[0]!.startMs + 120], [0, 1], {
    ...clamp,
    easing: Easing.out(Easing.cubic),
  });

  return (
    <div style={{ position: "absolute", display: "flex", justifyContent: "center", ...style }}>
      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          justifyContent: "center",
          columnGap: size * 0.38 * u,
          rowGap: size * 0.08 * u,
          fontFamily,
          fontWeight: 900,
          fontSize: size * u,
          lineHeight: 1.1,
          padding: background ? `${size * 0.18 * u}px ${size * 0.32 * u}px` : 0,
          background,
          borderRadius: size * 0.3 * u,
          opacity: enter,
          translate: `0 ${(1 - enter) * 24 * u}px`,
          outline: qa ? "4px solid #FF00FF" : undefined,
          backgroundColor: qa ? "#FF00FF" : background,
        }}
      >
        {current.map((w, i) => {
          const spoken = ms >= w.startMs;
          const active = spoken && ms < w.endMs;
          const key = w.emphasis || keys.has(clean(w.text));
          const pop = active ? interpolate(ms, [w.startMs, w.startMs + 90, w.endMs], [1, 1.07, 1.02], clamp) : 1;
          return (
            <span
              key={i}
              style={{
                color: spoken ? (key ? keywordColor : spokenColor) : upcomingColor,
                scale: pop,
                display: "inline-block",
                textShadow: background ? undefined : `0 ${4 * u}px ${18 * u}px rgba(0,0,0,0.55)`,
              }}
            >
              {w.text.trim()}
            </span>
          );
        })}
      </div>
    </div>
  );
};
