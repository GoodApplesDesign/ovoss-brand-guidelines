"""Recolour the pack textures for each palette in palettes.json.

Reads tex/*.png (exported by export_textures.jsx) and writes tex/<palette>/*.png.
Every pixel in the flat artwork is a mix of two brand colours (an anti-aliased edge) or one of them,
so each pixel is matched to the nearest line between two source colours and rebuilt from the same
mix of the palette's colours. Anything left over (the residual) is kept, so nothing is lost.

    python3 recolour.py            # all palettes
    python3 recolour.py b-soft     # one palette
"""
import json, sys, itertools
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).parent
CFG = json.loads((HERE / 'palettes.json').read_text())
ROLES = ['white', 'primary', 'light', 'band', 'accent', 'black']
FILES = ['carton.png', 'tube-label.png', 'mw-front.png', 'mw-back.png']


def rgb(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], dtype=np.float32)


SRC = np.stack([rgb(CFG['source'][r]) for r in ROLES])
PAIRS = list(itertools.combinations(range(len(ROLES)), 2))


def recolour(arr, dst):
    out = np.empty_like(arr)
    for y0 in range(0, arr.shape[0], 256):
        p = arr[y0:y0 + 256].reshape(-1, 3)
        best = np.full(len(p), np.inf, dtype=np.float32)
        res = np.zeros_like(p)
        for i, j in PAIRS:
            a, d = SRC[i], SRC[j] - SRC[i]
            t = np.clip(((p - a) @ d) / (d @ d), 0, 1)[:, None]
            proj = a + t * d
            dist = ((p - proj) ** 2).sum(1)
            m = dist < best
            best[m] = dist[m]
            res[m] = (dst[i] + t[m] * (dst[j] - dst[i])) + (p[m] - proj[m])
        out[y0:y0 + 256] = res.reshape(arr[y0:y0 + 256].shape)
    return np.clip(out + 0.5, 0, 255).astype(np.uint8)


def main(keys):
    for key in keys:
        pal = CFG['palettes'][key]
        dst = np.stack([rgb('#FFFFFF'), rgb(pal['primary']), rgb(pal['light']), rgb(pal['band']),
                        rgb(pal['accent']), rgb('#000000')])
        outdir = HERE / 'tex' / key
        outdir.mkdir(parents=True, exist_ok=True)
        for f in FILES:
            src = Image.open(HERE / 'tex' / f).convert('RGB')
            Image.fromarray(recolour(np.asarray(src).astype(np.float32), dst)).save(outdir / f)
        print(key, 'done')


if __name__ == '__main__':
    main(sys.argv[1:] or list(CFG['palettes']))
