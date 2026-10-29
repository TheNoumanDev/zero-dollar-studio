"""
Draw stand-in character sheets for the example series, so it renders before you have real art.

    .venv/bin/python tools/make_placeholder_cast.py [series]   # default: milo-and-rosa

For every character in series/<series>/series.json it writes, in the same layout
the cartoonsmith skill asks an image tool for:
  art/<series>/<id>/faces.png   4×3 grid of one bust on white: 8 mouth shapes, 4 expressions
  art/<series>/<id>/poses.png   two full-body poses on white (A-pose, wave)
Then run tools/rig_character.sh on them, exactly as with real sheets.
"""

import json
import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw

series = sys.argv[1] if len(sys.argv) > 1 else "milo-and-rosa"
bible = json.loads((Path("series") / series / "series.json").read_text())
INK, SKIN, WHITE = (40, 34, 38), (246, 205, 170), (255, 255, 255)
CELL = 512


def rgb(hex_color: str) -> tuple:
    h = hex_color.lstrip("#")
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))


def darker(c: tuple, k: float = 0.55) -> tuple:
    return tuple(int(v * k) for v in c)


def mouth(d: ImageDraw.ImageDraw, cx: int, cy: int, kind: str) -> None:
    """Mouth shapes, Rhubarb names (A–H) plus expression mouths."""
    red, tongue = (150, 40, 50), (230, 110, 120)
    if kind == "A":  # closed
        d.line([(cx - 34, cy), (cx + 34, cy)], fill=INK, width=8)
    elif kind in ("B", "C", "D"):  # slightly open → wide open
        h = {"B": 14, "C": 28, "D": 48}[kind]
        w = {"B": 40, "C": 42, "D": 44}[kind]
        d.ellipse([cx - w, cy - h, cx + w, cy + h], fill=red, outline=INK, width=7)
        if kind == "B":
            d.rectangle([cx - w + 10, cy - h + 4, cx + w - 10, cy - 2], fill=WHITE)  # teeth
        else:
            d.ellipse([cx - w * 0.55, cy + h * 0.2, cx + w * 0.55, cy + h - 6], fill=tongue)
    elif kind == "E":  # round O
        d.ellipse([cx - 26, cy - 30, cx + 26, cy + 30], fill=red, outline=INK, width=7)
    elif kind == "F":  # pucker
        d.ellipse([cx - 16, cy - 16, cx + 16, cy + 16], fill=red, outline=INK, width=7)
    elif kind == "G":  # teeth on lower lip
        d.chord([cx - 40, cy - 22, cx + 40, cy + 22], 0, 180, fill=red, outline=INK, width=7)
        d.rectangle([cx - 28, cy - 4, cx + 28, cy + 10], fill=WHITE, outline=INK, width=3)
    elif kind == "H":  # tongue up
        d.ellipse([cx - 38, cy - 26, cx + 38, cy + 26], fill=red, outline=INK, width=7)
        d.ellipse([cx - 16, cy - 22, cx + 16, cy + 2], fill=tongue)
    elif kind == "laugh":
        d.chord([cx - 50, cy - 30, cx + 50, cy + 44], 0, 180, fill=red, outline=INK, width=7)
    elif kind == "angry":
        d.arc([cx - 36, cy, cx + 36, cy + 40], 200, 340, fill=INK, width=8)
    elif kind == "shocked":
        d.ellipse([cx - 30, cy - 36, cx + 30, cy + 36], fill=red, outline=INK, width=7)
    elif kind == "sad":
        d.arc([cx - 34, cy + 2, cx + 34, cy + 40], 210, 330, fill=INK, width=8)


def eyes(d: ImageDraw.ImageDraw, cx: int, cy: int, kind: str) -> None:
    for side in (-1, 1):
        x = cx + side * 52
        if kind == "laugh":
            d.arc([x - 22, cy - 10, x + 22, cy + 22], 200, 340, fill=INK, width=8)
            continue
        r = 30 if kind == "shocked" else 24
        d.ellipse([x - r, cy - r, x + r, cy + r], fill=WHITE, outline=INK, width=6)
        d.ellipse([x - 9, cy - 9, x + 9, cy + 9], fill=INK)
        if kind in ("angry", "sad"):  # brows slope down toward the nose (angry) or away (sad)
            inner, outer = (cy - 32, cy - 52) if kind == "angry" else (cy - 54, cy - 36)
            left, right = (outer, inner) if side < 0 else (inner, outer)
            d.line([(x - 30, left), (x + 30, right)], fill=INK, width=9)
        else:
            d.arc([x - 26, cy - 52, x + 26, cy - 24], 200, 340, fill=INK, width=7)


