"""Builds the Bright palette preview for the guidelines site.

The site is written in the Original palette. A switch pinned to every page (site.js) swaps it to Bright
on the fly: colours, values, names, logos and product renders. This script makes what that needs:

- assets/bright/logo/... and assets/bright/img/dentist-mark.svg: the SVGs with the colours swapped
- assets/bright/img/front-panel.jpg: the flat carton front, recoloured
- assets/js/palette.js: the swap table (hex, RGB, CMYK, names, and which files have a Bright version)

The product renders come from the studio: render with ~tex=bright~light=DDF1FB into out/bright, then
`python3 _build/studio/finish.py bright` writes assets/bright/img/*.jpg.

Run:  python3 _build/make_bright.py   (then python3 _build/build.py)
"""
import glob, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CFG = json.load(open(os.path.join(HERE, 'studio', 'palettes.json'), encoding='utf-8'))
SWAP = CFG['site_swap']
MISUSE_WRONG = '#E8833A'   # the "recolour it" don't: blue is on-brand in Bright, so it shows an orange instead


def rgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


HEX = {s['from'].upper(): s['to'].upper() for s in SWAP}

# the CMYK the Original values are listed with on the site (same as make_downloads.py)
CMYK_FROM = {'#10233F': (97, 84, 46, 52), '#6F7D8A': (60, 44, 36, 6), '#DCEAF4': (12, 3, 1, 0), '#C6CDD5': (22, 14, 11, 0),
             '#A4546F': (34, 77, 39, 7), '#F4E1E8': (2, 12, 2, 0), '#2E5D4F': (81, 43, 67, 31), '#D8E8DE': (15, 2, 13, 0),
             '#1F6B72': (86, 43, 48, 17), '#DCEFEF': (13, 0, 5, 0), '#524677': (78, 81, 27, 11), '#E4E1EE': (9, 9, 1, 0)}


def swap_svg(text):
    text = re.sub(r'#[0-9A-Fa-f]{6}\b', lambda m: HEX.get(m.group(0).upper(), m.group(0)), text)
    return text.replace('#2988F8', MISUSE_WRONG).replace('#2988f8', MISUSE_WRONG)


