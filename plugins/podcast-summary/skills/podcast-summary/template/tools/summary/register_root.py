"""Register the PodcastSummary compositions in src/Root.tsx (safe to re-run).

Usage: .venv/bin/python tools/summary/register_root.py

Adds the imports and a <Folder name="PodcastSummaries"> with one <Composition> per entry in
src/compositions/PodcastSummary/summaries.ts (SUMMARIES and THUMBS) plus summary-cast-preview.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
root_tsx = ROOT / "src/Root.tsx"

IMPORTS = '''import { calculatePodcastSummary, PodcastSummary } from "./compositions/PodcastSummary";
import { CastPreview } from "./compositions/PodcastSummary/CastPreview";
import { DuoThumb } from "./compositions/PodcastSummary/DuoThumb";
import { ProThumb } from "./compositions/PodcastSummary/ProThumb";
import { SUMMARIES, THUMBS } from "./compositions/PodcastSummary/summaries";
'''

FOLDER = '''      <Folder name="PodcastSummaries">
        {SUMMARIES.map((s) => (
          <Composition
            key={s.id}
            id={s.id}
            component={PodcastSummary}
            width={s.wide ? 1920 : 1080}
            height={s.wide ? 1080 : 1920}
            fps={30}
            durationInFrames={300}
            calculateMetadata={calculatePodcastSummary}
            defaultProps={{ slug: s.slug }}
          />
        ))}
        {THUMBS.map((t) =>
          t.kind === "duo" ? (
            <Still key={t.id} id={t.id} component={DuoThumb} width={1280} height={720} defaultProps={t.props} />
          ) : (
            <Still key={t.id} id={t.id} component={ProThumb} width={1280} height={720} defaultProps={t.props} />
          ),
        )}
        <Composition
          id="summary-cast-preview"
          component={CastPreview}
          width={1920}
          height={1080}
          fps={30}
          durationInFrames={1}
          defaultProps={{ cast: [] as string[], mouth: 0.6 }}
        />
      </Folder>
'''


def main():
    src = root_tsx.read_text()
    if "PodcastSummaries" in src:
        print("src/Root.tsx: PodcastSummaries already registered")
        return
    # Imports go after the last import line.
    lines = src.splitlines(keepends=True)
    last = max(i for i, line in enumerate(lines) if line.startswith("import "))
    src = "".join(lines[: last + 1]) + IMPORTS + "".join(lines[last + 1:])
    # <Folder> and <Still> must be imported from "remotion".
    for name in ("Folder", "Still"):
        m = re.search(r'import \{([^}]*)\} from "remotion";', src)
        if m and not re.search(rf"\b{name}\b", m.group(1)):
            src = src[: m.start(1)] + m.group(1).rstrip() + f", {name} " + src[m.end(1):]
    # The folder goes just before the fragment closes.
    end = src.rfind("</>")
    if end == -1:
        sys.exit("src/Root.tsx: no closing </> fragment found; add the PodcastSummaries folder by hand (see this script)")
    line_start = src.rfind("\n", 0, end) + 1
    src = src[:line_start] + FOLDER + src[line_start:]
    root_tsx.write_text(src)
    print("src/Root.tsx: registered the PodcastSummaries folder")


if __name__ == "__main__":
    main()
