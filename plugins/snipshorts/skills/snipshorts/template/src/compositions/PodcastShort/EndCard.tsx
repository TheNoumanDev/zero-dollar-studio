import React from "react";
import { AbsoluteFill, Easing, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { FONTS } from "../../config/theme";
import { useScale } from "../../lib/animation";
import type { EndCardText } from "./types";

const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
/** Length of the optional end screen. sfx.py uses the same value. */
export const END_SECONDS = 3.5;

/**
 * Optional end screen: a title ("Follow for more") and your handle.
 * It breaks the seamless loop that Shorts reward, so leave it off for loop-first posts.
 */
export const EndCard: React.FC<{ at: number; card: EndCardText }> = ({ at, card }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  // Sized for a phone held at arm's length: 1.7× the design scale.
  const u = useScale() * 1.7;
  const t = frame / fps - at;
  if (t < -0.3) return null;
  const bg = interpolate(t, [-0.3, 0.15], [0, 1], { ...clamp, easing: Easing.out(Easing.cubic) });
  const pop = (start: number) => interpolate(t, [start, start + 0.35], [0, 1], { ...clamp, easing: Easing.out(Easing.back(1.8)) });
  const text = (size: number, color: string): React.CSSProperties => ({
    fontFamily: FONTS.caption,
    fontWeight: 900,
    fontSize: size * u,
    color,
    textTransform: "uppercase",
    lineHeight: 1.1,
  });

  return (
    <AbsoluteFill style={{ background: `rgba(11,13,23,${0.97 * bg})`, alignItems: "center", justifyContent: "center" }}>
      <div style={{ textAlign: "center", padding: `0 ${40 * u}px` }}>
        <div style={{ ...text(100, "#fff"), scale: pop(0.1) }}>{card.title}</div>
        {card.handle ? (
          <div
            style={{
              ...text(80, "#0B0D17"),
              textTransform: "none",
              display: "inline-block",
              marginTop: 40 * u,
              background: "#FFE600",
              borderRadius: 999,
              padding: `${12 * u}px ${44 * u}px`,
              scale: pop(0.35),
              translate: `0 ${Math.sin(t * 4) * 6 * u}px`,
            }}
          >
            {card.handle}
          </div>
        ) : null}
      </div>
    </AbsoluteFill>
  );
};
