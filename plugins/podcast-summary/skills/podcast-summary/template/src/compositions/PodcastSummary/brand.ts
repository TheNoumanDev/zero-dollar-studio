import type React from "react";
import { loadFont as loadMono } from "@remotion/google-fonts/JetBrainsMono";

// The summary's colours and its mono label font. Change them here to restyle every piece at once.
const { fontFamily: MONO } = loadMono("normal", { weights: ["500", "800"], subsets: ["latin"] });

export const UI = {
  ink: "#0E1525",
  text: "#E6EDF7",
  purple: "#C792EA",
  mint: "#7FD1B9",
  orange: "#F78C6C",
  yellow: "#FFE14D",
  green: "#3DDC84",
  red: "#FF4D6A",
} as const;

export const mono = (size: number, color: string, extra: React.CSSProperties = {}): React.CSSProperties => ({
  fontFamily: MONO,
  fontWeight: 800,
  fontSize: size,
  color,
  fontVariantLigatures: "none",
  ...extra,
});
