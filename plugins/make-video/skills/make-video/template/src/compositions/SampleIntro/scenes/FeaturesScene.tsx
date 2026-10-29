import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";
import { AnimatedText, Background } from "../../../components";
import { COLORS, FONTS } from "../../../config/theme";
import { mix, springIn, stagger, useScale } from "../../../lib/animation";

const FEATURES = [
  { label: "Typography", color: COLORS.primary, shape: "50%" },
  { label: "Shapes", color: COLORS.secondary, shape: "22%" },
  { label: "Transitions", color: COLORS.accent, shape: "50% 50% 12% 50%" },
];

export const FeaturesScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const scale = useScale();

  return (
    <AbsoluteFill>
      <Background from="#1A1240" />
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", gap: 90 * scale }}>
        <AnimatedText text="Built frame by frame" size={96} delay={0.1} />
        <div style={{ display: "flex", gap: 80 * scale }}>
          {FEATURES.map((f, i) => {
            const t = springIn(frame, fps, stagger(i, 0.5, 0.18));
            const seconds = frame / fps;
            return (
              <div
                key={f.label}
                style={{
                  width: 360 * scale,
                  height: 380 * scale,
                  borderRadius: 36 * scale,
                  background: `${COLORS.backgroundAlt}CC`,
                  border: `${2 * scale}px solid ${f.color}55`,
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                  justifyContent: "center",
                  gap: 44 * scale,
                  opacity: t,
                  scale: mix(t, 0.85, 1),
                  translate: `0 ${mix(t, 80, 0) * scale}px`,
                }}
              >
                <div
                  style={{
                    width: 140 * scale,
                    height: 140 * scale,
                    borderRadius: f.shape,
                    background: f.color,
                    boxShadow: `0 0 ${60 * scale}px ${f.color}88`,
                    rotate: `${Math.sin(seconds * 2 + i) * 12}deg`,
                  }}
                />
                <div
                  style={{
                    fontFamily: FONTS.body,
                    fontWeight: 600,
                    fontSize: 40 * scale,
                    color: COLORS.text,
                  }}
                >
                  {f.label}
                </div>
              </div>
            );
          })}
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
