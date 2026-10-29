import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { FONTS } from "../../config/theme";
import type { CastMember, Word } from "./types";

type Page = { words: Word[]; startMs: number; endMs: number; speaker: string };

/** Short pages: a new page per speaker, sentence end, pause over 300 ms, or `maxWords`. */
export const captionPages = (words: Word[], maxWords: number): Page[] => {
  const out: Page[] = [];
  let cur: Word[] = [];
  const flush = () => {
    if (cur.length) out.push({ words: cur, startMs: cur[0].startMs, endMs: cur[cur.length - 1].endMs, speaker: cur[0].speaker ?? "" });
    cur = [];
  };
  words.forEach((w, i) => {
    const prev = words[i - 1];
    if (cur.length && (w.speaker !== cur[0].speaker || cur.length >= maxWords || (prev && w.startMs - prev.endMs > 300))) flush();
    cur.push(w);
    if (/[.?!]$/.test(w.text.trim())) flush();
  });
  flush();
  // Hold each page until the next one starts (at most 500 ms of hang time).
  out.forEach((p, i) => {
    const next = out[i + 1];
    p.endMs = next ? Math.min(next.startMs, p.endMs + 500) : p.endMs + 500;
  });
  return out;
};

/** Word-by-word captions; the spoken word lights up in the speaker's colour. */
export const Captions: React.FC<{ pages: Page[]; cast: Record<string, CastMember>; top: number; size: number }> = ({ pages, cast, top, size }) => {
  const frame = useCurrentFrame();
  const { fps, width } = useVideoConfig();
  const ms = (frame / fps) * 1000;
  const page = pages.find((p) => ms >= p.startMs - 60 && ms < p.endMs);
  if (!page) return null;
  const color = cast[page.speaker]?.color ?? "#FFD84D";
  return (
    <div
      style={{
        position: "absolute",
        top,
        left: width * 0.08,
        right: width * 0.08,
        textAlign: "center",
        fontFamily: FONTS.display,
        fontWeight: 700,
        fontSize: size,
        lineHeight: 1.1,
        textTransform: "uppercase",
        color: "#fff",
        WebkitTextStroke: `${size * 0.15}px #1d1d1f`,
        paintOrder: "stroke fill",
      }}
    >
      {page.words.map((w, i) => (
        <span key={i} style={{ color: ms >= w.startMs ? color : "#fff" }}>
          {(i ? " " : "") + w.text.trim()}
        </span>
      ))}
    </div>
  );
};