def main():
    files = []
    svgs = glob.glob(os.path.join(ROOT, 'assets', 'logo', '**', '*.svg'), recursive=True) + [os.path.join(ROOT, 'assets', 'img', 'dentist-mark.svg')]
    for src in svgs:
        rel = os.path.relpath(src, os.path.join(ROOT, 'assets'))
        text = open(src, encoding='utf-8').read()
        new = swap_svg(text)
        if new == text:
            continue
        dst = os.path.join(ROOT, 'assets', 'bright', rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        open(dst, 'w', encoding='utf-8').write(new)
        files.append('assets/' + rel.replace(os.sep, '/'))

    # flat carton front: same recolouring as the render textures
    sys.path.insert(0, os.path.join(HERE, 'studio'))
    import numpy as np
    from PIL import Image
    import recolour
    pal = CFG['palettes']['bright']
    dst = np.stack([recolour.rgb('#FFFFFF'), recolour.rgb(pal['primary']), recolour.rgb(pal['light']), recolour.rgb(pal['band']),
                    recolour.rgb(pal['accent']), recolour.rgb('#000000')])
    fp = Image.open(os.path.join(ROOT, 'assets', 'img', 'front-panel.jpg')).convert('RGB')
    out = Image.fromarray(recolour.recolour(np.asarray(fp).astype(np.float32), dst))
    os.makedirs(os.path.join(ROOT, 'assets', 'bright', 'img'), exist_ok=True)
    out.save(os.path.join(ROOT, 'assets', 'bright', 'img', 'front-panel.jpg'), quality=92)
    files.append('assets/img/front-panel.jpg')

    # product renders written by finish.py bright
    for jpg in sorted(glob.glob(os.path.join(ROOT, 'assets', 'bright', 'img', '*.jpg'))):
        rel = 'assets/img/' + os.path.basename(jpg)
        if rel not in files:
            files.append(rel)

    table = {
        'hex': HEX,
        'rgb': {' '.join(map(str, rgb(s['from']))): ' '.join(map(str, rgb(s['to']))) for s in SWAP},
        'rgba': {','.join(map(str, rgb(s['from']))): ','.join(map(str, rgb(s['to']))) for s in SWAP},
        'cmyk': {' '.join(map(str, CMYK_FROM[s['from'].upper()])): ' '.join(map(str, s['cmyk_to'])) for s in SWAP},
        'names': [[s['name_from'], s['name_to']] for s in SWAP if s['name_from'] != s['name_to']] + [['Navy', 'Cobalt'], ['navy', 'cobalt']],
        'files': sorted(files),
        'vars': {'--navy': pal['primary'], '--slate': pal['accent'], '--ice': pal['light'], '--silver': pal['band']},
    }
    js = ('// Made by _build/make_bright.py from _build/studio/palettes.json. Don\'t edit by hand.\n'
          'window.OVOSS_BRIGHT = ' + json.dumps(table, indent=1) + ';\n')
    open(os.path.join(ROOT, 'assets', 'js', 'palette.js'), 'w', encoding='utf-8').write(js)
    print(len(files), 'files with a Bright version;', len(table['names']), 'name swaps')
    sync_site(pal)


def sync_site(pal):
    """Write the Bright values into the CSS overrides, the switch, and the range trim chips on the Colour page."""
    import html as H
    r = pal['ranges']
    core = r['Implant Care'][0]; c = ', '.join(map(str, rgb(core)))
    block = ('/* bright:start (made by _build/make_bright.py) */\n[data-palette="bright"] {\n'
             f"  --navy: {core}; --slate: {pal['accent']}; --ice: {pal['light']}; --silver: {pal['band']};\n"
             f"  --green: {r['Daily Care'][0]}; --mint: {r['Daily Care'][1]}; --rose: {r['Perio Care'][0]}; --gum: {r['Perio Care'][1]}; "
             f"--teal: {r['Restore'][0]}; --aqua: {r['Restore'][1]}; --violet: {r['Potential FPD'][0]}; --lilac: {r['Potential FPD'][1]};\n"
             f"  --muted: rgba({c}, .72); --faint: rgba({c}, .5); --line: rgba({c}, .12);\n}}\n/* bright:end */")
    css_p = os.path.join(ROOT, 'assets', 'css', 'site.css'); css = open(css_p, encoding='utf-8').read()
    if '/* bright:start' in css:
        css = re.sub(r'/\* bright:start.*?/\* bright:end \*/', lambda m: block, css, flags=re.S)
    else:
        css = re.sub(r'\[data-palette="bright"\] \{[^}]*\}', lambda m: block, css, count=1)
    css = re.sub(r'(\.pal-switch button\[data-pal="bright"\]\[aria-pressed="true"\] \{ background: )#[0-9A-Fa-f]{6}', r'\g<1>' + core, css)
    open(css_p, 'w', encoding='utf-8').write(css)
    lay_p = os.path.join(HERE, 'src', 'layout.html'); lay = open(lay_p, encoding='utf-8').read()
    lay = re.sub(r'(data-pal="bright" aria-pressed="false"><i style="background:)#[0-9A-Fa-f]{6}', r'\g<1>' + core, lay)
    open(lay_p, 'w', encoding='utf-8').write(lay)
    col_p = os.path.join(HERE, 'src', 'pages', 'colour.html'); col = open(col_p, encoding='utf-8').read()
    order = iter(['Implant Care', 'Perio Care', 'Daily Care', 'Restore', 'Potential FPD'])
    def chip(m):
        k = next(order); t = r[k][2]
        inner = (f'<div class="rc-chip" style="background:{t}"><span class="n">{pal["trim_names"][k]}</span><span class="v"><span>{t}</span>'
                 f'<span>RGB {" ".join(map(str, rgb(t)))}</span><span>CMYK {" ".join(map(str, pal["trim_cmyk"][k]))}</span></span></div>')
        return f'<div class="rc-trim" data-bright="{H.escape(inner, quote=True)}"></div>'
    col = re.sub(r'<div class="rc-trim" data-bright="[^"]*"></div>', chip, col)
    open(col_p, 'w', encoding='utf-8').write(col)
    print('synced CSS, switch and trim chips:', core, pal['accent'])


if __name__ == '__main__':
    main()
