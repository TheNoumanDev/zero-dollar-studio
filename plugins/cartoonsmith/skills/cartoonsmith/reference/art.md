# Character and set art

The user makes the art with an image tool they have the rights to use (Gemini's free tier works well), or draws it. Keep every prompt in the bible's `style` so the cast looks like one show.

## Rules for every sheet

- Flat 2D, thick dark outlines, flat colours, no gradients or cast shadows. Flat art splits, aligns and (later) bends cleanly; 3D-looking shading doesn't.
- Plain white background, nothing touching the page edge, no text, labels or panel borders.
- Big eyes and a clear view of the mouth. A beard or a hand over the mouth makes lip sync unreadable.
- One character per sheet.

## Face sheet (required)

> Character sheet for an animated show. Style: {style}. Character: {description}. A 4×3 grid of the exact same head-and-shoulders bust facing the viewer, same size and position in every cell, on a plain white background, no text or labels. Row 1 mouths: closed; slightly open showing teeth; open; wide open. Row 2 mouths: round O; small pucker; top teeth on lower lip; tongue behind top teeth. Row 3 faces: laughing; angry; shocked; sad.

The order matters: `tools/rig_character.sh` maps the cells to Rhubarb's mouth shapes (A/X closed, B, C, D, E, F, G, H) and then four expressions. For another order, pass `MAP=A=00,B=01,…,X=00,laugh=08,…`.

## Pose sheet (optional)

> Full-body character sheet for an animated show. Style: {style}. Character: {description}. {N} full-body poses side by side, well apart, not touching, on a plain white background, no text: 1) A-pose, facing the viewer, arms held 30-40 degrees out from the body with a clear gap, legs apart; 2) {pose}; 3) {pose}.

Name the poses in order when rigging: `POSES="apose wave sit"`.

## Set paintings

> Background painting for an animated show, no characters. Style: {style}. {set description}. Eye-level view, {16:9 | 9:16}, the middle third fairly plain (characters stand there), soft even light.

Save as `public/<series>/sets/<set>.png` and set `"image": "sets/<set>.png"` in the bible.

## When a sheet comes out wrong

| Problem | Fix |
|---|---|
| Cells framed differently (head jumps between mouths) | Regenerate: "same size and position in every cell". Check the mouth box `viseme_align.py` prints. |
| Faces too small or soft | `UPSCALE=1` (Real-ESRGAN anime model; `MODEL=realesrgan-x4plus` for painted art) |
| White clothes disappear | `REMBG=1` (AI matte + hole fill) |
| Busts touch each other | Fine with the face sheet's grid mode; for pose sheets ask for more space |
| Fewer than 12 faces found | Labels or specks were dropped, or two cells merged. Look at `art/<series>/<id>/cuts/faces/`. |
