"""Swap the OVOSS wordmark in the logo SVGs for v2 (Nov 2026): italic, tighter, tick V, rounded S ends, small upright TM.

Run:  python3 _build/make_logos_v2.py   (then make_monogram.py, make_diagrams.py, make_downloads.py, build.py)

The v2 outlines come from _build/wordmark_v2.json (built from Ovoss_Wordmark_v2_Tick.ai, row 2, by
Ovoss Packaging/_Scripts/wordmark_v2/make_rollout_data.py). They are in the old wordmark's units, scaled to the
old letter width, so each lockup keeps its Implant Care / brand line size and centring. Everything that isn't
the wordmark is left as it was. The V is Slate Grey when the letters are Deep Navy, Ice Blue when they're white;
misuse examples keep one colour treatment throughout. Writes the O's box into o_box.json for the other scripts.
"""
import json, os, re
from fontTools.svgLib.path import parse_path
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.boundsPen import BoundsPen

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
NEW = json.load(open(os.path.join(HERE, 'wordmark_v2.json')))
REF_O1, REF_S2 = (14.4365, 16.1825), (120.267, 16.1835)   # old wordmark: centres of O1 and S2
SLATE, ICE, NAVY, WHITE = '#6F7D8A', '#DCEAF4', '#10233F', '#FFFFFF'
FILES = ['svg/wordmark-navy', 'svg/wordmark-white', 'svg/implant-care-navy', 'svg/implant-care-white',
         'svg/brand-line-navy', 'svg/brand-line-white', 'misuse/wordmark-blue', 'misuse/wordmark-outline', 'misuse/wordmark-silver']


def bbox(d):
    bp = BoundsPen(None); parse_path(d, bp); return bp.bounds


def d_from_anchors(subpaths, f):
    out = []
    for anchors in subpaths:
        n = len(anchors)
        x, y = f(anchors[0][0], anchors[0][1]); out.append(f'M{x:.3f},{y:.3f}')
        for i in range(n):
            a, b = anchors[i], anchors[(i + 1) % n]
            c1 = f(a[4], a[5]); c2 = f(b[2], b[3]); p = f(b[0], b[1])
            if (abs(a[4] - a[0]) + abs(a[5] - a[1]) < 1e-6) and (abs(b[2] - b[0]) + abs(b[3] - b[1]) < 1e-6):
                out.append(f'L{p[0]:.3f},{p[1]:.3f}')
            else:
                out.append(f'C{c1[0]:.3f},{c1[1]:.3f} {c2[0]:.3f},{c2[1]:.3f} {p[0]:.3f},{p[1]:.3f}')
        out.append('Z')
    return ''.join(out)


def translate_d(d, dx, dy):
    rp = RecordingPen(); parse_path(d, rp); out = []
    fmt = lambda p: f'{p[0] + dx:.3f},{p[1] + dy:.3f}'
    for op, pts in rp.value:
        if op == 'moveTo': out.append('M' + fmt(pts[0]))
        elif op == 'lineTo': out.append('L' + fmt(pts[0]))
        elif op == 'curveTo': out.append('C' + ' '.join(fmt(p) for p in pts))
        elif op == 'qCurveTo': out.append('Q' + ' '.join(fmt(p) for p in pts))
        elif op == 'closePath': out.append('Z')
    return ''.join(out)


def swap(name):
    path = os.path.join(ROOT, 'assets', 'logo', name + '.svg')
    svg = open(path, encoding='utf-8').read()
    els = []
    for m in re.finditer(r'<path\b([^>]*?)\sd="([^"]+)"([^>]*)/>', svg):
        attrs = (m.group(1) + m.group(3)).strip(); d = m.group(2)
        els.append({'attrs': attrs, 'd': d, 'b': bbox(d)})
    for e in els:
        x0, y0, x1, y1 = e['b']; e['w'], e['h'] = x1 - x0, y1 - y0; e['c'] = ((x0 + x1) / 2, (y0 + y1) / 2)
    Os = sorted([e for e in els if 0.94 < e['w'] / e['h'] < 0.985], key=lambda e: -e['h'])[:2]
    Oh = Os[0]['h']
    O1, O2 = sorted(Os, key=lambda e: e['b'][0])
    Ss = sorted([e for e in els if 0.70 < e['w'] / e['h'] < 0.76 and abs(e['h'] - Oh) < 0.02 * Oh], key=lambda e: e['b'][0])
    V = [e for e in els if 0.97 < e['w'] / e['h'] < 1.04 and abs(e['h'] - 0.9415 * Oh) < 0.03 * Oh]
    S1, S2 = Ss[0], Ss[-1]
    TM = [e for e in els if e['b'][0] > S2['b'][2] - 0.01 and e['b'][3] < O1['b'][1] + 0.25 * Oh and e['w'] < 0.35 * Oh]
    assert len(V) == 1 and len(TM) == 1 and len(Ss) == 2, (name, len(V), len(TM), len(Ss))
    old = {id(e) for e in [O1, O2, S1, S2, V[0], TM[0]]}
    s = (S2['c'][0] - O1['c'][0]) / (REF_S2[0] - REF_O1[0])
    tx, ty = O1['c'][0] - s * REF_O1[0], O1['c'][1] - s * REF_O1[1]
    f = lambda x, y: (s * x + tx, s * y + ty)
    letter_attrs = O1['attrs']
    fill = re.search(r'fill="([^"]+)"', letter_attrs).group(1).upper()
    if name.startswith('svg/'):
        v_attrs = letter_attrs.replace(f'fill="{fill}"', f'fill="{SLATE if fill == NAVY else ICE}"')
        v_attrs = re.sub(r'fill="[^"]+"', f'fill="{SLATE if fill == NAVY else ICE}"', letter_attrs)
    else:
        v_attrs = letter_attrs
    new = []
    for part in ['O1', 'V', 'O2', 'S1', 'S2', 'TM']:
        new.append({'attrs': v_attrs if part == 'V' else letter_attrs, 'd': d_from_anchors(NEW[part], f)})
    rest = [e for e in els if id(e) not in old]
    allp = new + rest
    bs = [bbox(e['d']) for e in allp]
    minx, miny = min(b[0] for b in bs), min(b[1] for b in bs)
    maxx, maxy = max(b[2] for b in bs), max(b[3] for b in bs)
    pad_stroke = 0.5 if 'stroke-width' in letter_attrs else 0.0
    dx, dy = -minx + pad_stroke, -miny + pad_stroke
    W, H = maxx - minx + 2 * pad_stroke, maxy - miny + 2 * pad_stroke
    body = ''.join(f'<path {e["attrs"]} d="{translate_d(e["d"], dx, dy)}"/>' for e in allp)
    out = f'<svg width="{W:.3f}" height="{H:.3f}" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.3f} {H:.3f}"><g>{body}</g></svg>\n'
    open(path, 'w', encoding='utf-8').write(out)
    ob = bbox(translate_d(new[0]['d'], dx, dy))
    return (round(ob[0], 3), round(ob[1], 3), round(ob[2] - ob[0], 3), round(ob[3] - ob[1], 3)), round(s, 4), (round(W, 3), round(H, 3))


def main():
    boxes = {}
    for n in FILES:
        ob, s, size = swap(n)
        print(f'{n}: scale {s}, size {size}, O box {ob}')
        base = n.split('/')[-1].rsplit('-', 1)[0]
        if n.startswith('svg/'): boxes[base] = ob
    json.dump(boxes, open(os.path.join(HERE, 'o_box.json'), 'w'), indent=1)


if __name__ == '__main__':
    main()
