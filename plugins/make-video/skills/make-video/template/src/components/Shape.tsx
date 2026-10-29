import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { COLORS } from "../config/theme";
import { mix, springIn, useScale } from "../lib/animation";

type Props = {
  kind: "circle" | "ring" | "square" | "pill";
  /** Size in px at the 1920-wide design reference. */
  size: number;
  color?: string;
  /** Position as a percentage of the frame (0–100). */
  x: number;
  y: number;
  /** Seconds before the shape pops in. */
  delay?: number;
  /** Degrees of rotation per second. */
  spin?: number;
  /** Floating amplitude in design px. 0 disables floating. */
  float?: number;
};

/**
 * A simple geometric shape that pops in, then floats and spins.
 */
export const Shape: React.FC<Props> = ({
  kind,
  size,
  color = COLORS.primary,
  x,
  y,
  delay = 0,
  spin = 0,
  float = 10,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const scale = useScale();
  const t = springIn(frame, fps, delay);
  const seconds = frame / fps;
  const px = size * scale;

  const shapeStyle: React.CSSProperties =
    kind === "ring"
      ? { borderRadius: "50%", border: `${Math.max(2, px * 0.08)}px solid ${color}` }
      : kind === "circle"
        ? { borderRadius: "50%", background: color }
        : kind === "pill"
          ? { borderRadius: px, background: color, height: px * 0.4 }
          : { borderRadius: px * 0.18, background: color };

  return (
    <div
      style={{
        position: "absolute",
        left: `${x}%`,
        top: `${y}%`,
        width: px,
        height: px,
        // Center on (x, y), then float on a sine wave.
        translate: `-50% calc(-50% + ${Math.sin(seconds * 1.6 + delay * 3) * float * scale}px)`,
        scale: mix(t, 0, 1),
        rotate: `${seconds * spin + mix(t, -45, 0)}deg`,
        opacity: t,
        ...shapeStyle,
      }}
    />
  );
};
