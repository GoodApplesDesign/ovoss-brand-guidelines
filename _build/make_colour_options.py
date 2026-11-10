"""Builds colour-options.html: the palette options side by side, for Greg to choose from.

Everything comes from _build/studio/palettes.json, so a colour change there flows through:
    python3 _build/studio/recolour.py       # pack textures per palette
    node _build/studio/render.mjs out/options "range~tex=<key>~light=<light hex>:1600x1000"
    python3 _build/make_colour_options.py   # this page (also writes the option images from the renders)

Desktop shows the options as columns, row by row (products, core colours, the range), so there is
nothing to switch. On a phone one column shows at a time, picked from a bar that stays at the top.
The page is unlisted: it isn't in the guidelines nav and it's noindex.
"""
import json, os, re, html

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CFG = json.load(open(os.path.join(HERE, 'studio', 'palettes.json'), encoding='utf-8'))
PAL = CFG['palettes']
KEYS = list(PAL)

RANGE_NOTE = {}


def swatches(p):
    """(colour, name) pairs for the core row. Light palettes show their lid tint and paper too."""
    if 'solid' in p:
        return [(p['primary'], p['names']['primary']), (p['solid']['bg'], p['names']['solid']), (p['accent'], p['names']['accent']),
                (p['light'], p['names']['light']), (p['paper'], p['names']['paper'])]
    return [(p[r], p['names'][r]) for r in ('primary', 'accent', 'light', 'band')] + [('#FFFFFF', 'White')]


def light_edge(hexcol):
    h = hexcol.lstrip('#'); r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b > 200


def wordmark_symbol():
    svg = open(os.path.join(ROOT, 'assets/logo/range/wordmark-implant-care-on-dark.svg'), encoding='utf-8').read()
    vb = re.search(r'viewBox="([^"]+)"', svg).group(1)
    paths = ''.join(f'<path style="fill:var({"--wl" if f.upper() == "#FFFFFF" else "--wv"})" d="{d}"/>'
                    for f, d in re.findall(r'<path fill="([^"]+)" d="([^"]+)"', svg))
    return vb, f'<symbol id="wm" viewBox="{vb}">{paths}</symbol>'


VB, SYMBOL = wordmark_symbol()


