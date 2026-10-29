import type { EpisodeData, Framing, Transition } from "./types";

/** One camera setup on screen from `fromMs` to `toMs` (composition time). */
export type Shot = {
  fromMs: number;
  toMs: number;
  set: string;
  framing: Exclude<Framing, "auto">;
  /** Characters in frame, left to right. */
  members: string[];
  /** Who the camera favours (the speaker of the shot's first line). */
  focus: string;
  pose?: string;
  transitionIn: Transition;
};

/** Cut this long before the first syllable, so the new shot is settled when the line starts. */
const LEAD_MS = 120;

/**
 * The edit, derived from the script: a scene per set, a shot per line.
 * Lines can direct it with `shot` (see types.ts); everything else is automatic:
 * a scene opens on a two-shot (or a group), then alternates close-ups and two-shots,
 * so the picture changes with every line (QA's variety check wants a change every ≤ 5 s).
 */
export const buildShots = (data: EpisodeData): Shot[] => {
  const { lines, series } = data;
  const firstSet = Object.keys(series.sets)[0];
  const shots: Shot[] = [];
  let set = firstSet;
  let cast: string[] = [];
  let k = 0; // line index within the scene
  lines.forEach((line, i) => {
    const dir = line.shot ?? {};
    const newScene = i === 0 || (dir.set !== undefined && dir.set !== set);
    if (newScene) {
      set = dir.set ?? set;
      k = 0;
      // This scene's cast: given, or everyone who speaks (or is addressed) until the set changes.
      cast = dir.cast ? dir.cast.slice() : [];
      for (let j = i; j < lines.length; j++) {
        if (j > i && lines[j].shot?.set !== undefined && lines[j].shot?.set !== set) break;
        const s = lines[j].shot;
        for (const c of [lines[j].speaker, s?.with, ...Object.keys(lines[j].react ?? {})]) {
          if (c && c !== "all" && series.characters[c] && cast.indexOf(c) === -1) cast.push(c);
        }
      }
    }
    const who = line.speaker;
    const others = cast.filter((c) => c !== who);
    // The other half of a two-shot: given, else the last other speaker, else the next one.
    const prevOther = lines.slice(0, i).reverse().find((l) => l.speaker !== who && others.indexOf(l.speaker) !== -1)?.speaker;
    const partner = dir.with ?? prevOther ?? others[0];
    let framing: Shot["framing"];
    if (dir.framing && dir.framing !== "auto") framing = dir.framing;
    else if (who === "all" || (k === 0 && cast.length > 2)) framing = "group";
    else if (!partner) framing = "close";
    else framing = k % 2 === 0 ? "two" : "close";
    let members: string[];
    if (framing === "group") members = cast.slice();
    else if (framing === "two" && partner) members = cast.filter((c) => c === who || c === partner);
    else members = who === "all" ? cast.slice() : [who];
    const fromMs = i === 0 ? 0 : Math.max(line.startMs - LEAD_MS, shots[shots.length - 1].fromMs + 1);
    shots.push({
      fromMs,
      toMs: data.outroStartMs, // trimmed to the next shot below
      set,
      framing,
      members,
      focus: who,
      pose: dir.pose,
      transitionIn: dir.transitionIn ?? (newScene && i > 0 ? "fade" : "cut"),
    });
    if (shots.length > 1) shots[shots.length - 2].toMs = fromMs;
    k++;
  });
  // Merge a line into the previous shot when nothing about the camera changes.
  const merged: Shot[] = [];
  for (const s of shots) {
    const p = merged[merged.length - 1];
    if (p && s.transitionIn === "cut" && p.set === s.set && p.framing === s.framing && p.pose === s.pose && p.members.join() === s.members.join()) {
      p.toMs = s.toMs;
    } else merged.push({ ...s });
  }
  return merged;
};
