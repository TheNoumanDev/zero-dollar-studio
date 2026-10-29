import { loadFont as loadDisplay } from "@remotion/google-fonts/SpaceGrotesk";
import { loadFont as loadBody } from "@remotion/google-fonts/Inter";
import { loadFont as loadCaption } from "@remotion/google-fonts/Montserrat";

// Load fonts at module level. Remotion delays rendering until they are ready.
const display = loadDisplay("normal", {
  weights: ["500", "700"],
  subsets: ["latin"],
});
const body = loadBody("normal", {
  weights: ["400", "600"],
  subsets: ["latin"],
});

// Heavy, all-caps short-form captions (PodcastShort).
const caption = loadCaption("normal", {
  weights: ["800", "900"],
  subsets: ["latin"],
});

export const FONTS = {
  display: display.fontFamily,
  body: body.fontFamily,
  caption: caption.fontFamily,
} as const;

export const COLORS = {
  background: "#0B0D17",
  backgroundAlt: "#151933",
  text: "#F5F7FF",
  textMuted: "#9AA3C7",
  primary: "#6C5CE7",
  secondary: "#00D2D3",
  accent: "#FF7A59",
} as const;
