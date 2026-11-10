"""Downsample the studio PNGs to the site JPGs (same names and sizes).

    python3 finish.py           # out/*.png        -> assets/img/*.jpg          (Original)
    python3 finish.py bright    # out/bright/*.png -> assets/bright/img/*.jpg   (the Bright palette preview)

Bright renders come from render.mjs scenes with ~tex=bright~light=DDF1FB, so their files carry that suffix.
"""
import sys
from pathlib import Path
from PIL import Image
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SIZES = {"carton-front": (1200, 1500), "carton-back": (1200, 1500), "tube-front": (1200, 1500), "tube-back": (1200, 1500),
         "mw-front": (1200, 1500), "mw-back": (1200, 1500), "toothpaste": (2400, 1500), "mouthwash": (2400, 1500), "range": (2400, 1500)}
pal = sys.argv[1] if len(sys.argv) > 1 else None
src_dir = HERE / "out" / pal if pal else HERE / "out"
img_dir = ROOT / "assets" / pal / "img" if pal else ROOT / "assets" / "img"
img_dir.mkdir(parents=True, exist_ok=True)
for name, size in SIZES.items():
    src = src_dir / f"{name}.png"
    if not src.exists():
        src = next(src_dir.glob(f"{name}_tex_*.png"))
    Image.open(src).convert("RGB").resize(size, Image.LANCZOS).save(img_dir / f"{name}.jpg", quality=95, subsampling=2, dpi=(72, 72))
    print(name, size, '->', img_dir.relative_to(ROOT))
