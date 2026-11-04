import React, { useMemo } from "react";
import { Easing, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { loadFont as loadBangers } from "@remotion/google-fonts/Bangers";
import { loadFont as loadInter } from "@remotion/google-fonts/Inter";
import { FONTS } from "../../config/theme";
import { useScale } from "../../lib/animation";
import type { CaptionStyle, Word } from "./types";

const bangers = loadBangers("normal", { weights: ["400"], subsets: ["latin"] });
const inter = loadInter("normal", { weights: ["800"], subsets: ["latin"] });

const MAX_WORDS = 3;
const ACTIVE = "#FFE600";
const EMPHASIS = "#3DFF8C";
// Bounce: each page takes the next colour for its spoken word.
const BOUNCE_COLORS = ["#FFE600", "#FF5CDB", "#3DFFB0", "#5CC8FF"];

/**
 * bold: heavy all-caps, yellow active word, green emphasis (default; business, education, podcasts).
 * bounce: comic font, words spring in, a new colour each page (entertainment, funny clips).
 * clean: sentence case, soft fade, words light up as they are said (interviews, calm or serious talk).
 */
const STYLES: Record<CaptionStyle, { font: string; size: number; emph: number; upper: boolean; stroke: number; gap: number }> = {
  bold: { font: FONTS.caption, size: 150, emph: 175, upper: true, stroke: 14, gap: 26 },
  bounce: { font: bangers.fontFamily, size: 165, emph: 190, upper: true, stroke: 12, gap: 30 },
  clean: { font: inter.fontFamily, size: 124, emph: 124, upper: false, stroke: 0, gap: 22 },
};

type Page = { start: number; end: number; items: { word: Word; index: number }[] };

const clean = (w: string) => w.replace(/^[,.;:]+/, "").trim();

/** Short pages: break on 3 words, sentence ends, or a pause. */
const toPages = (words: Word[]): Page[] => {
  const pages: Page[] = [];
  let cur: Page["items"] = [];
  const flush = () => {
    if (cur.length) pages.push({ start: cur[0].word.s, end: cur[cur.length - 1].word.e, items: cur });
    cur = [];
  };
  words.forEach((word, index) => {
    const prev = words[index - 1];
    if (cur.length >= MAX_WORDS || (prev && word.s - prev.e > 0.35)) flush();
    cur.push({ word, index });
    if (/[.?!]$/.test(word.w)) flush();
  });
  flush();
  pages.forEach((p, i) => {
    const next = pages[i + 1];
    p.end = next ? Math.min(next.start, p.end + 0.5) : p.end + 0.5;
  });
  return pages;
};

export const Captions: React.FC<{ words: Word[]; emphasis: number[]; y: number; style?: CaptionStyle; qa?: boolean }> = ({
  words,
  emphasis,
  y,
  style = "bold",
  qa,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const u = useScale();
  const t = frame / fps;
  const pages = useMemo(() => toPages(words), [words]);
  const emph = useMemo(() => new Set(emphasis), [emphasis]);
  const pageIndex = pages.findIndex((p) => t >= p.start && t < p.end);
  if (pageIndex === -1) return null;
  const page = pages[pageIndex];
  const S = STYLES[style] ?? STYLES.bold;

  const pop = interpolate(t, [page.start, page.start + (style === "clean" ? 0.2 : 0.14)], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: style === "clean" ? Easing.out(Easing.cubic) : Easing.out(Easing.back(2)),
  });

  return (
    <div
      style={{
        position: "absolute",
        top: y,
        left: 70 * u,
        right: 70 * u,
        display: "flex",
        flexWrap: "wrap",
        justifyContent: "center",
        alignItems: "center",
        columnGap: S.gap * u,
        rowGap: 6 * u,
        scale: style === "bold" ? interpolate(pop, [0, 1], [0.8, 1]) : 1,
        opacity: style === "clean" ? pop : Math.min(1, pop * 2),
        translate: style === "clean" ? `0 ${(1 - pop) * 18 * u}px` : undefined,
        outline: qa ? "6px solid #FF00FF" : undefined,
      }}
    >
      {page.items.map(({ word, index }, k) => {
        const isActive = t >= word.s && t < word.e + 0.08;
        const isEmph = emph.has(index);
        const spoken = t >= word.s;
        let color = "#FFFFFF";
        let scale = 1;
        let rotate = "0deg";
        let opacity = 1;
        if (style === "bold") {
          color = isEmph && spoken ? EMPHASIS : isActive ? ACTIVE : "#FFFFFF";
          scale = isEmph && isActive ? interpolate(t, [word.s, word.s + 0.1], [1.3, 1.15], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) : 1;
          rotate = isEmph && isActive ? "-3deg" : "0deg";
        } else if (style === "bounce") {
          // Each word springs 70% → 120% → 100% as it is said.
          scale = spoken ? interpolate(t, [word.s, word.s + 0.08, word.s + 0.2], [0.7, 1.2, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) : 0.7;
          opacity = spoken ? 1 : 0.0;
          color = isActive || (isEmph && spoken) ? BOUNCE_COLORS[pageIndex % BOUNCE_COLORS.length] : "#FFFFFF";
          rotate = `${(k % 2 === 0 ? -1 : 1) * (isActive ? 4 : 2)}deg`;
        } else {
          opacity = spoken ? 1 : 0.5;
          color = isEmph && spoken ? ACTIVE : "#FFFFFF";
        }
        return (
          <span
            key={index}
            style={{
              fontFamily: S.font,
              fontWeight: style === "bounce" ? 400 : 900,
              fontSize: (isEmph ? S.emph : S.size) * u,
              lineHeight: 1.05,
              letterSpacing: style === "bounce" ? 2 * u : undefined,
              textTransform: S.upper ? "uppercase" : "none",
              color,
              opacity,
              WebkitTextStroke: S.stroke ? `${S.stroke * u}px #000` : undefined,
              paintOrder: "stroke fill",
              textShadow: style === "clean" ? `0 ${4 * u}px ${16 * u}px rgba(0,0,0,0.85), 0 0 ${3 * u}px rgba(0,0,0,0.9)` : `0 ${8 * u}px ${18 * u}px rgba(0,0,0,0.55)`,
              scale,
              display: "inline-block",
              // Room for the bump and tilt so a highlighted word never touches its neighbours.
              // The bump scales the word up to 1.3×: reserve half the extra width on each side (≈0.65 em per letter).
              marginInline: style === "bold" && isEmph ? Math.max(30 * u, clean(word.w).length * S.emph * u * 0.65 * 0.15) : 0,
              rotate,
            }}
          >
            {clean(word.w)}
          </span>
        );
      })}
    </div>
  );
};
