"""
Final -14 LUFS master for a rendered video, with one fixed gain.

    .venv/bin/python tools/summary/master.py out/summary/<slug>/raw.mp4 out/summary/<slug>/final.mp4

ffmpeg's two-pass loudnorm "linear=true" quietly falls back to dynamic mode when the peaks don't allow the full gain,
and then rides the level up and down through the video. Here: measure the mix, apply one gain to -14 LUFS, and catch
only the few peaks above -2 dBFS with a fast limiter (-2, not -1: the AAC encode overshoots ~1 dB between samples).
Video is copied; audio is AAC 192k at 48 kHz.
"""

import subprocess
import sys

src, dst = sys.argv[1], sys.argv[2]
m = subprocess.run(["ffmpeg", "-hide_banner", "-i", src, "-vn", "-af", "ebur128=framelog=quiet", "-f", "null", "-"], capture_output=True, text=True).stderr
lufs = float(m[m.rindex("I:") :].split()[1])
gain = -14 - lufs
subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", src, "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
                "-af", f"volume={gain:.2f}dB,alimiter=limit=0.79:level=false:attack=3:release=80", dst], check=True)
print(f"master: {lufs:.1f} LUFS → {gain:+.1f} dB → {dst}")