def write_images():
    """Option images from the renders: full frame for the click-through, and a 5:4 crop around the products."""
    try:
        from PIL import Image
    except ImportError:
        return
    out = os.path.join(HERE, 'studio', 'out', 'options')
    for key in KEYS:
        src = os.path.join(out, f'range_tex_{key}_light_{PAL[key]["light"].lstrip("#").upper()}.png')
        if not os.path.exists(src):
            continue
        im = Image.open(src).convert('RGB')
        w, h = im.size
        dst = os.path.join(ROOT, 'assets', 'img', 'options', key)
        im.resize((2000, 1250), Image.LANCZOS).save(dst + '.jpg', quality=86, optimize=True, progressive=True)
        cw, ch = round(w * 0.703), round(h * 0.9)   # 5:4 around the products, which sit centred
        box = ((w - cw) // 2, round(h * 0.045), (w - cw) // 2 + cw, round(h * 0.045) + ch)
        im.crop(box).resize((1250, 1000), Image.LANCZOS).save(dst + '-crop.jpg', quality=86, optimize=True, progressive=True)


write_images()


def wm(letters, v, label):
    return f'<svg class="wm" viewBox="{VB}" role="img" aria-label="{label}" style="--wl:{letters};--wv:{v}"><use href="#wm"/></svg>'


def cell(key, inner, cls=''):
    return f'<div class="cell {cls}" data-col="{key}">{inner}</div>'


heads, shots, cores, ranges = [], [], [], []
for i, key in enumerate(KEYS):
    p = PAL[key]
    strip = ''.join(f'<i style="background:{l if "solid" in p else d}"></i>' for d, l in p['ranges'].values())
    heads.append(f'<button class="opt" data-col="{key}" aria-pressed="{"true" if i == 0 else "false"}">'
                 f'<span class="opt-name">{html.escape(p["name"])}</span>'
                 f'<span class="opt-strip" aria-hidden="true">{strip}</span></button>')
    shots.append(cell(key,
        f'<a class="shot" href="assets/img/options/{key}.jpg" target="_blank" rel="noopener">'
        f'<img src="assets/img/options/{key}-crop.jpg" alt="Implant Care toothpaste carton, mouthwash and tube in the {html.escape(p["name"])} palette" width="1250" height="1000"></a>'
        f'<p class="note">{html.escape(p["note"])}</p>'))
    sw = ''.join(f'<div class="sw"><i style="background:{c}"{" class=edge" if light_edge(c) else ""}></i>'
                 f'<b>{nm}</b><span>{c}</span></div>' for c, nm in swatches(p))
    cores.append(cell(key, f'<div class="sws">{sw}</div>'))
    lite = 'solid' in p   # light palettes: the block is the pale tint, logo in the core colour, V in the range's deep tone
    rows = ''.join(
        (f'<div class="rr"><div class="rr-d" style="background:{l}">{wm(p["primary"], d, f"Ovoss logo on {name}")}</div>'
         f'<div class="rr-l" style="background:{d}"></div><div class="rr-t"><b>{name}</b><span>{l} &middot; {d}</span></div></div>') if lite else
        (f'<div class="rr"><div class="rr-d" style="background:{d}">{wm("#FFFFFF", l, f"Ovoss logo on {name}")}</div>'
         f'<div class="rr-l" style="background:{l}"></div><div class="rr-t"><b>{name}</b><span>{d} &middot; {l}</span></div></div>')
        for name, (d, l) in p['ranges'].items())
    note = f'<p class="note small">{RANGE_NOTE[key]}</p>' if key in RANGE_NOTE else ''
    ranges.append(cell(key, rows + note, 'rrs'))

n = len(KEYS)
page = f'''<!doctype html>
<html lang="en-AU">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Colour options | Ovoss</title>
<meta name="description" content="Colour palette options for Ovoss, side by side on the Implant Care packs and across the range.">
<meta name="robots" content="noindex, nofollow">
<link rel="icon" href="assets/logo/svg/monogram-navy.svg" type="image/svg+xml">
<link rel="stylesheet" href="assets/css/site.css">
<style>
  body {{ background: #fff; }}
  .bar {{ position: sticky; top: 0; z-index: 10; display: flex; align-items: center; justify-content: space-between; height: 56px; padding: 0 var(--gut); background: #fff; border-bottom: 1px solid var(--line); }}
  .bar img {{ width: 80px; height: auto; }}
  .bar a {{ font-size: 14px; color: var(--muted); text-decoration: none; }}
  .bar a:hover {{ color: var(--ink); }}
  .wrap {{ max-width: 1360px; margin: 0 auto; padding: 0 var(--gut); }}
  .intro {{ padding: clamp(32px, 5vw, 60px) 0 clamp(20px, 3vw, 32px); display: grid; gap: 10px; }}
  .intro h1 {{ margin: 0; font-weight: 600; text-transform: uppercase; letter-spacing: .14em; font-size: clamp(24px, 3vw, 36px); line-height: 1.1; }}
  .intro p {{ margin: 0; max-width: 40em; }}
  .intro p + p {{ color: var(--muted); font-size: 14px; }}

  .cmp {{ display: grid; grid-template-columns: repeat({n}, minmax(0, 1fr)); column-gap: clamp(16px, 2.4vw, 36px); }}
  .heads {{ grid-column: 1 / -1; display: grid; grid-template-columns: subgrid; position: sticky; top: 56px; z-index: 5; background: rgba(255,255,255,.94); backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px); padding: 14px 0 12px; border-bottom: 1px solid var(--line); }}
  .opt {{ font: inherit; color: inherit; background: none; border: 0; padding: 0; text-align: left; display: grid; gap: 8px; cursor: default; }}
  .opt-name {{ font-weight: 600; text-transform: uppercase; letter-spacing: .14em; font-size: 15px; }}
  .opt-strip {{ display: flex; gap: 3px; }}
  .opt-strip i {{ flex: 1; height: 6px; border-radius: 2px; }}
  .row-label {{ grid-column: 1 / -1; margin: clamp(28px, 3.5vw, 44px) 0 14px; font-family: var(--serif); font-style: italic; font-size: 21px; line-height: 1.3; }}
  .cell {{ min-width: 0; align-self: start; }}
  .shot {{ display: block; border-radius: 8px; overflow: hidden; background: var(--studio); margin-top: 20px; }}
  .shot img {{ width: 100%; aspect-ratio: 5 / 4; object-fit: cover; transition: transform .3s; }}
  .shot:hover img {{ transform: scale(1.02); }}
  .note {{ margin: 12px 0 0; color: var(--muted); font-size: 15px; line-height: 1.5; }}
  .note.small {{ font-size: 13px; margin-top: 10px; }}
  .sws {{ display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 6px; }}
  .sw {{ display: grid; gap: 2px; font-size: 12px; line-height: 1.35; align-content: start; }}
  .sw i {{ display: block; height: 56px; border-radius: 6px; margin-bottom: 6px; }}
  .sw i.edge {{ box-shadow: inset 0 0 0 1px var(--line); }}
  .sw b {{ font-weight: 600; }}
  .sw span {{ color: var(--faint); font-variant-numeric: tabular-nums; }}
  .rrs {{ display: grid; gap: 8px; align-content: start; }}
  .rr {{ display: grid; grid-template-columns: minmax(0, 1fr) 22% minmax(0, 1.1fr); align-items: stretch; border-radius: 6px; overflow: hidden; box-shadow: inset 0 0 0 1px var(--line); }}
  .rr-d {{ display: grid; place-items: center; height: 54px; }}
  .wm {{ width: 66%; max-width: 110px; height: auto; }}
  .rr-t {{ display: grid; align-content: center; padding: 0 12px; font-size: 13px; line-height: 1.35; }}
  .rr-t b {{ font-weight: 600; }}
  .rr-t span {{ color: var(--faint); font-size: 12px; font-variant-numeric: tabular-nums; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
  .foot {{ margin-top: 56px; padding: 24px 0 44px; border-top: 1px solid var(--line); color: var(--faint); font-size: 13px; }}

  /* phone: one column at a time, picked from the bar that stays at the top */
  @media (max-width: 820px) {{
    .cmp {{ grid-template-columns: minmax(0, 1fr); }}
    .heads {{ grid-template-columns: repeat({n}, minmax(0, 1fr)); gap: 6px; padding: 10px 0; }}
    .opt {{ cursor: pointer; padding: 9px 10px 10px; border-radius: 8px; border: 1px solid var(--line); gap: 7px; }}
    .opt[aria-pressed="true"] {{ border-color: var(--ink); box-shadow: inset 0 0 0 1px var(--ink); }}
    .opt-name {{ font-size: 12px; letter-spacing: .1em; }}
    .opt-strip i {{ height: 5px; }}
    .cmp .cell:not(.on) {{ display: none; }}
    .row-label {{ margin-top: 30px; }}
  }}
</style>
</head>
<body>
<svg width="0" height="0" style="position:absolute" aria-hidden="true">{SYMBOL}</svg>
<header class="bar"><img src="assets/logo/svg/wordmark-navy.svg" alt="Ovoss" width="104" height="23"><a href="index.html">Brand guidelines</a></header>
<main class="wrap">
  <div class="intro">
    <h1>Colour options</h1>
    <p>{n} palettes for Ovoss, side by side. Only the colour changes. The logo, type and layout stay as they are.</p>
    <p>Colours on screen are a guide. The chosen palette gets checked on a printed proof.</p>
  </div>
  <div class="cmp" id="cmp">
    <div class="heads">{"".join(heads)}</div>
    {"".join(shots)}
    <h2 class="row-label">Core colours</h2>
    {"".join(cores)}
    <h2 class="row-label">Across the range</h2>
    {"".join(ranges)}
  </div>
  <footer class="foot">Prepared by Good Apples for Cuross Health &middot; November 2026</footer>
</main>
<script>
(() => {{
  const opts = [...document.querySelectorAll('.opt')], cells = [...document.querySelectorAll('.cmp .cell')];
  const show = key => {{
    opts.forEach(o => o.setAttribute('aria-pressed', o.dataset.col === key));
    cells.forEach(c => c.classList.toggle('on', c.dataset.col === key));
  }};
  opts.forEach(o => o.addEventListener('click', () => show(o.dataset.col)));
  const start = location.hash.slice(1);
  show(opts.some(o => o.dataset.col === start) ? start : opts[0].dataset.col);
}})();
</script>
</body>
</html>
'''
open(os.path.join(ROOT, 'colour-options.html'), 'w', encoding='utf-8').write(page)
print('built colour-options.html with', n, 'options:', ', '.join(KEYS))
