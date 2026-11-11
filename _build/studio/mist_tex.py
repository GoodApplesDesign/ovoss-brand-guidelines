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


# Foil look (Joey, 11 Nov): each foil element gets its own metallic ramp built in OKLCH from its foil colour, so the
# hue holds and only brightness moves: rich darks, saturated lights, and just the thin core of the main highlight
# goes pale. One main highlight with a deep dark right beside it, a softer second light, smooth (smoothstep) blends.
# Rows: (position, lightness shift, chroma multiplier). Long trims repeat every 60 mm.
RAMP = [(0.00, -0.17, 1.05), (0.16, -0.06, 1.10), (0.30, 0.10, 1.15), (0.37, 0.25, 0.80), (0.40, 0.33, 0.45),
        (0.43, 0.22, 0.85), (0.52, -0.21, 1.00), (0.66, -0.08, 1.10), (0.80, 0.12, 1.10), (0.90, -0.02, 1.08),
        (1.00, -0.17, 1.05)]
# small foil (front logo V, ticks, dentist mark: under 12 mm): stays mid to dark with one thin highlight
RAMP_SMALL = [(0.00, -0.15, 1.05), (0.24, -0.04, 1.10), (0.33, 0.10, 1.10), (0.37, 0.17, 0.85), (0.41, 0.08, 1.10),
              (0.54, -0.17, 1.00), (0.78, -0.05, 1.10), (1.00, -0.15, 1.05)]


def ramp(t, table=RAMP):
    """Smoothstep between stops (no linear kinks), returns (dL, chroma multiplier)."""
    xs = np.array([r[0] for r in table]); i = np.clip(np.searchsorted(xs, t, side='right') - 1, 0, len(xs) - 2)
    x0, x1 = xs[i], xs[i + 1]; u = np.clip((t - x0) / np.maximum(x1 - x0, 1e-6), 0, 1); u = u * u * (3 - 2 * u)
    dl = np.array([r[1] for r in table]); cm = np.array([r[2] for r in table])
    return dl[i] + (dl[i + 1] - dl[i]) * u, cm[i] + (cm[i + 1] - cm[i]) * u


def _lin(c): c = c / 255; return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
def _srgb(c): c = np.clip(c, 0, 1); return np.where(c <= 0.0031308, 12.92 * c, 1.055 * c ** (1 / 2.4) - 0.055) * 255


def to_oklab(rgb):
    r, g, b = [_lin(rgb[..., k]) for k in range(3)]
    l = np.cbrt(0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b); m = np.cbrt(0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b)
    s_ = np.cbrt(0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b)
    return np.stack([0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s_, 1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s_,
                     0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s_], -1)


def from_oklab(lab):
    L, a, b = lab[..., 0], lab[..., 1], lab[..., 2]
    l = (L + 0.3963377774 * a + 0.2158037573 * b) ** 3; m = (L - 0.1055613458 * a - 0.0638541728 * b) ** 3; s_ = (L - 0.0894841775 * a - 1.2914855480 * b) ** 3
    return np.stack([_srgb(4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s_), _srgb(-1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s_),
                     _srgb(-0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s_)], -1)


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
        small = max(w, h) / px_per_mm < 12
        dL, cmul = ramp(t, RAMP_SMALL if small else RAMP)
        core = (lab[y0:y1, x0:x1] == k) & (m[y0:y1, x0:x1] > 0.95)
        base_lab = to_oklab(col[y0:y1, x0:x1][core].mean(0)[None, None, :])[0, 0] if core.any() else to_oklab(col[ys[0], xs[0]][None, None, :])[0, 0]
        L = np.clip(base_lab[0] + dL, 0.12, 0.985)
        shaded = from_oklab(np.stack([L, base_lab[1] * cmul, base_lab[2] * cmul], -1))
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
