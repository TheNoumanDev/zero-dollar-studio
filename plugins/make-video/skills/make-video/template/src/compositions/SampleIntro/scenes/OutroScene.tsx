import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";
import { AnimatedText, Background, Shape } from "../../../components";
import { COLORS, FONTS } from "../../../config/theme";
import { fadeIn, mix, progress, useScale } from "../../../lib/animation";

export const OutroScene: React.FC<{ tagline: string }> = ({ tagline }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const scale = useScale();
  const ring = progress(frame, fps, 0, 1.2);

  return (
    <AbsoluteFill>
      <Background from="#0E2A33" />
      {/* Expanding ring behind the text */}
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
        <div
          style={{
            width: mix(ring, 100, 900) * scale,
            height: mix(ring, 100, 900) * scale,
            borderRadius: "50%",
            border: `${3 * scale}px solid ${COLORS.secondary}`,
            opacity: mix(ring, 0.9, 0.15),
          }}
        />
      </AbsoluteFill>
      <Shape kind="circle" size={40} color={COLORS.accent} x={30} y={30} delay={0.3} float={16} />
      <Shape kind="circle" size={28} color={COLORS.primary} x={72} y={68} delay={0.45} float={16} />

      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", gap: 28 * scale }}>
        <AnimatedText text={tagline} size={110} delay={0.2} />
        <div
          style={{
            fontFamily: FONTS.body,
            fontSize: 36 * scale,
            letterSpacing: "0.3em",
            textTransform: "uppercase",
            color: COLORS.secondary,
            opacity: fadeIn(frame, fps, 0.9, 0.6),
          }}
        >
          Made with Remotion
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
