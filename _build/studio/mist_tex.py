"""Render textures for Mist, straight from the Mist pack files (make_mist_packs.jsx exports them to tex/mist-raw/).

    python3 mist_tex.py

tex/mist-raw/<name>.png        artwork + foil (in its visual colour)  -> tex/mist/<name>.png
tex/mist-raw/<name>-foil.png   the foil layer alone, on white         -> tex/mist/<name>-metal.png (white = foil)
tex/mist-raw/<name>-hb.png     the high build layer alone, on white   -> tex/mist/<name>-hb.png    (white = high build)
tex/mist-raw/<range>/carton.png  each range's carton colours          -> tex/mist-<range>/carton.png (+ the carton masks)
"""
import shutil
from collections import deque
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


# Foil look: each foil element gets its own multi-stop metallic ramp (dark, mid, light, highlight, back down, a
# second softer light band), across it at 35 degrees, built from that pixel's own foil colour. Long thin elements
# (the wave trim) repeat the ramp every ~40 mm so it reads as reflections running along it. Joey, 11 Nov.
RAMP = [(0.00, -0.72), (0.18, -0.25), (0.34, 0.55), (0.44, 0.97), (0.54, 0.40), (0.70, -0.68), (0.84, 0.30),
        (0.92, -0.10), (1.00, -0.72)]   # higher contrast, fewer and longer bands (Joey, 11 Nov)


def ramp(t):
    xs, ys = zip(*RAMP)
    return np.interp(t, xs, ys)


def label(mask, step=4):
    """Connected foil elements on a 1/step grid (8-connected); returns a full-size label image (0 = none)."""
    small = mask[::step, ::step] > 0.3
    lab = np.zeros(small.shape, np.int32); n = 0
    for y, x in zip(*np.where(small)):
        if lab[y, x]:
            continue
        n += 1; q = deque([(y, x)]); lab[y, x] = n
        while q:
            cy, cx = q.popleft()
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    yy, xx = cy + dy, cx + dx
                    if 0 <= yy < small.shape[0] and 0 <= xx < small.shape[1] and small[yy, xx] and not lab[yy, xx]:
                        lab[yy, xx] = n; q.append((yy, xx))
    full = np.kron(lab, np.ones((step, step), np.int32))[:mask.shape[0], :mask.shape[1]]
    # grow labels a little so anti-aliased edges belong to their element
    return full, n


def metallic(col_path, mask_path, px_per_mm):
    col = np.asarray(Image.open(col_path).convert('RGB')).astype(np.float32)
    m = np.asarray(Image.open(mask_path).convert('L')).astype(np.float32) / 255
    lab, n = label(m)
    out = col.copy()
    a = np.radians(35); ca, sa = np.cos(a), np.sin(a)
    for k in range(1, n + 1):
        ys, xs = np.where(lab == k)
        if len(xs) < 4:
            continue
        y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
        w, h = x1 - x0, y1 - y0
        yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
        proj = (xx - x0) * ca + (yy - y0) * sa
        span = w * ca + h * sa
        period = 60 * px_per_mm if w > 4 * h else span * 1.2   # long trims repeat every ~60 mm; others spread a touch wider
        t = (proj / max(period, 1)) % 1.0
        s = ramp(t)[..., None]
        base = col[y0:y1, x0:x1]
        shaded = np.where(s < 0, base * (1 + s), base + (255 - base) * s)
        mm = m[y0:y1, x0:x1][..., None] * (lab[y0:y1, x0:x1] == k)[..., None]
        out[y0:y1, x0:x1] = out[y0:y1, x0:x1] * (1 - mm) + shaded * mm
    Image.fromarray(np.clip(out + 0.5, 0, 255).astype(np.uint8)).save(col_path)
    return n


PXMM = {'carton': 3920 / 276.44, 'tube-label': 1938 / 114, 'mw-front': 1169 / 59, 'mw-back': 1169 / 59}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for f in sorted(RAW.glob('*.png')):
        if f.stem.endswith('-foil') or f.stem.endswith('-hb'):
            continue
        shutil.copy(f, OUT / f.name)
        for kind, suffix in (('foil', 'metal'), ('hb', 'hb')):
            m = mask(RAW / f'{f.stem}-{kind}.png')
            Image.fromarray((m * 255 + 0.5).astype(np.uint8)).save(OUT / f'{f.stem}-{suffix}.png')
        print('mist', f.name, 'foil elements', metallic(OUT / f.name, OUT / f'{f.stem}-metal.png', PXMM[f.stem]))
    for d in sorted(p for p in RAW.iterdir() if p.is_dir()):
        o = HERE / 'tex' / f'mist-{d.name}'; o.mkdir(parents=True, exist_ok=True)
        shutil.copy(d / 'carton.png', o / 'carton.png')
        for s in ('metal', 'hb'):
            shutil.copy(OUT / f'carton-{s}.png', o / f'carton-{s}.png')
        print('mist-' + d.name, 'foil elements', metallic(o / 'carton.png', o / 'carton-metal.png', PXMM['carton']))


if __name__ == '__main__':
    main()
