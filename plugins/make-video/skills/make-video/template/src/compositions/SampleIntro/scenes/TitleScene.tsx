import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";
import { AnimatedText, Background, Shape } from "../../../components";
import { COLORS, FONTS } from "../../../config/theme";
import { fadeIn, mix, progress, useScale } from "../../../lib/animation";

export const TitleScene: React.FC<{ title: string; subtitle: string }> = ({
  title,
  subtitle,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const scale = useScale();
  const bar = progress(frame, fps, 0.9, 0.8);

  return (
    <AbsoluteFill>
      <Background />
      <Shape kind="ring" size={220} color={COLORS.primary} x={14} y={24} delay={0.1} spin={12} />
      <Shape kind="circle" size={90} color={COLORS.accent} x={84} y={20} delay={0.25} />
      <Shape kind="square" size={130} color={COLORS.secondary} x={86} y={76} delay={0.4} spin={-18} />
      <Shape kind="pill" size={180} color={COLORS.primary} x={12} y={80} delay={0.55} spin={6} />

      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", gap: 36 * scale }}>
        <AnimatedText text={title} size={128} delay={0.2} style={{ maxWidth: "90%" }} />
        <div
          style={{
            width: mix(bar, 0, 280) * scale,
            height: 8 * scale,
            borderRadius: 8 * scale,
            background: `linear-gradient(90deg, ${COLORS.primary}, ${COLORS.secondary})`,
          }}
        />
        <div
          style={{
            fontFamily: FONTS.body,
            fontSize: 44 * scale,
            color: COLORS.textMuted,
            opacity: fadeIn(frame, fps, 1.1, 0.6),
            translate: `0 ${mix(fadeIn(frame, fps, 1.1, 0.6), 20, 0) * scale}px`,
          }}
        >
          {subtitle}
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
