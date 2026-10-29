/** public/<slug>/episode.json, written by tools/episode_data.py pack. */

export type Cue = { startMs: number; endMs: number; shape: string };

export type Framing = "auto" | "close" | "two" | "group" | "pose";
export type Transition = "cut" | "fade" | "wipe" | "iris";

/** Optional camera direction on a script line. Everything is optional and carries over sensibly. */
export type ShotDirection = {
  /** Set from the bible; lines without one stay on the previous set. */
  set?: string;
  /** auto (default) alternates two-shots and close-ups within a scene. */
  framing?: Framing;
  /** The other character in a two-shot. */
  with?: string;
  /** Everyone on this set, left to right (first line of a scene). Default: order of appearance. */
  cast?: string[];
  /** Full-body pose (public/<series>/cast/<who>/poses/<pose>.png) for framing "pose". */
  pose?: string;
  /** How this shot comes in. Default: cut within a scene, fade into a new set. */
  transitionIn?: Transition;
};

export type EpisodeLine = {
  speaker: string;
  caption: string;
  startMs: number;
  endMs: number;
  /** Loudness 0–1 per frame (tools/voice.py). */
  envelope: number[];
  /** Rhubarb mouth shapes (tools/lipsync.mjs); null without Rhubarb. */
  mouthCues: Cue[] | null;
  shot?: ShotDirection;
  /** The speaker's face for this line (an expression from the sheet), instead of lip sync. */
  expression?: string;
  /** Listeners' faces for this line, e.g. { "rosa": "shocked" }. */
  react?: Record<string, string>;
};

export type Rig = {
  width: number;
  height: number;
  mouth: { x: number; y: number; w: number; h: number };
  shapes: string[];
  expressions: string[];
};

export type CastMember = { name: string; color: string; scale: number; rig: Rig | null; poses: string[] };

export type SetDef = {
  name: string;
  description?: string;
  /** Painted background in public/<series>/, e.g. "sets/shop.png". null = a flat stand-in from the colours below. */
  image?: string | null;
  wall?: string;
  floor?: string;
  accent?: string;
};

export type EpisodeData = {
  slug: string;
  title: string;
  language: string;
  fps: number;
  width: number;
  height: number;
  durationInFrames: number;
  outroStartMs: number;
  outro: { text?: string; seconds?: number };
  events: Record<string, number>;
  series: { id: string; title: string; characters: Record<string, CastMember>; sets: Record<string, SetDef> };
  lines: EpisodeLine[];
};

/** public/<slug>/captions.json (tools/captions.mjs). */
export type Word = { text: string; startMs: number; endMs: number; speaker?: string };
