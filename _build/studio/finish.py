"""Downsample the studio PNGs in out/ to the site JPGs in assets/img/ (same names and sizes)."""
from pathlib import Path
from PIL import Image
HERE = Path(__file__).resolve().parent
IMG = HERE.parent.parent / "assets" / "img"
SIZES = {"carton-front": (1200, 1500), "carton-back": (1200, 1500), "tube-front": (1200, 1500), "tube-back": (1200, 1500),
         "mw-front": (1200, 1500), "mw-back": (1200, 1500), "toothpaste": (2400, 1500), "mouthwash": (2400, 1500), "range": (2400, 1500)}
for name, size in SIZES.items():
    Image.open(HERE / "out" / f"{name}.png").convert("RGB").resize(size, Image.LANCZOS).save(IMG / f"{name}.jpg", quality=95, subsampling=2, dpi=(72, 72))
    print(name, size)
