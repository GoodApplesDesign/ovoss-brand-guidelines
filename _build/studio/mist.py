"""Mist (Joey, 11 Nov 2026): the Original navy palette on a light tint of each range's hue, a darker wave fill,
foil in the range's own hue (the V, the wave trim, the whole dentist badge, ticks on the benefits list),
and high build (raised gloss UV) on the logo, the wave trim and the dentist badge.

Reads the flat textures from export_textures.jsx (tex/*.png) and export_range_cartons.jsx (tex/range/*.png)
and the "mist" entry in palettes.json. Writes tex/<variant>/<file>.png (colour), <file>-metal.png (foil)
and <file>-hb.png (high build), which studio.html uses with ?tex=<variant>&metal=1.

    python3 mist.py          # Implant Care (carton, tube, mouthwash) + the range cartons

By role (source colours in palettes.json "source"):
  white   -> the range's tint (inside the barcode box it stays white; on the lid it stays white)
  primary -> navy type; the range's dark on the lid / base flap
  light   -> the wave fill; on the lid it's the V, so foil
  band    -> the wave trim: foil + high build
  accent  -> the V (inside v_regions): foil; elsewhere the claims, in "claims"
Positions below were measured on the 8 Nov textures (see HANDOFF); move them if the artwork moves.
"""
import json
from collections import deque
from pathlib import Path
import itertools
import numpy as np
from PIL import Image

HERE = Path(__file__).parent
CFG = json.loads((HERE / 'palettes.json').read_text())
M = CFG['palettes']['mist']
ROLES = ['white', 'primary', 'light', 'band', 'accent', 'black']
PAIRS = list(itertools.combinations(range(len(ROLES)), 2))


def rgb(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], dtype=np.float32)


SRC = np.stack([rgb(CFG['source'][r]) for r in ROLES])
ONE = {r: np.array([[1.0 if q == r else 0.0] for q in ROLES], np.float32) for r in ROLES}


def remap(arr, dst, residual=True):
    """Each pixel = a mix of two source roles (anti-aliased edges); rebuild it from the same mix of dst rows.
    dst rows can have 3 channels (colours) or 1 (a weight, e.g. foil)."""
    h, w, _ = arr.shape
    out = np.empty((h, w, dst.shape[1]), dtype=np.float32)
    for y0 in range(0, h, 256):
        p = arr[y0:y0 + 256].reshape(-1, 3)
        best = np.full(len(p), np.inf, dtype=np.float32)
        res = np.zeros((len(p), dst.shape[1]), dtype=np.float32)
        for i, j in PAIRS:
            a, d = SRC[i], SRC[j] - SRC[i]
            t = np.clip(((p - a) @ d) / (d @ d), 0, 1)[:, None]
            proj = a + t * d
            dist = ((p - proj) ** 2).sum(1)
            m = dist < best
            best[m] = dist[m]
            v = dst[i] + t[m] * (dst[j] - dst[i])
            if residual and dst.shape[1] == 3:
                v = v + (p[m] - proj[m])
            res[m] = v
        out[y0:y0 + 256] = res.reshape(-1, w, dst.shape[1])
    return out


def weight(arr, *roles):
    return remap(arr, sum(ONE[r] for r in roles), residual=False)[..., 0]


# ---------- where things are on each texture (px) ----------
PX = {'carton.png': 3920 / 276.44, 'tube-label.png': 1938 / 114, 'mw-front.png': 1169 / 59, 'mw-back.png': 1169 / 59}
BADGES = {'carton.png': (2407.0, 2647.0, 99.5), 'tube-label.png': (658.5, 1321.5, 111.0), 'mw-front.png': (891.5, 1960.5, 159.0)}
BARCODES = {'carton.png': (1002, 2637, 1434, 2898), 'tube-label.png': (1330, 1349, 1848, 1662), 'mw-back.png': (469, 1920, 1072, 2284)}
BULLETS = {'carton.png': ([(2764, 2157), (2764, 2198), (2764, 2239), (2764, 2280), (2764, 2362)], 11),
           'mw-back.png': ([(108.5, 543.5), (108.5, 589.5), (108.5, 635.5), (108.5, 681.5), (108.5, 728)], 12)}
