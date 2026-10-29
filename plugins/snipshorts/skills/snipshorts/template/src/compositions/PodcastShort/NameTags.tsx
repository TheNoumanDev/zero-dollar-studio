import React, { useMemo } from "react";
import { Easing, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { FONTS } from "../../config/theme";
import { useScale } from "../../lib/animation";
import type { Clip } from "./types";

const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const SHOW = 2.6;

type Tag = { key: string; t: number; end: number; y: number };

/** Each person's name + role slides in at the left edge the first time they are on screen (after any cold open). */
export const NameTags: React.FC<{ clip: Clip; busy: [number, number][] }> = ({ clip, busy }) => {
  const frame = useCurrentFrame();
  const { fps, height } = useVideoConfig();
  const u = useScale();
  const t = frame / fps;

  const tags = useMemo(() => {
    const seen = new Set<string>();
    const out: Tag[] = [];
    // After the rewind label (on screen until teaserEnd + 1.6 s).
    const storyStart = clip.teaserEnd ? clip.teaserEnd + 1.7 : 0.3;
    for (const sh of clip.shots ?? []) {
      let start = Math.max(sh.start, storyStart);
      // Never under a kinetic slam: wait for it to finish.
      for (const [a, b] of busy) if (start < b + 0.2 && start + SHOW > a) start = b + 0.2;
      if (sh.end - start < 1.2) continue; // too short to read a tag
      (sh.who ?? []).forEach((key, slot) => {
        if (!key || seen.has(key) || !clip.people?.[key]) return;
        seen.add(key);
        // Single: just above the captions. Split: bottom of the top panel / just under the divider.
        const y = sh.mode === "split" ? (slot === 0 ? 0.375 : 0.535) : 0.555;
        // Leave with the shot: a tag must never sit over the next person after a cut.
        out.push({ key, t: start + slot * 0.3, end: Math.min(start + slot * 0.3 + SHOW, sh.end - 0.05), y });
      });
    }
    return out;
  }, [clip, busy]);

  return (
    <>
      {tags.map(({ key, t: t0, end, y }) => {
        if (t < t0 || t > end) return null;
        const person = clip.people![key];
        const enter = interpolate(t, [t0, t0 + 0.35], [0, 1], { ...clamp, easing: Easing.out(Easing.cubic) });
        const exit = interpolate(t, [end - 0.3, end], [0, 1], { ...clamp, easing: Easing.in(Easing.cubic) });
        return (
          <div
            key={key}
            style={{
              position: "absolute",
              top: height * y,
              left: 0,
              display: "flex",
              alignItems: "stretch",
              translate: `${interpolate(enter - exit, [0, 1], [-700, 0]) * u}px 0`,
            }}
          >
            <div style={{ width: 28 * u, background: "#FFE600" }} />
            <div style={{ background: "rgba(11,13,23,0.9)", padding: `${20 * u}px ${48 * u}px ${22 * u}px ${36 * u}px`, borderRadius: `0 ${24 * u}px ${24 * u}px 0` }}>
              <div style={{ fontFamily: FONTS.caption, fontWeight: 900, fontSize: 100 * u, color: "#fff", textTransform: "uppercase", lineHeight: 1.05 }}>
                {person.name}
              </div>
              {person.role ? (
                <div style={{ fontFamily: FONTS.caption, fontWeight: 800, fontSize: 60 * u, color: "#FFE600", textTransform: "uppercase", letterSpacing: 3 * u }}>
                  {person.role}
                </div>
              ) : null}
            </div>
          </div>
        );
      })}
    </>
  );
};