def bust(d: ImageDraw.ImageDraw, ox: int, oy: int, shirt: tuple, hair: tuple, kind: str) -> None:
    """One bust in a 512×512 cell: shoulders run off the bottom, like a real bust sheet."""
    cx = ox + CELL // 2
    d.polygon([(cx - 120, oy + 380), (cx + 120, oy + 380), (cx + 210, oy + 500), (cx - 210, oy + 500)], fill=shirt, outline=INK, width=8)
    d.rectangle([cx - 34, oy + 330, cx + 34, oy + 392], fill=SKIN, outline=INK, width=7)
    d.ellipse([cx - 150, oy + 60, cx + 150, oy + 360], fill=SKIN, outline=INK, width=8)
    d.chord([cx - 156, oy + 40, cx + 156, oy + 250], 180, 360, fill=hair, outline=INK, width=8)
    for side in (-1, 1):  # ears
        d.ellipse([cx + side * 150 - 22, oy + 190, cx + side * 150 + 22, oy + 250], fill=SKIN, outline=INK, width=6)
    eyes(d, cx, oy + 190, kind)
    mouth(d, cx, oy + 290, kind)


def body(d: ImageDraw.ImageDraw, cx: int, top: int, shirt: tuple, hair: tuple, wave: bool) -> None:
    """A simple full body, arms clear of the torso (A-pose), feet apart."""
    hip, sh = top + 520, top + 250
    for side in (-1, 1):
        d.line([(cx + side * 30, hip), (cx + side * 80, top + 760)], fill=INK, width=34)
        d.line([(cx + side * 30, hip), (cx + side * 80, top + 760)], fill=(70, 80, 120), width=22)
        if wave and side == 1:
            end = (cx + 210, sh - 150)
        else:
            a = math.radians(55)
            end = (cx + side * (90 + 230 * math.sin(a)), sh + 230 * math.cos(a))
        d.line([(cx + side * 90, sh + 10), end], fill=INK, width=34)
        d.line([(cx + side * 90, sh + 10), end], fill=shirt, width=22)
        d.ellipse([end[0] - 22, end[1] - 22, end[0] + 22, end[1] + 22], fill=SKIN, outline=INK, width=6)
    d.rectangle([cx - 26, top + 200, cx + 26, sh + 20], fill=SKIN, outline=INK, width=7)  # neck
    d.rounded_rectangle([cx - 100, sh, cx + 100, hip + 20], radius=40, fill=shirt, outline=INK, width=8)
    d.ellipse([cx - 110, top, cx + 110, top + 230], fill=SKIN, outline=INK, width=8)
    d.chord([cx - 116, top - 12, cx + 116, top + 150], 180, 360, fill=hair, outline=INK, width=8)
    eyes(d, cx, top + 110, "laugh" if wave else "neutral")
    mouth(d, cx, top + 175, "laugh" if wave else "A")


KINDS = ["A", "B", "C", "D", "E", "F", "G", "H", "laugh", "angry", "shocked", "sad"]
HAIR = [(92, 60, 36), (25, 22, 30), (180, 90, 40), (230, 200, 90)]
for n, (cid, c) in enumerate(bible["characters"].items()):
    shirt, hair = rgb(c.get("color", "#88aadd")), HAIR[n % len(HAIR)]
    out = Path("art") / series / cid
    out.mkdir(parents=True, exist_ok=True)
    sheet = Image.new("RGB", (CELL * 4, CELL * 3), WHITE)
    d = ImageDraw.Draw(sheet)
    for i, kind in enumerate(KINDS):
        bust(d, (i % 4) * CELL, (i // 4) * CELL, shirt, hair, kind)
    sheet.save(out / "faces.png")
    poses = Image.new("RGB", (1400, 1000), WHITE)
    d = ImageDraw.Draw(poses)
    body(d, 350, 120, shirt, hair, wave=False)
    body(d, 1050, 120, shirt, hair, wave=True)
    poses.save(out / "poses.png")
    print(f"{out}/faces.png, poses.png")