# wordmarks (high build): (box, roles that are the letters there)
LOGOS = {'carton.png': [((2234, 1476, 2597, 1566), ('primary', 'accent')),    # front
                        ((1102, 1453, 1342, 1515), ('primary', 'accent')),    # back panel
                        ((1049, 955, 1384, 1038), ('white', 'light')),       # lid (white on dark)
                        ((1616, 1508, 1907, 2746), ('primary', 'accent'))],  # big side wordmark
         'tube-label.png': [((442, 213, 892, 323), ('primary', 'accent'))],
         'mw-front.png': [((117, 164, 601, 281), ('primary', 'accent'))]}
V_SRC = ('carton.png', (2307, 1467, 2402, 1570))  # the front logo's V, used as the tick


def lid_regions(arr):
    """The carton's two solid navy blocks (lid + tuck at top left, base flap + tuck at bottom)."""
    if arr.shape[:2] != (4535, 3920):
        return []
    navy = np.abs(arr - SRC[1]).sum(2) < 40
    px = PX['carton.png']; H = arr.shape[0]
    out = []
    for x0, x1, y0, y1 in [(0, int(115 * px), 0, int(H - 225 * px)), (int(140 * px), int(200 * px), int(H - 95 * px), H)]:
        ys, xs = np.where(navy[y0:y1, x0:x1])
        out.append((x0 + xs.min(), y0 + ys.min(), x0 + xs.max() + 1, y0 + ys.max() + 1))
    return out


def components(mask):
    lab = np.zeros(mask.shape, int); comps = []
    for y, x in zip(*np.where(mask)):
        if lab[y, x]:
            continue
        n = len(comps) + 1; q = deque([(y, x)]); lab[y, x] = n; pts = []
        while q:
            cy, cx = q.popleft(); pts.append((cy, cx))
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                yy, xx = cy + dy, cx + dx
                if 0 <= yy < mask.shape[0] and 0 <= xx < mask.shape[1] and mask[yy, xx] and not lab[yy, xx]:
                    lab[yy, xx] = n; q.append((yy, xx))
        comps.append(np.array(pts))
    return comps


def resize_f(a, w, h):
    return np.asarray(Image.fromarray(a.astype(np.float32)).resize((w, h), Image.LANCZOS))


def rebadge(src, col, metal, hb, f, paper, foil, scale, ring_mm):
    """Solid disc -> line badge, all foil + high build: thin ring, the knocked-out type, tooth and tick; scaled."""
    cx, cy, r = BADGES[f]
    R = int(r + 4); x0, y0 = int(round(cx)) - R, int(round(cy)) - R
    patch = src[y0:y0 + 2 * R + 1, x0:x0 + 2 * R + 1]
    yy, xx = np.mgrid[0:2 * R + 1, 0:2 * R + 1].astype(np.float32)
    dist = np.hypot(xx - (cx - x0), yy - (cy - y0))
    white, navy = SRC[0], SRC[1]
    t = np.clip(((patch - white) @ (navy - white)) / ((navy - white) @ (navy - white)), 0, 1)
    knock = np.where(dist < r - 1.5, 1 - t, 0)
    w = ring_mm * PX[f] / scale
    ring = np.clip(w / 2 - np.abs(dist - (r - w / 2)) + 0.5, 0, 1)
    a = np.maximum(knock, ring)
    n = int(round((2 * R + 1) * scale)) | 1
    a_s = np.clip(resize_f(a, n, n), 0, 1)
    old = dist < r + 2
    for arr_, v in ((col, paper), (metal, 0), (hb, 0)):
        arr_[y0:y0 + 2 * R + 1, x0:x0 + 2 * R + 1][old] = v
    nx0, ny0 = int(round(cx)) - n // 2, int(round(cy)) - n // 2
    sl = (slice(ny0, ny0 + n), slice(nx0, nx0 + n))
    col[sl] = paper * (1 - a_s[..., None]) + foil * a_s[..., None]
    metal[sl] = np.maximum(metal[sl], a_s); hb[sl] = np.maximum(hb[sl], a_s)


_TICK = None


