import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import captions from "../../../public/fridge-drama/captions.json";
import { FONTS } from "../../config/theme";
import { mix, progress } from "../../lib/animation";
import { script } from "./data";

type Word = (typeof captions)[number];
type Page = { words: Word[]; startMs: number; endMs: number; speaker: string };

const MAX_WORDS = 3;

/** Groups words into short pages: a new page per speaker, sentence end, or 3 words. */
const pages: Page[] = (() => {
  const out: Page[] = [];
  let cur: Word[] = [];
  const flush = () => {
    if (cur.length) out.push({ words: cur, startMs: cur[0].startMs, endMs: cur[cur.length - 1].endMs, speaker: cur[0].speaker });
    cur = [];
  };
  captions.forEach((w, i) => {
    if (cur.length && (w.speaker !== cur[0].speaker || cur.length >= MAX_WORDS)) flush();
    cur.push(w);
    const next = captions[i + 1];
    if (/[.?!]$/.test(w.text.trim()) && next && next.startMs - w.endMs > 150) flush();
  });
  flush();
  // Keep each page up until the next one starts (max 600 ms of hang time).
  out.forEach((p, i) => {
    const next = out[i + 1];
    p.endMs = next ? Math.min(next.startMs, p.endMs + 600) : p.endMs + 600;
  });
  return out;
})();

const colorOf = (speaker: string) =>
  speaker === "all" ? "#FFEB3B" : script.characters[speaker as keyof typeof script.characters].color;

export const Captions: React.FC<{ y: number; u: number }> = ({ y, u }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const ms = (frame / fps) * 1000;
  const page = pages.find((p) => ms >= p.startMs && ms < p.endMs);
  if (!page) return null;

  const pageFrame = Math.round((page.startMs / 1000) * fps);
  const t = progress(frame - pageFrame, fps, 0, 0.18);
  const color = colorOf(page.speaker);
  const name = page.speaker === "all" ? "Everyone" : script.characters[page.speaker as keyof typeof script.characters].name;

  return (
    <div
      style={{
        position: "absolute",
        top: y,
        left: 60 * u,
        right: 60 * u,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: 14 * u,
        scale: mix(t, 0.85, 1),
        opacity: t,
      }}
    >
      <div
        style={{
          fontFamily: FONTS.body,
          fontWeight: 600,
          fontSize: 38 * u,
          color: "#1d1d1f",
          background: color,
          padding: `${6 * u}px ${18 * u}px`,
          borderRadius: 999,
          border: `${3 * u}px solid #1d1d1f`,
        }}
      >
        {name}
      </div>
      <div
        style={{
          fontFamily: FONTS.display,
          fontWeight: 700,
          fontSize: 96 * u,
          lineHeight: 1.1,
          textAlign: "center",
          color: "#fff",
          WebkitTextStroke: `${12 * u}px #1d1d1f`,
          paintOrder: "stroke fill",
          textTransform: "uppercase",
        }}
      >
        {page.words.map((w, i) => {
          const active = ms >= w.startMs;
          return (
            <span key={i} style={{ color: active ? color : "#fff" }}>
              {w.text}
            </span>
          );
        })}
      </div>
    </div>
  );
};
