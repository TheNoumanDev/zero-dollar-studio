"""Pick the best take of every line in a raw talking-head recording, and print the script that is kept.

Usage: .venv/bin/python tools/footage/takes.py footage/<slug>          # select takes, write takes.json, print the script
       .venv/bin/python tools/footage/takes.py footage/<slug> --show   # print the script from an edited takes.json
       .venv/bin/python tools/footage/takes.py footage/<slug> --keep 4,7 --drop 5   # flip lines by number

Reads footage/<slug>/words.json (transcribe.py --verbatim). Steps:
  1. Split the words into lines: at . ? ! or a pause over BREAK seconds.
  2. Drop "meta" lines ("let me start again", "okay", "cut that") and lines made only of fillers.
  3. Inside a line, drop false starts: "the best way to... the best way to learn" keeps the second try.
  4. Group retakes: neighbouring lines that say nearly the same thing (fuzzy word match). Keep the last
     complete take of each group; the earlier and the broken-off takes go.
  5. Drop filler words (um, uh, hmm) from kept lines.
Writes footage/<slug>/takes.json: one entry per line with "keep" (edit it by hand or with --keep/--drop),
"why" (reason it was dropped) and "cut" (word indices removed inside the line).
"""
import argparse
import json
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/podcast"))
sys.path.insert(0, str(Path(__file__).parent))
import audio  # noqa: E402
import prepare  # noqa: E402  (snipshorts: keep_ranges, FPS)

BREAK = 0.9         # a pause this long ends a line even without punctuation
RESTART_GAP = 0.25  # a repeated phrase counts as a restart after a hesitation this long (or a dash)
LOOKAHEAD = 3       # a retake can come up to 3 lines later
FILLERS = {"um", "umm", "uh", "uhh", "uhm", "erm", "er", "ah", "eh", "hmm", "hm", "mm", "mhm"}
META = re.compile(r"\b(let me (start|try|do (that|this|it)|say (that|this|it))( again| over)?|start(ing)? (again|over)|"
                  r"one more time|(take|try) (two|three|four|\d+)|cut (that|it)|scratch that|from the top|do (that|it) again)\b")
LEAD_IN = {"okay", "ok", "alright", "right", "so", "yeah"}
CHATTER = {"okay", "ok", "alright", "right", "sorry", "so", "yeah", "cool", "again", "wait", "no", "hold on", "one sec"}


def norm(w):
    return re.sub(r"[^\w']", "", w.lower())


def ends_line(w):
    return w.rstrip("\"')").endswith((".", "?", "!"))


def flat_words(folder: Path):
    return [w for s in json.loads((folder / "words.json").read_text())["segments"] for w in s["words"] if w["w"].strip()]


def split_lines(words):
    lines, cur = [], []
    for i, w in enumerate(words):
        if cur and w["s"] - words[i - 1]["e"] > BREAK:
            lines.append(cur)
            cur = []
        cur.append(i)
        if ends_line(w["w"]):
            lines.append(cur)
            cur = []
    if cur:
        lines.append(cur)
    return lines


def false_starts(idx, words):
    """Word indices of abandoned starts inside one line: A B (C) ... A B C, where the repeat
    follows a hesitation or a dash. Returns the indices before the restart."""
    toks = [norm(words[i]["w"]) for i in idx]
    cut, i = set(), 0
    while i < len(toks):
        hit = None
        for n in (4, 3, 2):
            for j in range(i + n, min(i + n + 8, len(toks) - n + 1)):
                if toks[i:i + n] != toks[j:j + n] or "" in toks[i:i + n]:
                    continue
                prev = words[idx[j - 1]]
                frag = [words[k]["w"] for k in idx[i:j]]
                hesitated = words[idx[j]]["s"] - prev["e"] >= RESTART_GAP or prev["w"].endswith(("-", "—", "–", "...", "…"))
                # Said straight through, a repeat of 3+ words with no punctuation in between is still a retry.
                unbroken = n >= 3 and not any(w[-1] in ",.;:?!" for w in frag)
                # "don't forget to subscribe, don't forget to click" is a list: a comma-ended fragment is only
                # a false start when the retry repeats all of it.
                m = 0
                while j + m < len(toks) and i + m < j and toks[i + m] == toks[j + m]:
                    m += 1
                if (hesitated or unbroken) and not (prev["w"].endswith(",") and m < j - i):
                    hit = j
                    break
            if hit:
                break
        if hit:
            cut.update(idx[i:hit])
            i = hit
        else:
            i += 1
    return cut


