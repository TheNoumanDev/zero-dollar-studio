import React from "react";
import { AbsoluteFill, CalculateMetadataFunction, Easing, Img, interpolate, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { Audio } from "@remotion/media";
import { FONTS } from "../../config/theme";
import { useScale } from "../../lib/animation";
import { mono, UI } from "./brand";
import { EndScreen, InfoCard, InfoCardData } from "./Cards";
import { Host, HostConfig, HostCue } from "./Host";
import { Mic } from "./Mascots";
import { Look, mascotOf } from "./MascotKit";

// Podcast summary: the speakers' own voices in short whole-sentence clips, over an animated stand-in for each person
// (their real photo animated by an AI talking face, their real mouth shapes, or a code-drawn mascot). Your commentary
// is text only (topic titles, cards, context lines, reaction bubbles); a real still from the episode flashes at the
// start of every scene. Data: tools/summary/build.py → public/summary/<slug>/manifest.json.

type Who = string;
type CastMember = { name: string; tint: string; look?: Look };
type Scene = { id: string; start: number; end: number; still: string; cast?: Who[]; card: InfoCardData | null; react?: string; comment?: string; context?: string; topic?: string; cues: { at: number; react: string; comment: string }[] };
type Manifest = {
  slug: string; duration: number; endAt: number; title: string; subtitle: string;
  listener?: Who; cast?: Record<Who, CastMember>; stillLabel?: string; host?: HostConfig | null; handle?: string;
  /** "Meet the cast" before the first clip: each real face (public/<faces>/<who>.jpg), then its mascot + name. */
  intro?: { dur: number; cast: Who[]; at: number[]; flip?: number; faces: string } | null;
  endNote: { title: string; accent: string; items: string[] };
  scenes: Scene[]; lines: { who: Who; start: number; end: number }[]; words: { w: string; s: number; e: number; who: Who; line: number }[]; mouth: number[];
};
export type PodcastSummaryProps = { slug: string; manifest?: Manifest };

const FPS = 30;
const STILL = 1.6;
const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
// Left to right on the 16:9 stage, in script.json cast order.
const castOf = (m: Manifest) => m.cast ?? {};

export const calculatePodcastSummary: CalculateMetadataFunction<PodcastSummaryProps> = async ({ props }) => {
  const manifest: Manifest = await fetch(staticFile(`summary/${props.slug}/manifest.json`)).then((r) => r.json());
  return { durationInFrames: Math.ceil(manifest.duration * FPS), fps: FPS, props: { ...props, manifest } };
};

/** Who holds the floor at t: the current line's speaker, else the last one (so nobody snaps back in the gaps). */
const speakerAt = (m: Manifest, t: number): Who => {
  let who: Who = m.lines[0]?.who ?? "";
  for (const l of m.lines) if (l.start <= t + 0.05) who = l.who;
  return who;
};

/** Who was on screen beside `speaker` most recently (the vertical stage shows two at a time). */
const partnerAt = (m: Manifest, t: number, speaker: Who): Who | undefined => {
  let other: Who | undefined;
  for (const l of m.lines) {
    if (l.start > t + 0.05) break;
    if (l.who !== speaker) other = l.who;
  }
  return other ?? m.lines.find((l) => l.who !== speaker)?.who ?? (m.listener !== speaker ? m.listener : undefined);
};

const Stage: React.FC<{ m: Manifest }> = ({ m }) => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();
  const wide = width > height;
  const t = frame / FPS;
  const speaker = speakerAt(m, t);
  // Full-episode cuts list who's in each scene; past four people only the speaker and whoever they're talking to sit.
  const scene = [...m.scenes].reverse().find((sc) => sc.start <= t + 0.05) ?? m.scenes[0];
  const inScene = scene?.cast ?? Object.keys(castOf(m));
  const partner = partnerAt(m, t, speaker);
  const cast = inScene.length <= 4 ? inScene : inScene.filter((w) => w === speaker || w === partner);
  const talking = m.lines.some((l) => l.start <= t && t < l.end);
  const open = talking ? m.mouth[frame] ?? 0 : 0;
  // Seat positions in px (each mascot is a 400 × 560 drawing). Two people: one each side. More: an even row
  // on 16:9; on vertical only the speaker and whoever they're talking to, kept in cast order.
  const two = cast.length <= 2;
  const s = wide ? (two ? 1.25 : 0.98) : 1.15;
  const shown = wide || two ? cast : cast.filter((w) => w === speaker || w === partnerAt(m, t, speaker));
  const seat: Record<Who, [number, number]> = {};
  if (wide && two) Object.assign(seat, { [cast[0]]: [280, 300], [cast[1]]: [930, 300] });
  // 16:9 row stops short of the host cam (bottom right).
  else if (wide) cast.forEach((w, i) => (seat[w] = [50 + i * ((1500 - 50 - 400 * s) / (cast.length - 1)), 420]));
  else shown.forEach((w, i) => (seat[w] = [i === 0 ? 50 : 570, 640]));
  const deskY = wide ? 960 : 1280;
  const one = (who: Who, i: number) => {
    const on = who === speaker;
    const k = interpolate(t - (m.lines.find((l) => l.who === who && l.start <= t)?.start ?? -9), [0, 0.25], [0, 1], clamp);
    // AI faces move their own head: no cartoon talk-wobble on top (it fought the real head motion).
    const ai = !!castOf(m)[who]?.look?.photo?.ai;
    const bob = on && talking && !ai ? Math.sin(t * 9) * 4 * open : Math.sin(t * 1.6 + i) * 3;
    const tilt = on && talking && !ai ? Math.sin(t * 3.1) * 2.5 : ai ? 0 : i % 2 ? 2 : -2;
    const blink = (t + i * 1.3) % 3.7 < 0.12;
    const [x, y] = seat[who];
    const grow = on ? 1 + 0.04 * Math.min(1, k + 0.5) : 0.97;
    const Body = mascotOf(who, castOf(m)[who]?.look);
    if (!Body) return null;
    return (
      <g key={who} transform={`translate(${x + 200 * s},${y + bob + 560 * s}) scale(${s * grow}) rotate(${tilt}) translate(-200,-560)`} style={{ filter: on ? "none" : "brightness(0.72) saturate(0.85)" }}>
        <Body pose={{ mouth: on ? open : 0, blink, t }} />
      </g>
    );
  };
  const spot = seat[speaker] ?? seat[shown[0]];
  const left = seat[shown[0]];
  const right = seat[shown[shown.length - 1]];
  return (
    <AbsoluteFill>
      <AbsoluteFill style={{ background: `radial-gradient(circle at 50% 38%, #2a2350 0%, ${UI.ink} 68%)` }} />
      <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} style={{ position: "absolute" }}>
        <ellipse cx={spot[0] + 200 * s} cy={spot[1] + 260 * s} rx={300 * s} ry={330 * s} fill="#C792EA" opacity={0.16} />
        {shown.map((w) => one(w, cast.indexOf(w)))}
        <rect x={0} y={deskY} width={width} height={height - deskY} fill="#1a1f2e" />
        <rect x={0} y={deskY} width={width} height={6} fill="#C792EA" opacity={0.35} />
        {two || !wide ? (
          <>
            <Mic x={left[0] + 400 * s + 30} y={deskY - 80} />
            <Mic x={right[0] - 30} y={deskY - 80} flip />
          </>
        ) : null}
      </svg>
    </AbsoluteFill>
  );
};

