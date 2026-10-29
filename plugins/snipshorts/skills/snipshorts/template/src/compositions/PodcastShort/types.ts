// Data for one podcast Short. clip.json comes from tools/podcast/prepare.py,
// plan.json from tools/podcast/plan.py (Claude's edit decisions).

export type Word = { w: string; s: number; e: number };

export type Face = { cx: number; cy: number; fh: number };

/** "split" shots show two people stacked: a = left person (top), b = right person (bottom). */
export type CropKey = { t: number; shot: number; cx: number; cy: number; fh: number; mode?: "single" | "split"; a?: Face; b?: Face };

export type Clip = {
  id: string;
  fps: number;
  width: number;
  height: number;
  duration: number;
  jumpCuts: number[];
  /** Where spliced segments meet (edited time); a bigger transition than a jump cut. */
  splices?: number[];
  words: Word[];
  crop: CropKey[];
  /** Cold open: the teaser plays from 0 to teaserEnd, then a rewind into the story. */
  teaserEnd?: number | null;
  moment?: { teaser?: { label?: string } };
  /** Per shot: who is on screen (single: [who]; split: [top, bottom]). From tools/podcast/people.py. */
  shots?: Shot[];
  people?: Record<string, { name: string; role: string }>;
  /** Optional branding, copied from source.json by prepare.py. */
  watermark?: string;
  endCard?: EndCardText | null;
};

/** End screen text, e.g. { title: "Follow for more", handle: "@yourchannel" }. */
export type EndCardText = { title: string; handle?: string };

export type Shot = { shot: number; mode: "single" | "split"; start: number; end: number; who?: (string | null)[] };

export type Zoom = { t: number; dur: number; to: number; kind: "punch" | "push" };

export type Graphic =
  | { type: "kinetic"; t: number; dur: number; text: string }
  | { type: "stat"; t: number; dur: number; value: number; prefix?: string; suffix?: string; label: string }
  | { type: "emoji"; t: number; dur: number; emoji: string }
  | { type: "callout"; t: number; dur: number; text: string; icon?: string }
  | { type: "quote"; t: number; dur: number; text: string };

export type Plan = {
  hook: string;
  /** Indices into clip.words that get the highlight colour and a bump. */
  emphasis: number[];
  zooms: Zoom[];
  graphics: Graphic[];
};

export type PodcastShortProps = {
  clipId: string;
  clip?: Clip;
  plan?: Plan;
  /** Watermark text (top-left). Overrides the clip's; empty or unset means no watermark. */
  watermark?: string;
  /** End screen after the clip. Overrides the clip's; unset means no end screen. */
  endCard?: EndCardText | null;
  /** Outlines captions and graphics for layout QA. */
  qa?: boolean;
};