def similar(a, b):
    """Two lines are takes of the same sentence: their openings match, or most of their words do."""
    k = min(len(a), len(b), 5)
    if k >= 2 and SequenceMatcher(None, a[:k], b[:k]).ratio() >= 0.8:
        return True
    return min(len(a), len(b)) >= 3 and SequenceMatcher(None, a, b).ratio() >= 0.6


def select(words):
    lines = []
    for n, idx in enumerate(split_lines(words)):
        text = " ".join(words[i]["w"] for i in idx)
        toks = [norm(words[i]["w"]) for i in idx]
        spoken = [t for t in toks if t and t not in FILLERS]
        line = {"n": n + 1, "w0": idx[0], "w1": idx[-1] + 1, "text": text, "start": words[idx[0]]["s"],
                "end": words[idx[-1]]["e"], "keep": True, "why": "", "cut": []}
        if not spoken:
            line.update(keep=False, why="filler")
        # Only short lines can be meta: "try it one more time and you'll see" is content.
        elif (len(spoken) <= 8 and META.search(" ".join(toks))) or " ".join(spoken) in CHATTER:
            line.update(keep=False, why="meta")
        else:
            cut = false_starts(idx, words)
            cut |= {i for i in idx if norm(words[i]["w"]) in FILLERS}
            # "Okay, [pause] so the best way..." : the warm-up word before a pause isn't part of the line.
            if len(idx) > 1 and toks[0] in LEAD_IN and words[idx[1]]["s"] - words[idx[0]]["e"] >= 0.4:
                cut.add(idx[0])
            line["cut"] = sorted(cut)
            line["_idx"] = [i for i in idx if i not in cut]
            line["_toks"] = [norm(words[i]["w"]) for i in line["_idx"]]
            line["_done"] = ends_line(words[idx[-1]]["w"])
        lines.append(line)

    spoken = [ln for ln in lines if ln["keep"]]
    # A restart across a pause: "link in my bio, go try it out and [pause] go try it on your own..." cuts
    # the abandoned tail of the first line when the next line opens with the same three words.
    for a, b in zip(spoken, spoken[1:]):
        head = b["_toks"][:3]
        for p in range(max(1, len(a["_toks"]) - 10), len(a["_toks"]) - 2):
            if len(head) == 3 and a["_toks"][p:p + 3] == head:
                tail = a["_idx"][p:]
                if ends_line(words[tail[-1]]["w"]) and len(tail) > 6:
                    break  # a finished sentence: the retake grouping below decides
                a["cut"] = sorted(set(a["cut"]) | set(tail))
                a["_idx"], a["_toks"] = a["_idx"][:p], a["_toks"][:p]
                break
    # Retake groups: chain each spoken line to a similar one within the next LOOKAHEAD spoken lines.
    group = {id(ln): k for k, ln in enumerate(spoken)}
    for a_i, a in enumerate(spoken):
        for b in spoken[a_i + 1:a_i + 1 + LOOKAHEAD]:
            if similar(a["_toks"], b["_toks"]):
                old, new = group[id(a)], group[id(b)]
                for ln in spoken:
                    if group[id(ln)] == old:
                        group[id(ln)] = new
                break
    for g in set(group.values()):
        takes = [ln for ln in spoken if group[id(ln)] == g]
        if len(takes) < 2:
            continue
        longest = max(len(t["_toks"]) for t in takes)
        # Best take: the last one that finishes its sentence and isn't cut short; else the longest.
        full = [t for t in takes if t["_done"] and len(t["_toks"]) >= 0.8 * longest]
        best = full[-1] if full else max(takes, key=lambda t: len(t["_toks"]))
        for k, t in enumerate(takes):
            t["take"] = f"{k + 1}/{len(takes)}"
            if t is not best:
                t.update(keep=False, why=f"retake {k + 1}/{len(takes)}, kept line {best['n']}")
    for ln in lines:
        for k in ("_toks", "_done", "_idx"):
            ln.pop(k, None)
    return lines


