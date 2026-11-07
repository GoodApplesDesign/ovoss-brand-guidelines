"""Builds the clear space diagrams and the wave graphic as inline SVG partials in _build/src/partials/.

Run:  python3 _build/make_diagrams.py   (after the logo SVGs exist in assets/logo/svg/)

Clear space: X is the height of the O in OVOSS. Stacks of the logo's own O, at low opacity, show X at the
top-left and bottom-right corners (turned 90 degrees on the sides), touching the logo and the boundary.
"""
import math, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LOGOS = os.path.join(ROOT, 'assets', 'logo', 'svg')
OUT = os.path.join(HERE, 'src', 'partials')
O_INDEX = 0  # the O is the first shape in the v2 wordmark SVGs (DOM order)
O_BOX = {'wordmark': (0.0, 1.136, 30.884, 30.218), 'implant-care': (0.0, 1.363, 37.061, 36.262), 'brand-line': (0.0, 1.363, 37.061, 36.262)}  # x, y, w, h of the O (v2, from make_logos_v2.py)


def inner(svg):
    vb = [float(v) for v in re.search(r'viewBox="([^"]+)"', svg).group(1).split()]
    body = re.sub(r'^.*?<svg[^>]*>|</svg>\s*$', '', svg, flags=re.S)
    return vb, body


def o_path(svg):
    shapes = re.findall(r'<(?:path|circle|polygon|rect)\b[^>]*/>', svg)
    d = re.search(r'\sd="([^"]+)"', shapes[O_INDEX]).group(1)
    return d


def clearspace(name):
    svg = open(os.path.join(LOGOS, f'{name}-white.svg'), encoding='utf-8').read()
    (_, _, W, H), body = inner(svg)
    if name == 'monogram':  # the O is drawn from the wordmark's O, scaled into the ring
        import make_monogram
        s, _, _, ow, oh = make_monogram.geometry()
        ox, oy = O_BOX['wordmark'][:2]
        d = o_path(open(os.path.join(LOGOS, 'wordmark-white.svg'), encoding='utf-8').read())
    else:
        s = 1
        ox, oy, ow, oh = O_BOX[name]
        d = o_path(svg)
    X = oh
    pad = 0.75 * X
    vx, vy, vw, vh = -X - pad, -X - pad, W + 2 * (X + pad), H + 2 * (X + pad)
    o = lambda x, y: f'<path d="{d}" transform="translate({x:.3f},{y:.3f}) scale({s:.5f}) translate({-ox:.3f},{-oy:.3f})"/>'
    o90 = lambda x, y: f'<path d="{d}" transform="translate({x + oh:.3f},{y:.3f}) rotate(90) scale({s:.5f}) translate({-ox:.3f},{-oy:.3f})"/>'
    marks = ''.join([
        o(0, -X), o90(-X, 0),                      # top-left: above and beside the logo
        o(W - ow, H), o90(W, H - ow),              # bottom-right
    ])
    sw = X * 0.035
    return (f'<svg class="diagram" viewBox="{vx:.2f} {vy:.2f} {vw:.2f} {vh:.2f}" role="img" aria-label="Clear space around the {name.replace("-", " ")}">'
            f'<rect x="{vx:.2f}" y="{vy:.2f}" width="{vw:.2f}" height="{vh:.2f}" fill="#10233F"/>'
            f'<g fill="#FFFFFF" opacity=".14">{marks}</g>'
            f'<rect x="{-X:.2f}" y="{-X:.2f}" width="{W + 2 * X:.2f}" height="{H + 2 * X:.2f}" fill="none" stroke="#FFFFFF" stroke-opacity=".32" stroke-width="{sw:.2f}" stroke-dasharray="{sw * 4:.2f} {sw * 3:.2f}"/>'
            f'<rect x="0" y="0" width="{W:.2f}" height="{H:.2f}" fill="none" stroke="#FFFFFF" stroke-opacity=".22" stroke-width="{sw:.2f}" stroke-dasharray="{sw * 2:.2f} {sw * 2:.2f}"/>'
            f'<g>{body}</g>'
            f'<text x="{ow / 2:.2f}" y="{-X / 2:.2f}" text-anchor="middle" dominant-baseline="central" font-size="{X * 0.36:.2f}" fill="#FFFFFF" fill-opacity=".6">X</text>'
            f'</svg>')


def wave(width=171.0, height=30.0):
    """The carton wave: Soft Silver behind Ice Blue, same curves as the packs (base, amplitude, period, phase in mm)."""
    def band(base, amp, period, phase, colour):
        pts = [(x, height - (base + amp * math.sin(2 * math.pi * x / period + phase))) for x in [i * 0.5 for i in range(int(width * 2) + 1)]]
        d = 'M' + ' L'.join(f'{x:.1f},{y:.2f}' for x, y in pts) + f' L{width:.1f},{height:.1f} L0,{height:.1f}Z'
        return f'<path d="{d}" fill="{colour}"/>'
    return (f'<svg class="wave" viewBox="0 0 {width:g} {height:g}" preserveAspectRatio="none" aria-hidden="true">'
            + band(15, 3.5, 120, 3.35, '#C6CDD5') + band(11, 4, 95, 1.33, '#DCEAF4') + '</svg>')


def main():
    os.makedirs(OUT, exist_ok=True)
    for name in list(O_BOX) + ['monogram']:
        open(os.path.join(OUT, f'clearspace-{name}.svg'), 'w', encoding='utf-8').write(clearspace(name))
    open(os.path.join(OUT, 'wave.svg'), 'w', encoding='utf-8').write(wave())
    print('diagrams written to', OUT)


if __name__ == '__main__':
    main()
