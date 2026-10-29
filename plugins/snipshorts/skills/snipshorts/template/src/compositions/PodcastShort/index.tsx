import React from "react";
import { Audio } from "@remotion/media";
import {
  AbsoluteFill,
  CalculateMetadataFunction,
  Easing,
  interpolate,
  OffthreadVideo,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { FONTS } from "../../config/theme";
import { useScale } from "../../lib/animation";
import { cropAt, framePanel, frameSource, jumpZoomAt, zoomAt } from "./camera";
import { Captions } from "./Captions";
import { NameTags } from "./NameTags";
import { Graphics } from "./Overlays";
import { Rewind, rewindVideoStyle } from "./Rewind";
import { EndCard, END_SECONDS } from "./EndCard";
import { Watermark } from "./Watermark";
import type { Clip, Plan, PodcastShortProps } from "./types";

export type { PodcastShortProps } from "./types";

const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const base = (id: string) => `podcast-shorts/${id}`;

/** Loads clip.json + plan.json for the clip and sizes the composition to it. */
export const calculatePodcastShort: CalculateMetadataFunction<
  PodcastShortProps
> = async ({ props }) => {
  const clip: Clip = await fetch(
    staticFile(`${base(props.clipId)}/clip.json`),
  ).then((r) => r.json());
  const plan: Plan = await fetch(
    staticFile(`${base(props.clipId)}/plan.json`),
  ).then((r) => r.json());
  // The clip, plus the end screen when there is one (props override source.json's).
  const endCard = props.endCard !== undefined ? props.endCard : clip.endCard;
  return {
    durationInFrames: Math.ceil(
      (clip.duration + (endCard ? END_SECONDS : 0)) * clip.fps,
    ),
    fps: clip.fps,
    props: { ...props, clip, plan },
  };
};

const Hook: React.FC<{ text: string; u: number }> = ({ text, u }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const enter = interpolate(t, [0, 0.3], [0, 1], {
    ...clamp,
    easing: Easing.out(Easing.back(1.6)),
  });
  const exit = interpolate(t, [2.3, 2.6], [0, 1], {
    ...clamp,
    easing: Easing.in(Easing.cubic),
  });
  if (t > 2.6) return null;
  return (
    <div
      style={{
        position: "absolute",
        top: 250 * u,
        left: 0,
        right: 0,
        display: "flex",
        justifyContent: "center",
      }}
    >
      <div
        style={{
          background: "#fff",
          color: "#0B0D17",
          borderRadius: 30 * u,
          padding: `${26 * u}px ${48 * u}px`,
          maxWidth: 1650 * u,
          textAlign: "center",
          fontFamily: FONTS.caption,
          fontWeight: 900,
          fontSize: 130 * u,
          lineHeight: 1.08,
          textTransform: "uppercase",
          boxShadow: `0 ${18 * u}px ${40 * u}px rgba(0,0,0,0.45), ${12 * u}px ${12 * u}px 0 #FFE600`,
          scale: interpolate(enter, [0, 1], [0.5, 1]) * (1 - exit * 0.3),
          opacity: 1 - exit,
          rotate: "-2deg",
        }}
      >
        {text}
      </div>
    </div>
  );
};

export const PodcastShort: React.FC<PodcastShortProps> = ({
  clipId,
  clip,
  plan,
  watermark,
  endCard,
  qa,
}) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const u = useScale();
  if (!clip || !plan) return <AbsoluteFill style={{ background: "#000" }} />;
  const t = frame / fps;
  const mark = watermark ?? clip.watermark ?? "";
  const card = endCard !== undefined ? endCard : clip.endCard;

  const zoom = zoomAt(plan.zooms, t) * jumpZoomAt(clip.jumpCuts, t);
  const key = cropAt(clip.crop, t);
  const split = key.mode === "split" && key.a && key.b;
  const video = staticFile(`${base(clipId)}/source.mp4`);
  // Tiny flash on punch-ins sells the cut.
  const flash = Math.max(
    0,
    ...plan.zooms
      .filter((z) => z.kind === "punch")
      .map((z) =>
        interpolate(t, [z.t, z.t + 0.03, z.t + 0.12], [0, 0.35, 0], clamp),
      ),
    // A brighter flash where spliced segments meet.
    ...(clip.splices ?? []).map((s) =>
      interpolate(t, [s - 0.05, s, s + 0.2], [0, 0.8, 0], clamp),
    ),
  );

  return (
    <AbsoluteFill style={{ background: "#000", overflow: "hidden" }}>
      <AbsoluteFill style={rewindVideoStyle(t, clip.teaserEnd)}>
        {split
          ? [key.a!, key.b!].map((face, i) => {
              const p = framePanel(
                clip,
                face,
                width,
                height / 2,
                zoom,
                i === 0 ? 0.52 : 0.4,
              );
              return (
                <div
                  key={i}
                  style={{
                    position: "absolute",
                    left: 0,
                    top: (i * height) / 2,
                    width,
                    height: height / 2,
                    overflow: "hidden",
                  }}
                >
                  <div
                    style={{
                      position: "absolute",
                      left: p.left,
                      top: p.top,
                      width: p.w,
                      height: p.h,
                    }}
                  >
                    {/* Only the top panel carries the sound. */}
                    <OffthreadVideo
                      src={video}
                      muted={i === 1}
                      style={{ width: "100%", height: "100%" }}
                    />
                  </div>
                </div>
              );
            })
          : (() => {
              const src = frameSource(clip, width, height, t, zoom);
              return (
                <div
                  style={{
                    position: "absolute",
                    left: src.left,
                    top: src.top,
                    width: src.w,
                    height: src.h,
                  }}
                >
                  <OffthreadVideo
                    src={video}
                    style={{ width: "100%", height: "100%" }}
                  />
                </div>
              );
            })()}
      </AbsoluteFill>
      {split ? (
        <div
          style={{
            position: "absolute",
            left: 0,
            right: 0,
            top: height / 2 - 4 * u,
            height: 8 * u,
            background: "#FFE600",
          }}
        />
      ) : null}
      {/* Grade: darker top and bottom so text reads, slight vignette. */}
      <AbsoluteFill
        style={{
          background:
            "linear-gradient(180deg, rgba(0,0,0,0.45) 0%, rgba(0,0,0,0) 22%, rgba(0,0,0,0) 55%, rgba(0,0,0,0.55) 82%, rgba(0,0,0,0.25) 100%)",
        }}
      />
      <AbsoluteFill style={{ background: "#fff", opacity: flash }} />

      {t < clip.duration ? (
        <>
          <Graphics graphics={plan.graphics} split={Boolean(split)} qa={qa} />
          {/* A kinetic slam says the same words bigger, and the rewind label owns the centre: both replace the captions. */}
          {plan.graphics.some(
            (g) => g.type === "kinetic" && t >= g.t && t <= g.t + g.dur,
          ) ||
          (clip.teaserEnd != null &&
            t >= clip.teaserEnd - 0.1 &&
            t <= clip.teaserEnd + 1.6) ? null : (
            <Captions
              words={clip.words}
              emphasis={plan.emphasis}
              y={split ? height * 0.455 : height * 0.66}
              qa={qa}
            />
          )}
          <Watermark text={mark} plan={plan} until={clip.duration} />
          <NameTags
            clip={clip}
            busy={plan.graphics
              .filter((g) => g.type === "kinetic")
              .map((g) => [g.t, g.t + g.dur] as [number, number])}
          />
          <Hook text={plan.hook} u={u} />
        </>
      ) : null}
      {clip.teaserEnd ? (
        <Rewind
          at={clip.teaserEnd}
          label={clip.moment?.teaser?.label ?? "HOW IT STARTED"}
        />
      ) : null}

      {/* Progress bar along the bottom edge. */}
      {t < clip.duration ? (
        <div
          style={{
            position: "absolute",
            left: 0,
            bottom: 0,
            height: 12 * u,
            width: `${Math.min(1, t / clip.duration) * 100}%`,
            background: "#FFE600",
          }}
        />
      ) : null}
      {card ? <EndCard at={clip.duration} card={card} /> : null}

      <Audio src={staticFile(`${base(clipId)}/sfx.wav`)} volume={0.55} />
    </AbsoluteFill>
  );
};
