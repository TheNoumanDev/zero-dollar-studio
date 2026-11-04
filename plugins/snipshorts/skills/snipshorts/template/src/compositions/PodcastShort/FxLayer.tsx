import React from "react";
import { useVideoConfig } from "remotion";
import { DrawOn, Particles } from "../../components/Fx";
import type { FxBeat } from "./types";

/**
 * The plan's accent effects, placed on the captions (which move to stay off the face):
 * particles burst from behind the caption, marks are drawn around or next to it.
 */
export const FxLayer: React.FC<{ fx: FxBeat[]; y: number; qa?: boolean }> = ({ fx, y }) => {
  const { width } = useVideoConfig();
  const s = width / 1080;
  const cx = width / 2;
  const cy = y + 90 * s;
  return (
    <>
      {fx.map((f, i) => {
        const key = `${f.kind}-${f.t}-${i}`;
        switch (f.kind) {
          case "underline":
            return <DrawOn key={key} kind="underline" start={f.t} x={150 * s} y={y + 125 * s} w={width - 300 * s} h={60 * s} color={f.color} stroke={12 * s} />;
          case "circle":
            return <DrawOn key={key} kind="circle" start={f.t} x={80 * s} y={y - 50 * s} w={width - 160 * s} h={290 * s} color={f.color} stroke={11 * s} />;
          case "arrow":
            return <DrawOn key={key} kind="arrow" start={f.t} x={40 * s} y={y + 150 * s} w={190 * s} h={190 * s} color={f.color} stroke={12 * s} />;
          case "check":
            return <DrawOn key={key} kind="check" start={f.t} x={width - 230 * s} y={y - 150 * s} w={170 * s} h={150 * s} color={f.color ?? "#3DFF8C"} stroke={16 * s} />;
          default:
            return <Particles key={key} kind={f.kind} start={f.t} x={cx} y={cy} color={f.color} scale={s} seed={`${i}`} />;
        }
      })}
    </>
  );
};