/** The real frame from the episode, full screen for the first STILL seconds of a scene, then wiped away. After the
 *  first scene it wipes in over the gap before the scene (under build.py's whoosh), so scene changes never jump. */
const WIPE_IN = 0.3;
const Still: React.FC<{ m: Manifest; scene: Scene; first: boolean }> = ({ m, scene, first }) => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();
  const u = useScale();
  const t = frame / FPS - scene.start;
  if (t < (first ? 0 : -WIPE_IN) || t > STILL) return null;
  const into = first ? 1 : interpolate(t, [-WIPE_IN, 0], [0, 1], { ...clamp, easing: Easing.out(Easing.cubic) });
  const out = interpolate(t, [STILL - 0.3, STILL], [0, 1], { ...clamp, easing: Easing.in(Easing.cubic) });
  const wide = width > height;
  return (
    <AbsoluteFill style={{ clipPath: `inset(0 ${Math.max(out, 1 - into) * 100}% 0 0)` }}>
      <Img src={staticFile(`summary/${m.slug}/${scene.still}`)} style={{ width: "100%", height: "100%", objectFit: "cover", scale: `${1 + 0.05 * (Math.max(0, t) / STILL)}` }} />
      <div style={{ position: "absolute", left: (wide ? 40 : 50) * u, top: (wide ? 40 : 120) * u, ...mono((wide ? 22 : 30) * u, UI.ink, { background: "#FFE14D", padding: `${6 * u}px ${16 * u}px`, borderRadius: 10 * u }) }}>
        {m.stillLabel ?? "📸 REAL MOMENT"}
      </div>
    </AbsoluteFill>
  );
};

