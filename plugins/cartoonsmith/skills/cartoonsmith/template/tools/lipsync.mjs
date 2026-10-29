/**
 * Phoneme-timed mouth shapes with Rhubarb Lip Sync (MIT, installed by tools/setup_cartoon.sh).
 *
 *   node tools/lipsync.mjs stories/<slug>
 *
 * Adds `mouthCues: [{ startMs, endMs, shape }]` to every line of
 * <story>/timeline.json. Shapes are Rhubarb's Preston Blair set:
 *   X rest · A closed (M B P) · B slightly open (most consonants, "ee")
 *   C open (E) · D wide open (A) · E rounded (O) · F puckered (OO, W)
 *   G teeth on lip (F V) · H tongue (L)
 * English uses Rhubarb's speech recogniser plus the script as a hint;
 * other languages use its language-independent phonetic recogniser.
 * Without Rhubarb the rig falls back to loudness (no mouthCues needed).
 */
import { execFile } from "node:child_process";
import { existsSync, mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { promisify } from "node:util";

const run = promisify(execFile);
const RHUBARB = "tools/rhubarb/rhubarb";
const storyDir = process.argv[2];
if (!storyDir) throw new Error("Usage: node tools/lipsync.mjs stories/<slug>");
if (!existsSync(RHUBARB)) {
  console.log("Rhubarb not installed (tools/setup_cartoon.sh): mouths will follow loudness only.");
  process.exit(0);
}
const tlPath = path.join(storyDir, "timeline.json");
const timeline = JSON.parse(readFileSync(tlPath, "utf8"));
const english = (timeline.language ?? "en") === "en";
const tmp = mkdtempSync(path.join(tmpdir(), "lipsync-"));
const t0 = Date.now();

const one = async (line, i) => {
  const dialog = path.join(tmp, `${i}.txt`);
  writeFileSync(dialog, line.text);
  const args = ["-f", "json", "-q", "--extendedShapes", "GHX", ...(english ? ["-d", dialog] : ["-r", "phonetic"]), line.file];
  const { stdout } = await run(RHUBARB, args, { maxBuffer: 1 << 24 });
  line.mouthCues = JSON.parse(stdout).mouthCues.map((c) => ({
    startMs: Math.round(c.start * 1000),
    endMs: Math.round(c.end * 1000),
    shape: c.value,
  }));
};

// Four at a time: a long episode has dozens of lines.
const queue = timeline.lines.map((line, i) => [line, i]);
await Promise.all(
  Array.from({ length: 4 }, async () => {
    while (queue.length) {
      const [line, i] = queue.shift();
      await one(line, i);
    }
  }),
);

writeFileSync(tlPath, JSON.stringify(timeline, null, 1));
const cues = timeline.lines.reduce((n, l) => n + l.mouthCues.length, 0);
console.log(`Lip sync: ${cues} mouth cues for ${timeline.lines.length} lines in ${((Date.now() - t0) / 1000).toFixed(1)}s`);
