/**
 * Central video settings. Change values here instead of inside components.
 *
 * - Resolution: every component scales from the 1920-wide reference
 *   (see `useScale()` in src/lib/animation.ts), so other sizes such as
 *   1080x1920 or 3840x2160 keep the same proportions.
 * - Frame rate: animations are written in seconds (`sec(…)`), so changing fps
 *   keeps the same real-time timing.
 * - Duration: set each scene's length in seconds below. The total is
 *   computed automatically, accounting for transition overlaps.
 */

export const VIDEO = {
  width: 1920,
  height: 1080,
  fps: 30,
} as const;

/** Reference width that sizes in components are designed against. */
export const DESIGN_WIDTH = 1920;

/** Scene lengths for the SampleIntro composition, in seconds. */
export const SAMPLE_INTRO_TIMING = {
  title: 3.5,
  shapes: 3.5,
  outro: 3,
  /** Length of each transition between scenes, in seconds. */
  transitionLength: 0.6,
} as const;

export const secondsToFrames = (seconds: number, fps: number = VIDEO.fps) =>
  Math.round(seconds * fps);