/** Their words, a few at a time, active word lit in the speaker's colour, name chip above. */
const Captions: React.FC<{ m: Manifest }> = ({ m }) => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();
  const wide = width > height;
  const u = useScale();
  const t = frame / FPS;
  const line = m.lines.findIndex((l) => l.start <= t && t < l.end + 0.15);
  if (line < 0) return null;
  const ws = m.words.filter((w) => w.line === line);
  // Pages of up to 6 words, breaking after sentence ends.
  const pages: (typeof ws)[] = [[]];
  for (const w of ws) {
    const p = pages[pages.length - 1];
    p.push(w);
    if (p.length >= (wide ? 7 : 5) || /[.?!]$/.test(w.w)) pages.push([]);
  }
  const page = [...pages].reverse().find((p) => p.length && p[0].s <= t + 0.05) ?? pages[0];
  const who = m.lines[line].who;
  const { name, tint } = castOf(m)[who] ?? { name: who.toUpperCase(), tint: "#FFE14D" };
  // 16:9: left of centre, clear of the host cam (bottom right).
  return (
    <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: wide ? "flex-start" : "center", paddingBottom: wide ? 28 : 420, paddingLeft: wide ? 120 : 0 }}>
      <div style={{ display: "flex", flexDirection: "column", alignItems: wide ? "center" : "center", width: wide ? 1300 : "100%" }}>
        <div style={{ ...mono(wide ? 24 * u : 30, UI.ink, { background: tint, padding: `${4 * u}px ${16 * u}px`, borderRadius: 8 * u, letterSpacing: 2 * u }) }}>{name}</div>
        <div style={{ marginTop: 10 * u, maxWidth: wide ? 1300 : 980, textAlign: "center", background: "rgba(11,13,23,0.82)", padding: `${10 * u}px ${26 * u}px`, borderRadius: 18 * u, fontFamily: FONTS.caption, fontWeight: 800, fontSize: wide ? 54 * u : 68, lineHeight: 1.18, color: "#fff" }}>
          {page.map((w, i) => (
            <span key={i} style={{ color: t >= w.s && t < w.e + 0.08 ? tint : "#fff" }}>{w.w} </span>
          ))}
        </div>
      </div>
    </AbsoluteFill>
  );
};

/** The scene's topic as a big heading in the empty space at the top (wide cut), held for the whole scene. `*word*` = yellow. */
const Topic: React.FC<{ scene: Scene }> = ({ scene }) => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();
  const u = useScale();
  if (!scene.topic || width <= height) return null;
  const t = frame / FPS - scene.start - STILL + 0.2;
  const left = scene.end - frame / FPS;
  if (t < 0 || left < 0) return null;
  const k = Math.min(interpolate(t, [0, 0.35], [0, 1], { ...clamp, easing: Easing.out(Easing.back(1.6)) }), interpolate(left, [0, 0.3], [0, 1], clamp));
  const parts = scene.topic.split(/(\*[^*]+\*)/);
  const len = scene.topic.replace(/\*/g, "").length;
  const l = scene.card ? 660 : 320;
  const size = Math.min(100, ((1600 - l) * 1.7) / (len * 0.6));
  return (
    <div style={{ position: "absolute", top: 46 * u, left: l * u, right: 320 * u, textAlign: "center", opacity: Math.min(1, k * 1.5), scale: `${0.85 + 0.15 * k}`, fontFamily: FONTS.display, fontWeight: 900, fontSize: size * u, lineHeight: 1.05, color: "#fff", textTransform: "uppercase", letterSpacing: -1 * u, textShadow: `0 ${6 * u}px ${24 * u}px rgba(0,0,0,0.7)`, WebkitTextStroke: `${8 * u}px ${UI.ink}`, paintOrder: "stroke fill" }}>
      {parts.map((p, i) => (p.startsWith("*") ? <span key={i} style={{ color: "#FFE14D" }}>{p.slice(1, -1)}</span> : <span key={i}>{p}</span>))}
    </div>
  );
};

