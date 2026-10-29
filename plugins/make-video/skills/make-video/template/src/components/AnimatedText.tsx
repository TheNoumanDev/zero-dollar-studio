import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { FONTS, COLORS } from "../config/theme";
import { mix, progress, stagger, useScale } from "../lib/animation";

type Props = {
  text: string;
  /** Font size in px at the 1920-wide design reference. */
  size?: number;
  /** Seconds after the parent sequence starts before the first word appears. */
  delay?: number;
  /** Seconds between each word. */
  wordGap?: number;
  color?: string;
  weight?: number;
  fontFamily?: string;
  style?: React.CSSProperties;
};

/**
 * Reveals text word by word, with each word sliding up out of a mask.
 */
export const AnimatedText: React.FC<Props> = ({
  text,
  size = 120,
  delay = 0,
  wordGap = 0.08,
  color = COLORS.text,
  weight = 700,
  fontFamily = FONTS.display,
  style,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const scale = useScale();
  const words = text.split(" ");

  return (
    <div
      style={{
        display: "flex",
        flexWrap: "wrap",
        justifyContent: "center",
        columnGap: size * 0.28 * scale,
        fontFamily,
        fontSize: size * scale,
        fontWeight: weight,
        lineHeight: 1.05,
        letterSpacing: "-0.02em",
        color,
        ...style,
      }}
    >
      {words.map((word, i) => {
        const t = progress(frame, fps, stagger(i, delay, wordGap), 0.7);
        return (
          // The wrapper clips the word so it appears to rise out of a line.
          <span key={i} style={{ display: "inline-block", overflow: "hidden", paddingBottom: "0.08em" }}>
            <span
              style={{
                display: "inline-block",
                translate: `0 ${mix(t, 110, 0)}%`,
                opacity: t,
              }}
            >
              {word}
            </span>
          </span>
        );
      })}
    </div>
  );
};
