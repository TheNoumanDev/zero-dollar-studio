import React from "react";
import { Audio } from "@remotion/media";
import { AbsoluteFill, interpolate, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { FONTS } from "../../config/theme";
import { EASE_IN_OUT, mix, progress, springIn } from "../../lib/animation";
import { Captions } from "./Captions";
import { blinkAt, Broccoli, Carrot, Tomato } from "./Characters";
import { activeLine, mouthOpen, msToFrame, SpeakerId, timeline } from "./data";

export const fridgeDramaDuration = timeline.durationInFrames;

/** Character x positions in a 1080-wide frame, used for gaze direction. */
const X: Record<SpeakerId, number> = { broccoli: 290, tomato: 700, carrot: 830 };
/** Layout rows (1080×1920). Captions sit at the top, clear of the platform UI; nothing below y=1520. */
const SHELF_Y = 1080;
const DRAWER_Y = 1270;

export const FridgeDrama: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps, width } = useVideoConfig();
  const u = width / 1080;
  const sec = frame / fps;

  const line = activeLine(frame, fps);
  const openFrame = msToFrame(timeline.events.fridgeOpens, fps);
  const hideFrame = msToFrame(timeline.events.hide, fps);
  const outroFrame = msToFrame(timeline.outroStartMs, fps);

  const doorLight = progress(frame - openFrame, fps, 0, 0.35);
  const shock = progress(frame - openFrame, fps, 0.1, 0.2);
  // Everyone jumps then drops out of sight, starting just after "Hide!".
  const hide = progress(frame - hideFrame, fps, 0.25, 0.45, EASE_IN_OUT);
  const hop = Math.sin(Math.min(1, progress(frame - hideFrame, fps, 0, 0.3)) * Math.PI) * 40;
  const outro = springIn(frame - outroFrame, fps, 0, 0.6);

  const charProps = (id: SpeakerId, blinkOffset: number) => {
    const speaking = line && (line.speaker === id || line.speaker === "all");
    const target = line && line.speaker !== "all" && line.speaker !== id ? X[line.speaker as SpeakerId] : null;
    return {
      mouth: mouthOpen(id, frame, fps),
      look: target === null ? Math.sin(sec * 0.7 + blinkOffset) * 0.3 : Math.sign(target - X[id]),
      blink: shock > 0.5 ? 0 : blinkAt(frame, fps, blinkOffset),
      shock,
      speaking: Boolean(speaking),
    };
  };

  const placed = (id: SpeakerId, offset: number, extraY = 0, hides = true) => {
    const p = charProps(id, offset);
    // Broccoli doesn't hide: it freezes, eyes shut, pretending to be a tree.
    const frozen = !hides && frame >= hideFrame;
    const bob = Math.sin(sec * 2.2 + offset) * 6;
    return {
      face: { mouth: p.mouth, look: frozen ? 0 : p.look, blink: frozen ? 1 : p.blink, shock: frozen ? 0 : p.shock },
      style: {
        position: "absolute" as const,
        translate: "-50% -100%",
        top: 0,
        left: 0,
        transformOrigin: "50% 100%",
        scale: p.speaking ? 1.06 + p.mouth * 0.04 : 1,
        rotate: `${frozen ? Math.sin(sec * 40) * 1.2 : p.speaking ? Math.sin(sec * 6) * 2 : 0}deg`,
        marginTop: (hides ? bob - hop + hide * 1300 + extraY : frozen ? 0 : bob) * u,
        opacity: hides ? 1 - hide : 1,
      },
    };
  };

  const broc = placed("broccoli", 0, 0, false);
  const tom = placed("tomato", 41);
  const car = placed("carrot", 77, hide * 300);

  return (
    <AbsoluteFill style={{ background: "#BFE6F7", overflow: "hidden" }}>
      {/* Fridge interior */}
      <AbsoluteFill style={{ background: "linear-gradient(180deg, #E8F7FF 0%, #BFE6F7 55%, #9FD3EC 100%)" }} />
      <AbsoluteFill style={{ background: "linear-gradient(90deg, #00000018 0%, transparent 14%, transparent 86%, #00000018 100%)" }} />

      {/* The door opens: warm light floods the back wall (behind the characters) */}
      <AbsoluteFill style={{ background: "radial-gradient(ellipse at 15% 45%, #FFF3C4 0%, #FFE08299 40%, transparent 75%)", opacity: doorLight * (1 - outro) }} />
      {/* Fridge bulb switches on with the door */}
      <div style={{ position: "absolute", top: 60 * u, left: "50%", translate: "-50% 0", width: 150 * u, height: 70 * u, borderRadius: `0 0 ${75 * u}px ${75 * u}px`, background: doorLight > 0 ? "#FFF8E1" : "#E3F2FD", border: `${4 * u}px solid #90A4AE`, boxShadow: `0 0 ${mix(doorLight, 0, 180) * u}px ${mix(doorLight, 0, 60) * u}px #FFE082` }} />

      {/* Milk carton at the back of the shelf */}
      <div style={{ position: "absolute", top: (SHELF_Y - 270) * u, left: 905 * u, width: 140 * u, height: 270 * u, background: "#fff", border: `${4 * u}px solid #1d1d1f`, borderRadius: `${12 * u}px ${12 * u}px ${6 * u}px ${6 * u}px`, display: "flex", alignItems: "center", justifyContent: "center", fontFamily: FONTS.display, fontWeight: 700, fontSize: 38 * u, color: "#1E88E5" }}>
        MILK
      </div>

      {/* Shelf: Broccoli and Tomato stand on it */}
      <div style={{ position: "absolute", top: SHELF_Y * u, left: 0, right: 0, height: 28 * u, background: "#ffffffcc", borderTop: `${3 * u}px solid #fff`, boxShadow: `0 ${12 * u}px ${30 * u}px #00000026`, zIndex: 2 }} />
      <div style={{ position: "absolute", top: SHELF_Y * u, left: X.broccoli * u, zIndex: 1 }}>
        <div style={broc.style}><Broccoli size={440 * u} {...broc.face} /></div>
      </div>
      <div style={{ position: "absolute", top: (SHELF_Y + 5) * u, left: X.tomato * u, zIndex: 1 }}>
        <div style={tom.style}><Tomato size={400 * u} {...tom.face} /></div>
      </div>

      {/* Crisper drawer: Carrot peeks out of it */}
      <div style={{ position: "absolute", top: (DRAWER_Y + 180) * u, left: X.carrot * u, zIndex: 1 }}>
        <div style={car.style}><Carrot size={270 * u} {...car.face} /></div>
      </div>
      <div style={{ position: "absolute", top: DRAWER_Y * u, left: 430 * u, width: 610 * u, height: 250 * u, background: "#ffffffaa", border: `${5 * u}px solid #ffffff`, borderRadius: 28 * u, boxShadow: `inset 0 ${8 * u}px ${20 * u}px #00000018`, zIndex: 3, display: "flex", alignItems: "flex-end", justifyContent: "center", paddingBottom: 20 * u }}>
        <div style={{ width: 180 * u, height: 24 * u, borderRadius: 12 * u, background: "#ffffffcc", border: `${3 * u}px solid #90A4AE` }} />
      </div>

      <div style={{ position: "absolute", inset: 0, zIndex: 5 }}>
        <Captions y={250 * u} u={u} />
      </div>

      {/* Outro card */}
      <AbsoluteFill style={{ zIndex: 6, background: "#1d1d1f", opacity: outro, justifyContent: "center", alignItems: "center", gap: 60 * u }}>
        <div style={{ display: "flex", alignItems: "flex-end", gap: 36 * u, translate: `0 ${mix(outro, 80, 0) * u}px` }}>
          <Broccoli size={260 * u} mouth={0} look={0.5} blink={0} shock={0} />
          <Tomato size={240 * u} mouth={0.4} look={0} blink={0} shock={0} />
          <Carrot size={170 * u} mouth={0} look={-0.5} blink={blinkAt(frame, fps, 9)} shock={0} />
        </div>
        <div style={{ fontFamily: FONTS.display, fontWeight: 700, fontSize: 96 * u, lineHeight: 1.05, color: "#fff", textAlign: "center", padding: `0 ${80 * u}px`, scale: interpolate(outro, [0, 1], [0.8, 1]) }}>
          Follow for more <span style={{ color: "#FF9800" }}>fridge drama</span>
        </div>
      </AbsoluteFill>

      <Audio src={staticFile("fridge-drama/voice.wav")} />
      <Audio src={staticFile("fridge-drama/music.wav")} volume={0.9} />
      <Audio src={staticFile("fridge-drama/sfx.wav")} volume={0.8} />
    </AbsoluteFill>
  );
};