/** Our own context, as text: a slim strip at the top for a few seconds after the still. */
const Context: React.FC<{ scene: Scene }> = ({ scene }) => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();
  const wide = width > height;
  const u = useScale();
  const t = frame / FPS - scene.start - STILL;
  if (!scene.context || t < 0 || t > 4) return null;
  const k = Math.min(interpolate(t, [0, 0.3], [0, 1], clamp), interpolate(t, [3.6, 4], [1, 0], clamp));
  return (
    <div style={{ position: "absolute", top: wide ? (scene.topic ? 250 * u : 56) : 500, left: wide ? 700 : 50, right: wide ? 300 : 50, opacity: k, translate: `0 ${(1 - k) * -20}px`, background: "rgba(11,18,32,0.9)", border: `${3 * u}px solid #FFE14D88`, borderRadius: 20 * u, padding: `${14 * u}px ${24 * u}px`, fontFamily: FONTS.display, fontWeight: 700, fontSize: wide ? 34 * u : 40, color: UI.text, lineHeight: 1.2 }}>
      <span style={{ color: "#FFE14D" }}>Context: </span>
      {scene.context}
    </div>
  );
};

const Title: React.FC<{ m: Manifest }> = ({ m }) => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();
  const wide = width > height;
  const u = useScale();
  const t = frame / FPS;
  if (t > 3.2) return null;
  const k = Math.min(interpolate(t, [0.1, 0.5], [0, 1], { ...clamp, easing: Easing.out(Easing.back(1.4)) }), interpolate(t, [2.8, 3.2], [1, 0], clamp));
  return (
    <AbsoluteFill style={{ justifyContent: wide ? "flex-start" : "flex-start", alignItems: "center", paddingTop: (wide ? 150 : 330) * u }}>
      <div style={{ opacity: k, scale: `${0.85 + 0.15 * k}`, textAlign: "center", background: "rgba(11,18,32,0.88)", padding: `${18 * u}px ${40 * u}px`, borderRadius: 26 * u, border: `${4 * u}px solid #C792EA` }}>
        <div style={{ fontFamily: FONTS.display, fontWeight: 800, fontSize: (wide ? 88 : 92) * u, color: "#fff", lineHeight: 1.05 }}>{m.title}</div>
        <div style={mono((wide ? 30 : 34) * u, "#FFE14D", { marginTop: 8 * u })}>{m.subtitle}</div>
      </div>
    </AbsoluteFill>
  );
};

/** The real face of whoever is speaking, in the free top-right corner; pops when the speaker changes. */
const SpeakerFace: React.FC<{ m: Manifest }> = ({ m }) => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();
  const wide = width > height;
  const t = frame / FPS;
  const it = m.intro;
  if (!it || t < it.dur || t > m.endAt) return null;
  // Hidden while a scene's real still is up.
  if (m.scenes.some((s) => t >= s.start - 0.05 && t < s.start + STILL)) return null;
  const who = speakerAt(m, t);
  let since = 0;
  for (let i = 0; i < m.lines.length && m.lines[i].start <= t + 0.05; i++) if (i === 0 || m.lines[i - 1].who !== m.lines[i].who) since = m.lines[i].start;
  const scene = [...m.scenes].reverse().find((s) => s.start <= t);
  const from = Math.max(since, (scene?.start ?? 0) + STILL);
  const k = interpolate(t - from, [0, 0.3], [0, 1], { ...clamp, easing: Easing.out(Easing.back(1.8)) });
  const { name, tint } = castOf(m)[who] ?? { name: who.toUpperCase(), tint: "#FFE14D" };
  const size = wide ? 210 : 250;
  return (
    <div style={{ position: "absolute", right: wide ? 56 : 40, top: wide ? 48 : 150, display: "flex", flexDirection: "column", alignItems: "center", scale: `${k}`, transformOrigin: "top right" }}>
      <div style={{ width: size, height: size, borderRadius: "50%", overflow: "hidden", border: `${wide ? 7 : 8}px solid ${tint}`, boxShadow: "0 10px 30px rgba(0,0,0,0.55)" }}>
        <Img src={staticFile(`${it.faces}/${who}.jpg`)} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
      </div>
      <div style={{ ...mono(wide ? 20 : 26, UI.ink, { background: tint, padding: "4px 14px", borderRadius: 8, letterSpacing: 2 }), marginTop: -16, whiteSpace: "nowrap" }}>{name}</div>
    </div>
  );
};