def edit_ranges(lines, words, length):
    """Source-time ranges to keep: kept lines minus cut words, with snipshorts' jump cuts on long pauses.
    Each run of kept words is padded, but never into a removed word."""
    kept = sorted(i for ln in lines if ln["keep"] for i in range(ln["w0"], ln["w1"]) if i not in set(ln["cut"]))
    runs = []
    for i in kept:
        if runs and i == runs[-1][-1] + 1:
            runs[-1].append(i)
        else:
            runs.append([i])
    ranges = []
    for run in runs:
        rs = [list(r) for r in prepare.keep_ranges([words[i] for i in run], 0.0, length)]
        if run[0] > 0:
            rs[0][0] = max(rs[0][0], words[run[0] - 1]["e"] + 0.03)
        if run[-1] + 1 < len(words):
            rs[-1][1] = min(rs[-1][1], words[run[-1] + 1]["s"] - 0.03)
        for a, b in rs:
            a, b = round(a * prepare.FPS) / prepare.FPS, round(b * prepare.FPS) / prepare.FPS
            if b - a < 0.05:
                continue
            if ranges and a <= ranges[-1][1]:
                ranges[-1][1] = max(ranges[-1][1], b)
            else:
                ranges.append([a, b])
    return [tuple(r) for r in ranges], kept


def show(lines, words, target):
    dim, green, red, off = "\033[2m", "\033[32m", "\033[31m", "\033[0m"
    for ln in lines:
        if ln["keep"]:
            cut = set(ln["cut"])
            text = " ".join(f"{dim}[{words[i]['w']}]{off}" if i in cut else words[i]["w"] for i in range(ln["w0"], ln["w1"]))
            print(f"{green}✓ {ln['n']:>3}{off}  {ln['start']:6.1f}s  {text}")
        else:
            print(f"{red}✗ {ln['n']:>3}{off}  {ln['start']:6.1f}s  {dim}{ln['text']}  ({ln['why']}){off}")
    length = words[-1]["e"] + 1.0
    ranges, kept = edit_ranges(lines, words, length)
    dur = sum(b - a for a, b in ranges)
    n_kept = sum(ln["keep"] for ln in lines)
    note = "" if target[0] <= dur <= target[1] else f"  ⚠️  outside the {target[0]}-{target[1]} s target"
    print(f"\nKept {n_kept} of {len(lines)} lines, {len(kept)} words: about {dur:.1f} s "
          f"(raw {length - 1:.1f} s, {len(ranges)} cuts){note}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("folder")
    ap.add_argument("--show", action="store_true", help="print the script from takes.json without re-selecting")
    ap.add_argument("--keep", default="", help="line numbers to keep, e.g. 4,7")
    ap.add_argument("--drop", default="", help="line numbers to drop")
    args = ap.parse_args()
    folder = Path(args.folder)
    cfg = json.loads((folder / "footage.json").read_text())
    words = flat_words(folder)
    out = folder / "takes.json"
    if args.show or args.keep or args.drop:
        saved = json.loads(out.read_text())
        lines, quiet = saved["lines"], saved.get("untranscribed", [])
    else:
        voiced = audio.envelope(folder / "source.mp4")
        data = json.loads((folder / "words.json").read_text())
        if data.get("refined") != audio.VERSION:
            # Once: pull pauses Whisper hid inside words back out, so pauses and restarts show.
            moved = audio.refine([w for s in data["segments"] for w in s["words"]], voiced)
            data["refined"] = audio.VERSION
            (folder / "words.json").write_text(json.dumps(data, ensure_ascii=False))
            print(f"word timings: {moved} words trimmed to their voiced part")
            words = flat_words(folder)
        quiet = audio.untranscribed(words, voiced)
        lines = select(words)
    flips = {int(n): True for n in args.keep.split(",") if n} | {int(n): False for n in args.drop.split(",") if n}
    for ln in lines:
        if ln["n"] in flips:
            ln["keep"], ln["why"] = flips[ln["n"]], "" if flips[ln["n"]] else "dropped by hand"
    out.write_text(json.dumps({"lines": lines, "untranscribed": quiet}, indent=1, ensure_ascii=False))
    show(lines, words, cfg.get("target", [30, 75]))
    for a, b in quiet:
        print(f"⚠️  {a:.1f}-{b:.1f} s: speech with no transcript (another language than \"{cfg.get('language', 'en')}\"? "
              "mumbling?). It is left out. For a bilingual recording, make one reel per language: trim the file, "
              "set \"language\", delete words.json and rerun.")


if __name__ == "__main__":
    main()
