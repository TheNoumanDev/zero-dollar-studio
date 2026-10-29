import { Easing, interpolate, useVideoConfig } from "remotion";
import { DESIGN_WIDTH } from "../config/video";

/**
 * Reusable animation helpers. Every helper takes `frame` and `fps` and
 * measures time in seconds, so timing stays the same at any frame rate.
 */

const clamp = {
  extrapolateLeft: "clamp",
  extrapolateRight: "clamp",
} as const;

/** Smooth ease-out without bounce. Good default for UI-style motion. */
export const EASE_OUT = Easing.bezier(0.16, 1, 0.3, 1);
/** Symmetric ease for movements that start and end at rest. */
export const EASE_IN_OUT = Easing.bezier(0.65, 0, 0.35, 1);

/** Converts seconds to frames at the current fps. */
export const sec = (seconds: number, fps: number) => Math.round(seconds * fps);

/**
 * Progress from 0 to 1 between `start` and `start + duration` (seconds),
 * clamped at both ends.
 */
export const progress = (
  frame: number,
  fps: number,
  start: number,
  duration: number,
  easing: (t: number) => number = EASE_OUT,
) =>
  interpolate(frame, [sec(start, fps), sec(start + duration, fps)], [0, 1], {
    ...clamp,
    easing,
  });

/** Fades from 0 to 1. */
export const fadeIn = (frame: number, fps: number, start = 0, duration = 0.5) =>
  progress(frame, fps, start, duration);

/** Fades from 1 to 0, ending at `end` seconds. */
export const fadeOut = (frame: number, fps: number, end: number, duration = 0.5) =>
  1 - progress(frame, fps, end - duration, duration, EASE_IN_OUT);

/** Spring-like overshoot-free pop from 0 to 1. */
export const springIn = (frame: number, fps: number, start = 0, duration = 0.8) =>
  progress(frame, fps, start, duration, Easing.spring({ damping: 14 }));

/** Maps a 0–1 progress value to an output range. */
export const mix = (t: number, from: number, to: number) => from + (to - from) * t;

/** Start time in seconds for the item at `index` in a stagger. */
export const stagger = (index: number, start = 0, gap = 0.06) => start + index * gap;

/**
 * Scale factor from the 1920-wide design reference to the current
 * composition width. Multiply pixel sizes by it so layouts work at any resolution.
 */
export const useScale = () => {
  const { width, height } = useVideoConfig();
  // Use the shorter side for portrait formats so text does not overflow.
  return Math.min(width, height * (16 / 9)) / DESIGN_WIDTH;
};