/** The opening: title on top, then one big card per person: their real photo (head and shoulders) pops in, then the
 *  card flips over to reveal their mascot saying hi, with the name chip under it and a "×" between two people. */
const Intro: React.FC<{ m: Manifest }> = ({ m }) => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();
  const wide = width > height;
  // Vertical layouts here are written in real px (like the captions); 16:9 in 1920-wide design px.
  const scale = useScale();
  const u = wide ? scale : 1;
  const t = frame / FPS;
  const it = m.intro;
  if (!it || t > it.dur) return null;
  const n = it.cast.length;
  const flip = it.flip ?? 1.1;
  const out = interpolate(t, [it.dur - 0.35, it.dur], [1, 0], clamp);
  const pop = (a: number) => interpolate(t - a, [0, 0.4], [0, 1], { ...clamp, easing: Easing.out(Easing.back(1.6)) });
  // 16:9 keeps clear of the host cam (x > 1500); vertical gives each person a big column.
  const span = wide ? 1440 : 1000;
  const col = span / n;
  const cardW = Math.min(wide ? 470 : 440, col * 0.84);
  const cardH = cardW * 1.28;
  // Cards (and their name chips) centred in the space under the title.
  const top = wide ? Math.max(200, 180 + (900 - cardH - 70) / 2) : 620;
  return (
    <AbsoluteFill style={{ opacity: out }}>
      <AbsoluteFill style={{ background: `radial-gradient(circle at 50% 45%, #2a2350 0%, ${UI.ink} 72%)` }} />
      <div style={{ position: "absolute", top: (wide ? 56 : 300) * u, left: 0, width: wide ? 1500 * u : "100%", textAlign: "center", opacity: interpolate(t, [0, 0.3], [0, 1], clamp), translate: `0 ${interpolate(t, [0, 0.4], [-20, 0], clamp) * u}px` }}>
        <div style={{ fontFamily: FONTS.display, fontWeight: 800, fontSize: (wide ? 80 : 96) * u, color: "#fff", lineHeight: 1.05 }}>{m.title}</div>
        <div style={mono((wide ? 28 : 36) * u, "#FFE14D", { marginTop: 10 * u })}>{m.subtitle}</div>
      </div>
      {n === 2 ? (
        <div style={{ position: "absolute", left: ((wide ? 30 : 40) + col) * u, top: (top + cardH * 0.42) * u, translate: "-50% 0", fontFamily: FONTS.display, fontWeight: 800, fontSize: (wide ? 90 : 110) * u, color: "#FFE14D", scale: `${pop(it.at[1] + 0.2)}`, textShadow: "0 6px 20px rgba(0,0,0,0.6)" }}>×</div>
      ) : null}
      {it.cast.map((who, i) => {
        const a = it.at[i];
        const k = pop(a);
        // 0 → 180°: the real photo turns away, the mascot side turns in.
        const turn = interpolate(t, [a + flip, a + flip + 0.45], [0, 180], { ...clamp, easing: Easing.inOut(Easing.cubic) });
        const since = t - (a + flip + 0.45);
        const cx = (wide ? 30 : 40) + col * (i + 0.5);
        const { name, tint } = castOf(m)[who] ?? { name: who.toUpperCase(), tint: "#FFE14D" };
        const Body = mascotOf(who, castOf(m)[who]?.look);
        const side: React.CSSProperties = { position: "absolute", inset: 0, borderRadius: 26 * u, overflow: "hidden", backfaceVisibility: "hidden", border: `${6 * u}px solid ${tint}`, boxShadow: `0 16px 40px rgba(0,0,0,0.55), 0 0 ${40 * u}px ${tint}55` };
        // "Hi!": the mascot talks for ~0.8 s after the flip, with a small hop.
        const talk = since > 0 && since < 0.8 ? 0.35 + 0.35 * Math.sin(since * 22) : 0;
        const hop = since > 0 ? Math.sin(Math.min(1, since / 0.35) * Math.PI) * 14 : 0;
        return (
          <div key={who} style={{ position: "absolute", left: (cx - cardW / 2) * u, top: top * u, width: cardW * u, display: "flex", flexDirection: "column", alignItems: "center", scale: `${k}`, opacity: k > 0 ? 1 : 0 }}>
            <div style={{ position: "relative", width: cardW * u, height: cardH * u, perspective: 1400 * u }}>
              <div style={{ position: "absolute", inset: 0, transformStyle: "preserve-3d", transform: `rotateY(${turn}deg)` }}>
                <div style={{ ...side, background: "#000" }}>
                  <Img src={staticFile(`${it.faces}/${who}.jpg`)} style={{ width: "100%", height: "100%", objectFit: "cover", objectPosition: "50% 30%", scale: `${1.04 - 0.04 * Math.min(1, Math.max(0, t - a) / flip)}` }} />
                  <div style={{ position: "absolute", left: 14 * u, top: 14 * u, ...mono(16 * u, UI.ink, { background: "#FFE14D", padding: `${3 * u}px ${10 * u}px`, borderRadius: 6 * u }) }}>REAL</div>
                </div>
                <div style={{ ...side, transform: "rotateY(180deg)", background: `radial-gradient(circle at 50% 38%, ${tint}66 0%, #1a1733 70%)` }}>
                  <svg width="100%" height="100%" viewBox="-10 20 420 520" preserveAspectRatio="xMidYMax meet" style={{ position: "absolute", inset: 0, translate: `0 ${-hop * u}px` }}>
                    {Body ? <Body pose={{ mouth: talk, blink: (t + i) % 3.1 < 0.12, t: -100 + t }} /> : null}
                  </svg>
                  {since > 0.05 && since < 1.1 ? (
                    <div style={{ position: "absolute", right: 14 * u, top: 16 * u, ...mono(28 * u, UI.ink, { background: "#fff", padding: `${5 * u}px ${14 * u}px`, borderRadius: 16 * u }), scale: `${interpolate(since, [0.05, 0.3], [0, 1], { ...clamp, easing: Easing.out(Easing.back(2)) })}` }}>hi! 👋</div>
                  ) : null}
                </div>
              </div>
            </div>
            <div style={{ ...mono((wide ? 26 : 32) * u, UI.ink, { background: tint, padding: `${6 * u}px ${18 * u}px`, borderRadius: 8 * u, letterSpacing: 2 * u }), marginTop: 18 * u, whiteSpace: "nowrap" }}>{name}</div>
          </div>
        );
      })}
    </AbsoluteFill>
  );
};

