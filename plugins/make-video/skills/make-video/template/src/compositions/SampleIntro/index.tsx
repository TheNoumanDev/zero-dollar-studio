import React from "react";
import { Audio } from "@remotion/media";
import { linearTiming, TransitionSeries } from "@remotion/transitions";
import { fade } from "@remotion/transitions/fade";
import { slide } from "@remotion/transitions/slide";
import { interpolate, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { SAMPLE_INTRO_TIMING as T } from "../../config/video";
import { sec } from "../../lib/animation";
import { FeaturesScene } from "./scenes/FeaturesScene";
import { OutroScene } from "./scenes/OutroScene";
import { TitleScene } from "./scenes/TitleScene";

export type SampleIntroProps = {
  title: string;
  subtitle: string;
  tagline: string;
};

/** Total length in frames: scene lengths minus the overlap of each transition. */
export const getSampleIntroDuration = (fps: number) =>
  sec(T.title, fps) + sec(T.shapes, fps) + sec(T.outro, fps) - 2 * sec(T.transitionLength, fps);

export const SampleIntro: React.FC<SampleIntroProps> = ({ title, subtitle, tagline }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const transitionTiming = linearTiming({ durationInFrames: sec(T.transitionLength, fps) });

  // Fade the music in over 1s and out over the last 1.5s.
  const musicVolume = interpolate(
    frame,
    [0, fps, durationInFrames - 1.5 * fps, durationInFrames - 1],
    [0, 0.8, 0.8, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );

  return (
    <>
      <TransitionSeries>
        <TransitionSeries.Sequence durationInFrames={sec(T.title, fps)} premountFor={fps}>
          <TitleScene title={title} subtitle={subtitle} />
        </TransitionSeries.Sequence>
        <TransitionSeries.Transition presentation={fade()} timing={transitionTiming} />
        <TransitionSeries.Sequence durationInFrames={sec(T.shapes, fps)} premountFor={fps}>
          <FeaturesScene />
        </TransitionSeries.Sequence>
        <TransitionSeries.Transition
          presentation={slide({ direction: "from-right" })}
          timing={transitionTiming}
        />
        <TransitionSeries.Sequence durationInFrames={sec(T.outro, fps)} premountFor={fps}>
          <OutroScene tagline={tagline} />
        </TransitionSeries.Sequence>
      </TransitionSeries>
      <Audio src={staticFile("audio/ambient.mp3")} volume={musicVolume} />
    </>
  );
};
