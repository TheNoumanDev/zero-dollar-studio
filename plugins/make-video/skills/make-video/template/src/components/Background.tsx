import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";
import { COLORS } from "../config/theme";
import { useScale } from "../lib/animation";

type Props = {
  from?: string;
  to?: string;
  /** Show a slowly drifting dot grid. */
  grid?: boolean;
};

/**
 * Full-frame gradient background with an optional drifting grid.
 */
export const Background: React.FC<Props> = ({
  from = COLORS.backgroundAlt,
  to = COLORS.background,
  grid = true,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const scale = useScale();
  const cell = 64 * scale;
  // Drift 12 design-px per second, independent of fps.
  const drift = ((frame / fps) * 12 * scale) % cell;

  return (
    <AbsoluteFill
      style={{
        background: `radial-gradient(ellipse at 50% 35%, ${from} 0%, ${to} 70%)`,
      }}
    >
      {grid ? (
        <AbsoluteFill
          style={{
            backgroundImage: `radial-gradient(${COLORS.textMuted}33 ${1.5 * scale}px, transparent 0)`,
            backgroundSize: `${cell}px ${cell}px`,
            backgroundPosition: `${drift}px ${drift}px`,
            maskImage: "radial-gradient(ellipse at center, black 30%, transparent 75%)",
          }}
        />
      ) : null}
    </AbsoluteFill>
  );
};
