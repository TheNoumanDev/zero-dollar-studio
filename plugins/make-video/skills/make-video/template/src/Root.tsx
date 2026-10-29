import React from "react";
import { Composition, Folder } from "remotion";
import { VIDEO, secondsToFrames } from "./config/video";
import { getSampleIntroDuration, SampleIntro } from "./compositions/SampleIntro";
import { Template } from "./compositions/_Template";
import { FridgeDrama, fridgeDramaDuration } from "./compositions/FridgeDrama";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="SampleIntro"
        component={SampleIntro}
        width={VIDEO.width}
        height={VIDEO.height}
        fps={VIDEO.fps}
        durationInFrames={getSampleIntroDuration(VIDEO.fps)}
        // Keep defaultProps inline so Studio can save edits made in the props panel.
        defaultProps={{
          title: "Motion, written in code",
          subtitle: "Programmatic video with React and Remotion",
          tagline: "Now make it yours",
        }}
      />
      <Folder name="Stories">
        <Composition
          id="FridgeDrama"
          component={FridgeDrama}
          width={1080}
          height={1920}
          fps={30}
          durationInFrames={fridgeDramaDuration}
        />
      </Folder>
      <Folder name="Templates">
        <Composition
          id="Template"
          component={Template}
          width={VIDEO.width}
          height={VIDEO.height}
          fps={VIDEO.fps}
          durationInFrames={secondsToFrames(4)}
          defaultProps={{ title: "New composition" }}
        />
      </Folder>
    </>
  );
};