const hostCues = (m: Manifest): HostCue[] => {
  const cues: HostCue[] = [];
  m.scenes.forEach((s, i) => {
    const until = m.scenes[i + 1]?.start ?? m.endAt;
    cues.push({ at: s.start + STILL, until, react: s.react, comment: s.comment });
    s.cues.forEach((c) => cues.push({ at: c.at, until, react: c.react, comment: c.comment }));
  });
  return cues.sort((a, b) => a.at - b.at).map((c, i, all) => ({ ...c, until: Math.min(c.until, all[i + 1]?.at ?? c.until) }));
};

export const PodcastSummary: React.FC<PodcastSummaryProps> = ({ manifest: m }) => {
  if (!m) return null;
  return (
    <AbsoluteFill style={{ background: UI.ink }}>
      <Stage m={m} />
      {m.scenes.map((s, i) => <Still key={`s${s.id}`} m={m} scene={s} first={i === 0} />)}
      <Captions m={m} />
      {m.scenes.map((s) => (s.card ? <InfoCard key={`c${s.id}`} card={s.card} at={s.card.at ?? s.start} until={s.end} /> : null))}
      {m.scenes.map((s) => <Context key={`x${s.id}`} scene={s} />)}
      {m.scenes.map((s) => <Topic key={`t${s.id}`} scene={s} />)}
      <SpeakerFace m={m} />
      <Intro m={m} />
      <Host cues={hostCues(m)} until={m.endAt} host={m.host} />
      {m.intro ? null : <Title m={m} />}
      <EndScreen at={m.endAt} title={m.endNote.title} accent={m.endNote.accent} items={m.endNote.items} handle={m.handle} />
      <Audio src={staticFile(`summary/${m.slug}/audio.wav`)} />
    </AbsoluteFill>
  );
};
