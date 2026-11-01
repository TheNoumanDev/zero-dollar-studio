/**
 * Word-level captions for a story.
 *
 *   node tools/captions.mjs stories/<slug>
 *
 * Reads <story>/timeline.json (written by tools/voice.py), transcribes each
 * line's WAV with Whisper on the GPU, then snaps the result onto the script
 * text: Whisper supplies the timings and the script supplies the spelling,
 * so captions never contain typos. Writes:
 *   public/<slug>/captions.json   Remotion Caption[] (ms, composition time)
 *   <story>/captions-report.json  per-line Whisper text, word error rate, matched
 *                                 words and the filled (estimated) stretches
 */
import { execFileSync } from "node:child_process";
import { existsSync, readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import { env } from "@huggingface/transformers";
import {
  disposeWhisperModel,
  downloadWhisperModel,
  loadWhisperModel,
  toCaptions,
  transcribe,
  WHISPER_WEBGPU_SAMPLE_RATE,
} from "@remotion/whisper-webgpu";

const storyDir = process.argv[2];
if (!storyDir) throw new Error("Usage: node tools/captions.mjs stories/<slug>");
const timeline = JSON.parse(readFileSync(path.join(storyDir, "timeline.json"), "utf8"));
const LANG = timeline.language ?? "en";
const MODEL = process.env.WHISPER_MODEL ?? (LANG === "en" ? "small.en" : "small");
const LANGUAGE_NAMES = { hi: "hindi", ur: "urdu", es: "spanish", fr: "french", de: "german", ar: "arabic" };
// Non-English: name the language and stop Whisper's repetition loops ("आप आप आप…").
const transcribeOptions = LANG === "en" ? {} : { language: LANGUAGE_NAMES[LANG] ?? LANG, noRepeatNgramSize: 3, repetitionPenalty: 1.3 };
const NUMBER_WORDS = { zero: "0", one: "1", two: "2", three: "3", four: "4", five: "5", six: "6", seven: "7", eight: "8", nine: "9", ten: "10" };
// Whisper writes "ten" as "10"; normalise both sides so WER only counts real mistakes.
const norm = (w) => {
  const s = w.toLowerCase().replace(/[^\p{L}\p{M}\p{N}']/gu, "");
  return NUMBER_WORDS[s] ?? s;
};

/**
 * Display text differs from the spoken text (e.g. Roman Hinglish captions over
 * Devanagari speech): spread the caption words across the audible span of the
 * line (from its loudness envelope, not Whisper, which may miss words),
 * weighted by word length.
 */
const spread = (words, envelope, fps, lineMs) => {
  const voiced = envelope.map((v, i) => (v > 0.12 ? i : -1)).filter((i) => i >= 0);
  const start = voiced.length ? (voiced[0] / fps) * 1000 : 0;
  const end = voiced.length ? Math.min(lineMs, ((voiced.at(-1) + 1) / fps) * 1000) : lineMs;
  const weights = words.map((w) => norm(w).length + 1);
  const total = weights.reduce((a, b) => a + b, 0);
  let t = start;
  return words.map((_, i) => {
    const d = ((end - start) * weights[i]) / total;
    const out = [t, t + d];
    t += d;
    return out;
  });
};

/** Decode any audio file to 16 kHz mono float32 with ffmpeg. */
const decode = (file) => {
  const buf = execFileSync("ffmpeg", [
    "-v", "error", "-i", file, "-ac", "1", "-ar", String(WHISPER_WEBGPU_SAMPLE_RATE), "-f", "f32le", "-",
  ], { maxBuffer: 1 << 30 });
  return new Float32Array(buf.buffer, buf.byteOffset, buf.byteLength / 4);
};

/**
 * Place words Whisper missed between their matched neighbours: only over the
 * voiced part of the gap (loudness envelope, so no word sits on a pause),
 * longer words getting more time. Falls back to an even split when the gap
 * has no voiced audio.
 */
const fillGap = (words, from, to, envelope, fps) => {
  const frameMs = 1000 / fps;
  const voiced = [];
  for (let f = Math.floor(from / frameMs); f * frameMs < to; f++) {
    if ((envelope?.[f] ?? 0) <= 0.12) continue;
    const s = Math.max(from, f * frameMs), e = Math.min(to, (f + 1) * frameMs);
    if (voiced.length && Math.abs(voiced.at(-1)[1] - s) < 1e-6) voiced.at(-1)[1] = e;
    else voiced.push([s, e]);
  }
  const voicedMs = voiced.reduce((t, [s, e]) => t + e - s, 0);
  if (voicedMs < 40 * words.length) voiced.splice(0, voiced.length, [from, to]);
  const total = voiced.reduce((t, [s, e]) => t + e - s, 0);
  const weights = words.map((w) => norm(w).length + 1);
  const sum = weights.reduce((a, b) => a + b, 0);
  // Map "voiced time elapsed" back onto the real clock.
  const at = (v) => {
    for (const [s, e] of voiced) {
      if (v <= e - s) return s + v;
      v -= e - s;
    }
    return voiced.at(-1)[1];
  };
  let v = 0;
  return weights.map((w) => {
    const d = (total * w) / sum;
    const out = [at(v), at(v + d)];
    v += d;
    return out;
  });
};

/**
 * Align script words to Whisper words (LCS on normalized tokens). Matched
 * words take Whisper's timing; unmatched words are filled into the voiced
 * part of the gap between their neighbours (fillGap).
 */
const snap = (scriptWords, heard, lineMs, envelope, fps) => {
  const a = scriptWords.map(norm);
  const b = heard.map((c) => norm(c.text));
  const dp = Array.from({ length: a.length + 1 }, () => new Array(b.length + 1).fill(0));
  for (let i = a.length - 1; i >= 0; i--)
    for (let j = b.length - 1; j >= 0; j--)
      dp[i][j] = a[i] === b[j] ? dp[i + 1][j + 1] + 1 : Math.max(dp[i + 1][j], dp[i][j + 1]);
  const times = new Array(a.length).fill(null);
  for (let i = 0, j = 0; i < a.length && j < b.length; ) {
    if (a[i] === b[j]) { times[i] = [heard[j].startMs, heard[j].endMs]; i++; j++; }
    else if (dp[i + 1][j] >= dp[i][j + 1]) i++;
    else j++;
  }
  // Fill gaps between known anchors (line start/end as fallbacks).
  const filled = [];
  for (let i = 0; i < times.length; i++) {
    if (times[i]) continue;
    let k = i;
    while (k < times.length && !times[k]) k++;
    const from = i === 0 ? 0 : times[i - 1][1];
    const to = k < times.length ? times[k][0] : lineMs;
    fillGap(scriptWords.slice(i, k), from, to, envelope, fps).forEach((t, m) => (times[i + m] = t));
    filled.push({ words: scriptWords.slice(i, k).join(" "), fromMs: Math.round(from), toMs: Math.round(to) });
  }
  const matched = dp[0][0];
  const wer = 1 - matched / Math.max(a.length, b.length, 1);
  return { times, wer, matched, filled };
};

const t0 = Date.now();
// Models live in tools/models/<hosted id>/ — the Transformers.js file-cache
// layout. remotion.media (Remotion's model host) is blocked on this network,
// so the folder is pre-filled from the Hugging Face mirror (see AGENTS.md);
// elsewhere downloadWhisperModel() fills it normally.
env.cacheDir = path.resolve("tools/models");
const hostedDir = path.join(env.cacheDir, `whisper-${MODEL}_timestamped-v1`);
if (!existsSync(hostedDir)) await downloadWhisperModel({ model: MODEL });
await loadWhisperModel({ model: MODEL });

const captions = [];
const report = [];
let totalWords = 0, totalMatched = 0;
for (const line of timeline.lines) {
  const waveform = decode(line.file);
  const out = await transcribe({ channelWaveform: waveform, model: MODEL, ...transcribeOptions });
  const heard = toCaptions({ whisperWebGpuOutput: out }).captions.filter((c) => norm(c.text));
  const spoken = line.text.split(/\s+/).filter(Boolean);
  const { times: spokenTimes, wer, matched, filled } = snap(spoken, heard, line.durationMs, line.envelope, timeline.fps);
  totalWords += spoken.length;
  totalMatched += matched;
  const caption = line.caption ?? line.text;
  const words = caption.split(/\s+/).filter(Boolean);
  const times = caption === line.text ? spokenTimes : spread(words, line.envelope, timeline.fps, line.durationMs);
  words.forEach((w, i) => {
    captions.push({
      text: (captions.length ? " " : "") + w,
      startMs: Math.round(line.startMs + times[i][0]),
      endMs: Math.round(line.startMs + times[i][1]),
      timestampMs: Math.round(line.startMs + (times[i][0] + times[i][1]) / 2),
      confidence: null,
      speaker: line.speaker,
      // Voice direction: words the line stresses get highlighted on screen too.
      emphasis: (line.emphasis ?? []).some((e) => norm(e) === norm(w)),
    });
  });
  report.push({ speaker: line.speaker, script: line.text, heard: heard.map((c) => c.text).join("").trim(), wer: Number(wer.toFixed(2)), matched: `${matched}/${spoken.length}`, filled });
  console.log(`[${line.speaker}] WER ${(wer * 100).toFixed(0)}%  heard: ${report.at(-1).heard}`);
}

await disposeWhisperModel({ model: MODEL });

writeFileSync(path.join("public", timeline.slug, "captions.json"), JSON.stringify(captions, null, 2));
const avg = report.reduce((s, r) => s + r.wer, 0) / report.length;
const matchRate = totalMatched / Math.max(totalWords, 1);
writeFileSync(
  path.join(storyDir, "captions-report.json"),
  JSON.stringify({ model: MODEL, seconds: (Date.now() - t0) / 1000, averageWer: Number(avg.toFixed(3)), matchRate: Number(matchRate.toFixed(3)), lines: report }, null, 2),
);
console.log(`Captions: ${captions.length} words, avg WER ${(avg * 100).toFixed(1)}%, matched ${(matchRate * 100).toFixed(0)}%, ${((Date.now() - t0) / 1000).toFixed(1)}s`);
// Under 70% matched, the timings are mostly guesses: the script and the audio probably differ (a garbled take, edited text).
if (matchRate < 0.7) console.warn(`⚠ Only ${(matchRate * 100).toFixed(0)}% of words matched Whisper: check captions-report.json ("filled") and re-voice garbled lines.`);
