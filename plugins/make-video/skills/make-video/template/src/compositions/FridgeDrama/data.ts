import script from "../../../stories/fridge-drama/script.json";
import timeline from "../../../stories/fridge-drama/timeline.json";

/** Story data produced by tools/voice.py and tools/captions.mjs. */
export { script, timeline };

export type SpeakerId = "broccoli" | "tomato" | "carrot";
export type Line = (typeof timeline.lines)[number];

export const msToFrame = (ms: number, fps: number) => Math.round((ms / 1000) * fps);

/** The line being spoken at `frame`, if any. */
export const activeLine = (frame: number, fps: number): Line | undefined =>
  timeline.lines.find(
    (l) => frame >= msToFrame(l.startMs, fps) && frame < msToFrame(l.endMs, fps),
  );

/** Mouth openness 0..1 for a character at `frame`. */
export const mouthOpen = (id: SpeakerId, frame: number, fps: number) => {
  const line = activeLine(frame, fps);
  if (!line || (line.speaker !== id && line.speaker !== "all")) return 0;
  return line.envelope[frame - msToFrame(line.startMs, fps)] ?? 0;
};
