import React from "react";
import { AbsoluteFill } from "remotion";
import { Look, mascotOf } from "./MascotKit";

/** Everyone in a cast side by side (mascots or photo cut-outs), to check them before a summary is built. */
export const CastPreview: React.FC<{ cast: string[]; mouth?: number; looks?: Record<string, Look> }> = ({ cast, mouth = 0, looks }) => (
  <AbsoluteFill style={{ background: "radial-gradient(circle at 50% 40%, #2a2350 0%, #0E1525 65%)" }}>
    <svg width={1920} height={1080} viewBox="0 0 1920 1080">
      {cast.map((who, i) => {
        const Body = mascotOf(who, looks?.[who]);
        if (!Body) return null;
        const x = 60 + i * ((1920 - 120 - 440) / Math.max(1, cast.length - 1));
        return (
          <g key={who} transform={`translate(${x},${280}) scale(1.1)`}>
            <Body pose={{ mouth: i % 2 ? mouth : 0, blink: false, t: 0 }} />
            <text x={200} y={-30} textAnchor="middle" fontSize={40} fontWeight={800} fill="#FFE14D" fontFamily="Montserrat, Arial">{who.toUpperCase()}</text>
          </g>
        );
      })}
    </svg>
  </AbsoluteFill>
);
