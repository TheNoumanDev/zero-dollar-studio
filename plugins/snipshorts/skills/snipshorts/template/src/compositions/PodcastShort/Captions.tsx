import React, { useMemo } from "react";
import { Easing, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { FONTS } from "../../config/theme";
import { useScale } from "../../lib/animation";
import type { Word } from "./types";

const MAX_WORDS = 3;
const ACTIVE = "#FFE600";
const EMPHASIS = "#3DFF8C";

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

export const Captions: React.FC<{ words: Word[]; emphasis: number[]; y: number; qa?: boolean }> = ({ words, emphasis, y, qa }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const u = useScale();
  const t = frame / fps;
  const pages = useMemo(() => toPages(words), [words]);
  const emph = useMemo(() => new Set(emphasis), [emphasis]);
  const page = pages.find((p) => t >= p.start && t < p.end);
  if (!page) return null;

  const pop = interpolate(t, [page.start, page.start + 0.14], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.back(2)),
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
        columnGap: 26 * u,
        rowGap: 6 * u,
        scale: interpolate(pop, [0, 1], [0.8, 1]),
        opacity: Math.min(1, pop * 2),
        outline: qa ? "6px solid #FF00FF" : undefined,
      }}
    >
      {page.items.map(({ word, index }) => {
        const isActive = t >= word.s && t < word.e + 0.08;
        const isEmph = emph.has(index);
        const spoken = t >= word.s;
        const bump = isEmph && isActive ? interpolate(t, [word.s, word.s + 0.1], [1.3, 1.15], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) : 1;
        return (
          <span
            key={index}
            style={{
              fontFamily: FONTS.caption,
              fontWeight: 900,
              fontSize: (isEmph ? 175 : 150) * u,
              lineHeight: 1.05,
              textTransform: "uppercase",
              color: isEmph && spoken ? EMPHASIS : isActive ? ACTIVE : "#FFFFFF",
              WebkitTextStroke: `${14 * u}px #000`,
              paintOrder: "stroke fill",
              textShadow: `0 ${8 * u}px ${18 * u}px rgba(0,0,0,0.55)`,
              scale: bump,
              display: "inline-block",
              // Room for the bump and tilt so a highlighted word never touches its neighbours.
              // The bump scales the word up to 1.3×: reserve half the extra width on each side (≈0.65 em per letter).
              marginInline: isEmph ? Math.max(30 * u, clean(word.w).length * 175 * u * 0.65 * 0.15) : 0,
              rotate: isEmph && isActive ? "-3deg" : "0deg",
            }}
          >
            {clean(word.w)}
          </span>
        );
      })}
    </div>
  );
};