def tick_shape():
    """The logo's V (front of the carton), as a 0-1 mask cropped to its bounds."""
    global _TICK
    if _TICK is None:
        f, (x0, y0, x1, y1) = V_SRC
        arr = np.asarray(Image.open(HERE / 'tex' / f).convert('RGB')).astype(np.float32)[y0:y1, x0:x1]
        v = weight(arr, 'accent')
        ys, xs = np.where(v > 0.02)
        _TICK = v[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    return _TICK


def ticks(col, metal, f, paper, foil):
    """Benefit bullets -> small foil ticks (the logo's V), centred on each bullet."""
    pts, d = BULLETS[f]
    v = tick_shape(); th = int(round(1.85 * d)); tw = int(round(th * v.shape[1] / v.shape[0]))
    vs = np.clip(resize_f(v, tw, th), 0, 1)
    yy, xx = np.mgrid[-d:d + 1, -d:d + 1]
    for bx, by in pts:
        bx, by = int(round(bx)), int(round(by))
        disc = np.hypot(xx, yy) <= d / 2 + 2
        col[by - d:by + d + 1, bx - d:bx + d + 1][disc] = paper
        x0, y0 = bx - tw // 2, int(round(by - 0.2 * d)) - th // 2
        sl = (slice(y0, y0 + th), slice(x0, x0 + tw))
        col[sl] = col[sl] * (1 - vs[..., None]) + foil * vs[..., None]
        metal[sl] = np.maximum(metal[sl], vs)


def build(files, out_dir, look, src_dir=HERE / 'tex', rename=None):
    """look: paper, wave (fill), dark (lid), foil, claims, ink (type)."""
    out = HERE / 'tex' / out_dir
    out.mkdir(parents=True, exist_ok=True)
    P, F, D, Fo, C, I = (rgb(look[k]) for k in ('paper', 'wave', 'dark', 'foil', 'claims', 'ink'))
    W, K = rgb('#FFFFFF'), rgb('#000000')
    #                 white primary light band accent black
    dst = np.stack([P, I, F, Fo, C, K]); dst_v = np.stack([P, I, F, Fo, Fo, K])
    for f in files:
        arr = np.asarray(Image.open(src_dir / (rename or {}).get(f, f)).convert('RGB')).astype(np.float32)
        col = remap(arr, dst)
        metal = weight(arr, 'band'); hb = metal.copy()                 # wave trim: foil + high build
        for x0, y0, x1, y1 in CFG['v_regions'].get(f, []):           # the V: foil
            col[y0:y1, x0:x1] = remap(arr[y0:y1, x0:x1], dst_v)
            metal[y0:y1, x0:x1] = weight(arr[y0:y1, x0:x1], 'band', 'accent')
        for x0, y0, x1, y1 in lid_regions(arr):                         # lid + base flap: dark, white type, foil V
            col[y0:y1, x0:x1] = remap(arr[y0:y1, x0:x1], np.stack([W, D, Fo, Fo, Fo, K]))
            metal[y0:y1, x0:x1] = weight(arr[y0:y1, x0:x1], 'light', 'band', 'accent')
        for (x0, y0, x1, y1), roles in LOGOS.get(f, []):                # wordmarks: high build
            hb[y0:y1, x0:x1] = np.maximum(hb[y0:y1, x0:x1], weight(arr[y0:y1, x0:x1], *roles))
        if f in BARCODES:                                              # the barcode's white box stays white
            x0, y0, x1, y1 = BARCODES[f]
            col[y0:y1, x0:x1] = remap(arr[y0:y1, x0:x1], np.stack([W, I, F, Fo, C, K]))
        if f in BADGES:
            rebadge(arr, col, metal, hb, f, P, Fo, M['badge_scale'], M['badge_ring_mm'])
        if f in BULLETS:
            ticks(col, metal, f, P, Fo)
        Image.fromarray(np.clip(col + 0.5, 0, 255).astype(np.uint8)).save(out / f)
        for suffix, a in (('metal', metal), ('hb', hb)):
            Image.fromarray(np.clip(a * 255 + 0.5, 0, 255).astype(np.uint8)).save(out / f.replace('.png', f'-{suffix}.png'))
        print(out_dir, f, flush=True)


def look_for(rname):
    rc = M['ranges'][rname]
    return dict(paper=rc['paper'], wave=rc['wave'], dark=rc['dark'], foil=rc['metal'], claims=M['claims'], ink=M['ink'])


def main():
    build(['carton.png', 'tube-label.png', 'mw-front.png', 'mw-back.png'], 'mist', look_for('Implant Care'))
    for rname, slug in [('Implant Care', 'implant-care'), ('Perio Care', 'perio-care'), ('Daily Care', 'daily-care'), ('Restore', 'restore')]:
        build(['carton.png'], f'mist-{slug}', look_for(rname), src_dir=HERE / 'tex' / 'range', rename={'carton.png': f'carton-{slug}.png'})


if __name__ == '__main__':
    main()
