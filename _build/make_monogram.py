"""Builds the monogram: the O from the OVOSS wordmark inside a thin ring (after the Oravoss "A" monogram).

Run:  python3 _build/make_monogram.py   (before make_diagrams.py and make_downloads.py)
Writes assets/logo/svg/monogram-navy.svg and monogram-white.svg.
"""
import os, re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LOGOS = os.path.join(ROOT, 'assets', 'logo', 'svg')
O_INDEX = 0                                   # the O is the first shape in the v2 wordmark SVG
O_BOX = (0.0, 1.136, 30.884, 30.218)          # its bounds in the v2 wordmark (x, y, w, h)
SIZE = 100                                    # viewBox, tight to the outside of the ring
RING = 4.6                                    # ring weight, % of the diameter
O_HEIGHT = 44                                 # O height, % of the diameter


def o_path():
    svg = open(os.path.join(LOGOS, 'wordmark-navy.svg'), encoding='utf-8').read()
    shapes = re.findall(r'<(?:path|circle|polygon|rect)\b[^>]*/>', svg)
    return re.search(r'\sd="([^"]+)"', shapes[O_INDEX]).group(1)


def geometry():
    """Where the O sits in the monogram: (scale, x, y, w, h), used by make_diagrams.py for clear space."""
    ox, oy, ow, oh = O_BOX
    s = O_HEIGHT / oh
    w, h = ow * s, oh * s
    return s, (SIZE - w) / 2, (SIZE - h) / 2, w, h


def svg(colour):
    ox, oy, _, _ = O_BOX
    s, x, y, _, _ = geometry()
    r = SIZE / 2 - RING / 2
    return (f'<svg width="{SIZE}" height="{SIZE}" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {SIZE} {SIZE}">'
            f'<circle cx="{SIZE / 2}" cy="{SIZE / 2}" r="{r:.3f}" fill="none" stroke="{colour}" stroke-width="{RING}"/>'
            f'<path fill="{colour}" transform="translate({x:.3f},{y:.3f}) scale({s:.5f}) translate({-ox},{-oy})" d="{o_path()}"/>'
            f'</svg>\n')


def main():
    for name, colour in (('navy', '#10233F'), ('white', '#FFFFFF')):
        open(os.path.join(LOGOS, f'monogram-{name}.svg'), 'w', encoding='utf-8').write(svg(colour))
    print('monogram written')


if __name__ == '__main__':
    main()
