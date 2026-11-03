"""Builds assets/downloads/: the logo pack (SVG + transparent PNG), Adobe swatches (.ase) and CSS colour tokens.

Run:  python3 _build/make_downloads.py   (needs Google Chrome for the PNGs)
"""
import os, re, shutil, struct, subprocess, tempfile, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LOGOS = os.path.join(ROOT, 'assets', 'logo', 'svg')
DL = os.path.join(ROOT, 'assets', 'downloads')
PNG = os.path.join(HERE, 'png')
CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'

# name, hex, (C, M, Y, K) as converted by Illustrator's colour settings
CORE = [('Deep Navy', '#10233F', (97, 84, 46, 52)), ('Slate Grey', '#6F7D8A', (60, 44, 36, 6)), ('Ice Blue', '#DCEAF4', (12, 3, 1, 0)),
        ('Soft Silver', '#C6CDD5', (22, 14, 11, 0)), ('Mist White', '#F7F9FB', (2, 1, 0, 0))]
RANGE = [('Perio Gum Rose', '#A4546F', (34, 77, 39, 7)), ('Perio Gum Pink', '#F4E1E8', (2, 12, 2, 0)),
         ('Daily Green', '#2E5D4F', (81, 43, 67, 31)), ('Daily Mint', '#D8E8DE', (15, 2, 13, 0)),
         ('Restore Teal', '#1F6B72', (86, 43, 48, 17)), ('Restore Aqua', '#DCEFEF', (13, 0, 5, 0)),
         ('FPD Violet (reserved)', '#524677', (78, 81, 27, 11)), ('FPD Lilac (reserved)', '#E4E1EE', (9, 9, 1, 0))]
PNG_WIDTH = {'wordmark': 2400, 'implant-care': 2400, 'brand-line': 2400, 'monogram': 2000}


def render_png(svg_path, out_path, width):
    svg = open(svg_path, encoding='utf-8').read()
    vb = [float(v) for v in re.search(r'viewBox="([^"]+)"', svg).group(1).split()]
    height = round(width * vb[3] / vb[2])
    with tempfile.TemporaryDirectory() as tmp:
        page = os.path.join(tmp, 'p.html')
        open(page, 'w').write(f'<!doctype html><html><body style="margin:0;background:transparent"><img src="file://{svg_path}" style="display:block;width:{width}px;height:{height}px"></body></html>')
        subprocess.run([CHROME, '--headless=new', '--hide-scrollbars', '--allow-file-access-from-files', '--default-background-color=00000000',
                        f'--user-data-dir={tmp}/prof', f'--window-size={width},{height}', '--virtual-time-budget=2000', f'--screenshot={out_path}', f'file://{page}'],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)


def ase(groups):
    def utf16(s):
        return struct.pack('>H', len(s) + 1) + s.encode('utf-16-be') + b'\x00\x00'
    blocks = []
    for gname, colours in groups:
        blocks.append(struct.pack('>HI', 0xC001, len(utf16(gname))) + utf16(gname))
        for name, model, vals in colours:
            body = utf16(name) + model.encode('ascii') + b''.join(struct.pack('>f', v) for v in vals) + struct.pack('>H', 2)
            blocks.append(struct.pack('>HI', 0x0001, len(body)) + body)
        blocks.append(struct.pack('>HI', 0xC002, 0))
    return b'ASEF' + struct.pack('>HHI', 1, 0, len(blocks)) + b''.join(blocks)


def rgb(h):
    return tuple(int(h[i:i + 2], 16) / 255 for i in (1, 3, 5))


def main():
    os.makedirs(DL, exist_ok=True)
    os.makedirs(PNG, exist_ok=True)
    svgs = sorted(f for f in os.listdir(LOGOS) if f.endswith('.svg'))
    for f in svgs:
        base = f[:-4]
        render_png(os.path.join(LOGOS, f), os.path.join(PNG, base + '.png'), PNG_WIDTH[base.rsplit('-', 1)[0]])
    def pack(zname, bases):
        with zipfile.ZipFile(os.path.join(DL, zname), 'w', zipfile.ZIP_DEFLATED) as z:
            for b in bases:
                z.write(os.path.join(LOGOS, b + '.svg'), f'SVG/Ovoss-{b}.svg')
                z.write(os.path.join(PNG, b + '.png'), f'PNG/Ovoss-{b}.png')
    allb = [f[:-4] for f in svgs]
    pack('Ovoss-logo-pack.zip', allb)
    for lock in PNG_WIDTH:
        pack(f'Ovoss-{lock}.zip', [b for b in allb if b.startswith(lock + '-')])
    colours = CORE + RANGE
    open(os.path.join(DL, 'Ovoss-colours.ase'), 'wb').write(ase([
        ('Ovoss RGB', [(n, 'RGB ', rgb(h)) for n, h, _ in colours]),
        ('Ovoss CMYK', [(n, 'CMYK', tuple(v / 100 for v in c)) for n, _, c in colours]),
    ]))
    css = '/* Ovoss colour tokens */\n:root {\n' + ''.join(f'  --ovoss-{re.sub(r"[^a-z0-9]+", "-", n.lower()).strip("-")}: {h};\n' for n, h, _ in colours) + '}\n'
    open(os.path.join(DL, 'Ovoss-colours.css'), 'w').write(css)
    for f in sorted(os.listdir(DL)):
        print('  ', f, os.path.getsize(os.path.join(DL, f)), 'bytes')


if __name__ == '__main__':
    main()
