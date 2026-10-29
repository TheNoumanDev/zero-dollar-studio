import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";
import { AnimatedText, Background } from "../../components";
import { fadeOut } from "../../lib/animation";

/**
 * Starter for new compositions. Copy this folder, rename it, then register it
 * in src/Root.tsx. See AGENTS.md → "Creating a new composition".
 */
export type TemplateProps = {
  title: string;
};

export const Template: React.FC<TemplateProps> = ({ title }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  return (
    <AbsoluteFill style={{ opacity: fadeOut(frame, fps, durationInFrames / fps) }}>
      <Background />
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
        <AnimatedText text={title} />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
