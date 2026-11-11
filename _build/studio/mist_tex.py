"""Render textures for Mist, straight from the Mist pack files (make_mist_packs.jsx exports them to tex/mist-raw/).

    python3 mist_tex.py

tex/mist-raw/<name>.png        artwork + foil (in its visual colour)  -> tex/mist/<name>.png
tex/mist-raw/<name>-foil.png   the foil layer alone, on white         -> tex/mist/<name>-metal.png (white = foil)
tex/mist-raw/<name>-hb.png     the high build layer alone, on white   -> tex/mist/<name>-hb.png    (white = high build)
tex/mist-raw/<range>/carton.png  each range's carton colours          -> tex/mist-<range>/carton.png (+ the carton masks)
"""
import shutil
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).parent
RAW, OUT = HERE / 'tex' / 'mist-raw', HERE / 'tex' / 'mist'


def mask(path):
    """A single spot colour on white -> 0-1 coverage (anti-aliased edges kept)."""
    a = np.asarray(Image.open(path).convert('RGB')).astype(np.float32)
    d = 255 - a                                   # distance from white per channel
    n = np.linalg.norm(d, axis=2)
    if n.max() < 1:
        return np.zeros(n.shape, np.float32)
    ink = d[n >= np.percentile(n[n > 1], 90)].mean(0)   # the spot's own colour (as a distance from white)
    return np.clip((d @ ink) / (ink @ ink), 0, 1)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for f in sorted(RAW.glob('*.png')):
        if f.stem.endswith('-foil') or f.stem.endswith('-hb'):
            continue
        shutil.copy(f, OUT / f.name)
        for kind, suffix in (('foil', 'metal'), ('hb', 'hb')):
            m = mask(RAW / f'{f.stem}-{kind}.png')
            Image.fromarray((m * 255 + 0.5).astype(np.uint8)).save(OUT / f'{f.stem}-{suffix}.png')
        print('mist', f.name)
    for d in sorted(p for p in RAW.iterdir() if p.is_dir()):
        o = HERE / 'tex' / f'mist-{d.name}'; o.mkdir(parents=True, exist_ok=True)
        shutil.copy(d / 'carton.png', o / 'carton.png')
        for s in ('metal', 'hb'):
            shutil.copy(OUT / f'carton-{s}.png', o / f'carton-{s}.png')
        print('mist-' + d.name)


if __name__ == '__main__':
    main()
