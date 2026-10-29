import React from "react";
import { Easing, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { FONTS } from "../../config/theme";
import { useScale } from "../../lib/animation";
import type { Graphic } from "./types";

const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const YELLOW = "#FFE600";
const INK = "#0B0D17";

/** 0 → 1 entrance (back-eased), 1 → 0 exit over the last 0.25 s of [t, t + dur]. */
const life = (now: number, t: number, dur: number, inDur = 0.28) => {
  const enter = interpolate(now, [t, t + inDur], [0, 1], { ...clamp, easing: Easing.out(Easing.back(1.8)) });
  const exit = interpolate(now, [t + dur - 0.25, t + dur], [0, 1], { ...clamp, easing: Easing.in(Easing.cubic) });
  return { enter, exit, on: now >= t && now <= t + dur };
};

const Kinetic: React.FC<{ g: Extract<Graphic, { type: "kinetic" }>; now: number; u: number; split: boolean }> = ({ g, now, u, split }) => {
  const { height } = useVideoConfig();
  const { enter, exit } = life(now, g.t, g.dur, 0.18);
  const shake = now - g.t < 0.25 ? Math.sin((now - g.t) * 90) * 10 * u * (1 - (now - g.t) / 0.25) : 0;
  // Fit the longest word inside the frame (heavy caps ≈ 0.72 em per letter).
  const longest = Math.max(...g.text.split(/\s+/).map((w) => w.length));
  const size = Math.min(250, 1650 / (0.72 * Math.max(1, longest)));
  return (
    // Slams sit where the captions are (captions hide meanwhile): lower third in close-ups, on the divider in split shots.
    <div style={{ position: "absolute", top: split ? height * 0.39 : height * 0.58, left: 0, right: 0, display: "flex", justifyContent: "center", opacity: 1 - exit, translate: `${shake}px 0` }}>
      <div
        style={{
          fontFamily: FONTS.caption,
          fontWeight: 900,
          fontSize: size * u,
          lineHeight: 0.95,
          textAlign: "center",
          textTransform: "uppercase",
          color: YELLOW,
          WebkitTextStroke: `${18 * u}px ${INK}`,
          paintOrder: "stroke fill",
          scale: interpolate(enter, [0, 1], [2.2, 1]),
          rotate: "-4deg",
          maxWidth: 1700 * u,
          textShadow: `0 ${14 * u}px 0 ${INK}`,
        }}
      >
        {g.text}
      </div>
    </div>
  );
};

const Stat: React.FC<{ g: Extract<Graphic, { type: "stat" }>; now: number; u: number }> = ({ g, now, u }) => {
  const { enter, exit } = life(now, g.t, g.dur);
  const count = interpolate(now, [g.t, g.t + Math.min(1, g.dur * 0.5)], [0, g.value], { ...clamp, easing: Easing.out(Easing.cubic) });
  const shown = Number.isInteger(g.value) ? Math.round(count).toLocaleString("en-US") : count.toFixed(1);
  return (
    <div style={{ position: "absolute", top: 280 * u, left: 0, right: 0, display: "flex", justifyContent: "center", opacity: 1 - exit }}>
      <div
        style={{
          background: YELLOW,
          border: `${8 * u}px solid ${INK}`,
          borderRadius: 40 * u,
          boxShadow: `${16 * u}px ${16 * u}px 0 ${INK}`,
          padding: `${24 * u}px ${70 * u}px`,
          textAlign: "center",
          scale: enter,
          rotate: "-2deg",
        }}
      >
        <div style={{ fontFamily: FONTS.caption, fontWeight: 900, fontSize: 320 * u, lineHeight: 1, color: INK }}>
          {g.prefix ?? ""}
          {shown}
          {g.suffix ?? ""}
        </div>
        <div style={{ fontFamily: FONTS.caption, fontWeight: 800, fontSize: 90 * u, color: INK, textTransform: "uppercase", letterSpacing: 2 * u }}>{g.label}</div>
      </div>
    </div>
  );
};

const Emoji: React.FC<{ g: Extract<Graphic, { type: "emoji" }>; now: number; u: number }> = ({ g, now, u }) => {
  const { height } = useVideoConfig();
  const { exit } = life(now, g.t, g.dur);
  // Six copies float up from the sides with staggered starts and sway.
  const spots = [0.12, 0.85, 0.22, 0.75, 0.08, 0.9];
  return (
    <>
      {spots.map((x, i) => {
        const t0 = g.t + i * 0.09;
        const p = interpolate(now, [t0, t0 + g.dur], [0, 1], clamp);
        const pop = interpolate(now, [t0, t0 + 0.2], [0, 1], { ...clamp, easing: Easing.out(Easing.back(2.5)) });
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: `${x * 100}%`,
              top: interpolate(p, [0, 1], [0.66, 0.22]) * height,
              fontSize: (i % 2 ? 150 : 200) * u,
              translate: `-50% 0`,
              rotate: `${Math.sin((now + i) * 4) * 14}deg`,
              scale: pop,
              opacity: (1 - exit) * interpolate(p, [0.7, 1], [1, 0], clamp),
            }}
          >
            {g.emoji}
          </div>
        );
      })}
    </>
  );
};

