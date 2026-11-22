// Summaries registered in Root.tsx (tools/summary/register_root.py adds the folder once; add a line per summary).
//   id:   Remotion composition id (letters, digits, "-")
//   slug: public/summary/<slug>/ (build.py writes <name> for the 16:9 cut, <name>-short for the 9:16 one)
//   wide: 1920×1080 when true, 1080×1920 when false
export const SUMMARIES: { id: string; slug: string; wide: boolean }[] = [
  // { id: "summary-my-episode", slug: "my-episode", wide: true },
  // { id: "summary-my-episode-short", slug: "my-episode-short", wide: false },
];

// Thumbnails (16:9 stills, 1280×720): DuoThumb (host + guest) or ProThumb (one face). Props as in each file.
export const THUMBS: ({ id: string; kind: "duo"; props: import("./DuoThumb").DuoThumbProps } | { id: string; kind: "pro"; props: import("./ProThumb").ProThumbProps })[] = [
  // { id: "summarythumb-my-episode", kind: "duo", props: { clip: "my-episode", left: { file: "host.png", h: 760 }, right: { file: "guest.png", h: 760, flip: true }, lines: ["The *one* habit", "that changed", "everything"], boxLine: 2 } },
];
