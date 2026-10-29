import { Easing, interpolate } from "remotion";
import type { Clip, CropKey, Face, Zoom } from "./types";

const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

/** Crop key interpolated at time t; holds across shot changes so cuts stay hard. */
export const cropAt = (crop: CropKey[], t: number): CropKey => {
  if (crop.length === 0) return { t, shot: 0, cx: 0, cy: 0, fh: 0 };
  const i = crop.findIndex((k) => k.t > t);
  if (i === -1) return crop[crop.length - 1];
  if (i === 0) return crop[0];
  const a = crop[i - 1];
  const b = crop[i];
  if (a.shot !== b.shot) return a;
  const f = (t - a.t) / (b.t - a.t);
  return { ...a, t, cx: a.cx + (b.cx - a.cx) * f, cy: a.cy + (b.cy - a.cy) * f, fh: a.fh + (b.fh - a.fh) * f };
};

/** Zoom multiplier from the plan: punches snap in and ease out, pushes drift in slowly. */
export const zoomAt = (zooms: Zoom[], t: number) => {
  let z = 1;
  for (const zm of zooms) {
    if (t < zm.t || t > zm.t + zm.dur + 0.4) continue;
    if (zm.kind === "punch") {
      const inT = interpolate(t, [zm.t, zm.t + 0.12], [0, 1], { ...clamp, easing: Easing.out(Easing.cubic) });
      const outT = interpolate(t, [zm.t + zm.dur, zm.t + zm.dur + 0.4], [0, 1], { ...clamp, easing: Easing.inOut(Easing.cubic) });
      z = Math.max(z, 1 + (zm.to - 1) * inT * (1 - outT));
    } else {
      const inT = interpolate(t, [zm.t, zm.t + zm.dur], [0, 1], { ...clamp, easing: Easing.inOut(Easing.sin) });
      const outT = interpolate(t, [zm.t + zm.dur, zm.t + zm.dur + 0.4], [0, 1], { ...clamp, easing: Easing.inOut(Easing.cubic) });
      z = Math.max(z, 1 + (zm.to - 1) * inT * (1 - outT));
    }
  }
  return z;
};

/** Alternate framing at every jump cut (1.0 / 1.12) so cuts read as edits, not glitches. */
export const jumpZoomAt = (cuts: number[], t: number) => {
  const n = cuts.filter((c) => c <= t).length;
  return n % 2 === 1 ? 1.12 : 1;
};

/**
 * Where to draw the full source frame so the crop centre lands in the 9:16 frame.
 * Returns the source's displayed size and offset in output px.
 */
export const frameSource = (clip: Clip, outW: number, outH: number, t: number, zoom: number) => {
  const k = cropAt(clip.crop, t);
  const s = (outH / clip.height) * zoom;
  const w = clip.width * s;
  const h = clip.height * s;
  // Aim slightly below the face centre so headroom looks natural, more so when zoomed in.
  const fy = k.cy + k.fh * 0.35 * Math.min(1, zoom - 1);
  const left = Math.min(0, Math.max(outW - w, outW / 2 - k.cx * s));
  const top = Math.min(0, Math.max(outH - h, outH * 0.42 - fy * s));
  return { left, top, w, h };
};

/**
 * One panel of a split screen: the source drawn so `face` sits at 40% height of a
 * panelW x panelH box, the face about 32% of the panel tall (times zoom).
 */
export const framePanel = (clip: Clip, face: Face, panelW: number, panelH: number, zoom: number, faceY = 0.4) => {
  const minS = Math.max(panelW / clip.width, panelH / clip.height);
  const s = Math.max(minS, ((panelH * 0.32) / face.fh) * zoom);
  const w = clip.width * s;
  const h = clip.height * s;
  const left = Math.min(0, Math.max(panelW - w, panelW / 2 - face.cx * s));
  const top = Math.min(0, Math.max(panelH - h, panelH * faceY - face.cy * s));
  return { left, top, w, h };
};
