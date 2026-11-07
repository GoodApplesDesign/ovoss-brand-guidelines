# Product render studio

Makes the 9 product images in `assets/img/` (carton, tube, mouthwash, toothpaste pair, range) from the print artwork.
three.js 0.165.0 (pinned, from jsDelivr) in headless Chrome, lit by the Poly Haven `studio_small_09` HDRI (CC0, loaded from Poly Haven).

1. **Textures.** Save the pack files in Illustrator, then run `export_textures.jsx` in Illustrator
   (it stops if any pack file is open with unsaved edits). It copies the three pack .ai files from
   `../../../Ovoss Packaging/` into `.ai_copies/`, hides the dielines (keeps the tube's printed eye mark)
   and writes `tex/carton.png`, `tex/tube-label.png`, `tex/mw-front.png`, `tex/mw-back.png`.
2. **Render.** `node render.mjs out carton-front carton-back tube-front tube-back mw-front mw-back toothpaste:1600x1000 mouthwash:1600x1000 range:1600x1000`
   (renders at 2x, so 2000x2500 and 3200x2000 PNGs). Every line should say `"env":"hdr"`; `room` means the HDRI
   didn't load and the lighting will be off.
3. **Site images.** `python3 finish.py` downsamples `out/*.png` to `assets/img/*.jpg`.

Open `studio.html?scene=range` (with `--allow-file-access-from-files`, or over a local server) to look around a scene.
Scene layouts, camera and lights live in `studio.html`. The environment is turned to `envrot=1.0` (x pi) so the
tube's highlights stay off the type. The bottle shape and the mouthwash back label size are stand-ins.
`tex/`, `out/` and the copies are not committed.
