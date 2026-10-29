"""Register the PodcastShort compositions in src/Root.tsx (safe to re-run).

Usage: python3 tools/podcast/register_root.py

Adds two imports and a <Folder name="PodcastShorts"> with one <Composition> per id in
src/compositions/PodcastShort/clips.ts. make-shorts.sh appends new ids to clips.ts.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
root_tsx = ROOT / "src/Root.tsx"

IMPORTS = '''import { calculatePodcastShort, PodcastShort } from "./compositions/PodcastShort";
import { PODCAST_SHORTS } from "./compositions/PodcastShort/clips";
'''

FOLDER = '''      <Folder name="PodcastShorts">
        {PODCAST_SHORTS.map((id) => (
          <Composition
            key={id}
            id={id}
            component={PodcastShort}
            width={1080}
            height={1920}
            fps={30}
            durationInFrames={900}
            calculateMetadata={calculatePodcastShort}
            defaultProps={{ clipId: id, qa: false }}
          />
        ))}
      </Folder>
'''


def main():
    src = root_tsx.read_text()
    if "PODCAST_SHORTS" in src:
        print("src/Root.tsx: PodcastShorts already registered")
        return
    # Imports go after the last import line.
    lines = src.splitlines(keepends=True)
    last = max(i for i, line in enumerate(lines) if line.startswith("import "))
    src = "".join(lines[: last + 1]) + IMPORTS + "".join(lines[last + 1:])
    # <Folder> must be imported from "remotion".
    m = re.search(r'import \{([^}]*)\} from "remotion";', src)
    if m and "Folder" not in m.group(1):
        src = src[: m.start(1)] + m.group(1).rstrip() + ", Folder " + src[m.end(1):]
    # The folder goes just before the fragment closes.
    end = src.rfind("</>")
    if end == -1:
        sys.exit("src/Root.tsx: no closing </> fragment found; add the PodcastShorts folder by hand (see this script)")
    line_start = src.rfind("\n", 0, end) + 1
    src = src[:line_start] + FOLDER + src[line_start:]
    root_tsx.write_text(src)
    print("src/Root.tsx: registered the PodcastShorts folder")


if __name__ == "__main__":
    main()