const Callout: React.FC<{ g: Extract<Graphic, { type: "callout" }>; now: number; u: number }> = ({ g, now, u }) => {
  const { enter, exit } = life(now, g.t, g.dur);
  return (
    <div style={{ position: "absolute", top: 330 * u, left: 0, right: 0, display: "flex", justifyContent: "center", opacity: 1 - exit }}>
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 24 * u,
          background: "#FFFFFF",
          color: INK,
          border: `${7 * u}px solid ${INK}`,
          borderRadius: 999,
          padding: `${30 * u}px ${70 * u}px`,
          boxShadow: `${12 * u}px ${12 * u}px 0 ${YELLOW}`,
          translate: `0 ${interpolate(enter, [0, 1], [-160, 0]) * u}px`,
          scale: interpolate(enter, [0, 1], [0.6, 1]),
        }}
      >
        {g.icon ? <span style={{ fontSize: 140 * u }}>{g.icon}</span> : null}
        <span style={{ fontFamily: FONTS.caption, fontWeight: 900, fontSize: 125 * u, textTransform: "uppercase" }}>{g.text}</span>
      </div>
    </div>
  );
};

const Quote: React.FC<{ g: Extract<Graphic, { type: "quote" }>; now: number; u: number }> = ({ g, now, u }) => {
  const { enter, exit } = life(now, g.t, g.dur, 0.35);
  const words = g.text.split(" ");
  return (
    <div style={{ position: "absolute", top: 230 * u, left: 70 * u, right: 70 * u, display: "flex", justifyContent: "center", opacity: 1 - exit }}>
      <div
        style={{
          background: "rgba(11,13,23,0.88)",
          borderLeft: `${16 * u}px solid ${YELLOW}`,
          borderRadius: 24 * u,
          padding: `${36 * u}px ${54 * u}px`,
          translate: `${interpolate(enter, [0, 1], [-300, 0]) * u}px 0`,
          opacity: enter,
        }}
      >
        <div style={{ fontFamily: FONTS.caption, fontWeight: 800, fontSize: 118 * u, lineHeight: 1.15, color: "#fff" }}>
          <span style={{ color: YELLOW }}>“</span>
          {words.map((w, i) => {
            const at = g.t + 0.2 + i * 0.06;
            return (
              <span key={i} style={{ opacity: interpolate(now, [at, at + 0.15], [0, 1], clamp) }}>
                {w}{" "}
              </span>
            );
          })}
          <span style={{ color: YELLOW }}>”</span>
        </div>
      </div>
    </div>
  );
};

export const Graphics: React.FC<{ graphics: Graphic[]; split: boolean; qa?: boolean }> = ({ graphics, split, qa }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const u = useScale();
  const now = frame / fps;
  return (
    <div style={{ position: "absolute", inset: 0, outline: qa ? "6px solid #00FFFF" : undefined }}>
      {graphics.map((g, i) => {
        if (now < g.t || now > g.t + g.dur) return null;
        if (g.type === "kinetic") return <Kinetic key={i} g={g} now={now} u={u} split={split} />;
        if (g.type === "stat") return <Stat key={i} g={g} now={now} u={u} />;
        if (g.type === "emoji") return <Emoji key={i} g={g} now={now} u={u} />;
        if (g.type === "callout") return <Callout key={i} g={g} now={now} u={u} />;
        return <Quote key={i} g={g} now={now} u={u} />;
      })}
    </div>
  );
};
