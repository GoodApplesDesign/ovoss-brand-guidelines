"""Builds colour-options.html: the four palette options side by side, for Greg to choose from.

Everything comes from _build/studio/palettes.json, so a colour change there flows through:
    python3 _build/studio/recolour.py      # pack textures per palette
    node _build/studio/render.mjs ...       # renders (see the README in _build/studio)
    python3 _build/make_colour_options.py   # this page

The page is unlisted: it isn't in the guidelines nav and it's noindex.
"""
import json, os, re, html

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CFG = json.load(open(os.path.join(HERE, 'studio', 'palettes.json'), encoding='utf-8'))

COPY = {
    'a-original': 'The current palette. Deep navy does most of the work, with ice blue and silver.',
    'b-soft': 'Navy lifts to a dusk blue and the silver warms to pearl. Calmer, closer to premium skincare.',
    'c-bright': 'A clear clinical blue with an aqua accent. Fresh, and mostly white.',
    'd-periwinkle': 'Blue shifts toward violet, with a lilac mist. Soft, but still clinical.',
}
RANGE_NOTE = {
    'd-periwinkle': 'Potential FPD moves to a deep blue, so it doesn&rsquo;t sit next to Implant Care.',
}
ROLE_USE = {'primary': 'Logo, type, lid', 'accent': 'The V, claims', 'light': 'The wave', 'band': 'The wave'}


def wordmark_symbol():
    svg = open(os.path.join(ROOT, 'assets/logo/range/wordmark-implant-care-on-dark.svg'), encoding='utf-8').read()
    vb = re.search(r'viewBox="([^"]+)"', svg).group(1)
    paths = []
    for fill, d in re.findall(r'<path fill="([^"]+)" d="([^"]+)"', svg):
        var = '--wl' if fill.upper() == '#FFFFFF' else '--wv'
        paths.append(f'<path style="fill:var({var})" d="{d}"/>')
    return vb, f'<symbol id="wm" viewBox="{vb}">{"".join(paths)}</symbol>'


def wm(letters, v, label):
    return (f'<svg class="wm" viewBox="{VB}" role="img" aria-label="{label}" style="--wl:{letters};--wv:{v}">'
            f'<use href="#wm"/></svg>')


VB, SYMBOL = wordmark_symbol()
keys = list(CFG['palettes'])

cards, panels = [], []
for i, key in enumerate(keys):
    p = CFG['palettes'][key]
    letter = 'ABCD'[i]
    strip = ''.join(f'<i style="background:{d}"></i>' for d, _ in p['ranges'].values())
    cards.append(
        f'<button class="opt-card" role="tab" id="tab-{key}" aria-controls="{key}" aria-selected="{"true" if i == 0 else "false"}" tabindex="{0 if i == 0 else -1}" data-key="{key}">'
        f'<img src="assets/img/options/{key}-thumb.jpg" alt="" width="720" height="450" loading="eager">'
        f'<span class="oc-name"><b>{letter}</b>{html.escape(p["name"])}</span>'
        f'<span class="oc-strip" aria-hidden="true">{strip}</span></button>')

    chips = ''.join(
        f'<div class="cc"><div class="cc-c{" edge" if role in ("light", "band") else ""}" style="background:{p[role]}"></div>'
        f'<div class="cc-t"><b>{p["names"][role]}</b><span>{p[role]}</span><small>{ROLE_USE[role]}</small></div></div>'
        for role in ('primary', 'accent', 'light', 'band'))

    tiles = ''.join(
        f'<div class="rt">'
        f'<div class="rt-dark" style="background:{d}">{wm("#FFFFFF", l, f"Ovoss wordmark on {name} dark")}</div>'
        f'<div class="rt-light" style="background:{l}"></div>'
        f'<div class="rt-white">{wm(p["primary"], d, f"Ovoss wordmark in {name} colours on white")}</div>'
        f'<div class="rt-t"><b>{name}</b><span>{d} &middot; {l}</span></div></div>'
        for name, (d, l) in p['ranges'].items())

    note = f'<p class="range-note">{RANGE_NOTE[key]}</p>' if key in RANGE_NOTE else ''
    panels.append(
        f'<section class="opt-panel" role="tabpanel" id="{key}" aria-labelledby="tab-{key}"{"" if i == 0 else " hidden"}>'
        f'<div class="op-head"><h2><span>{letter}</span>{html.escape(p["name"])}</h2><p>{COPY[key]}</p></div>'
        f'<figure class="hero"><img src="assets/img/options/{key}.jpg" alt="Ovoss Implant Care toothpaste carton, mouthwash and tube in the {html.escape(p["name"])} palette" width="2000" height="1250" loading="lazy"></figure>'
        f'<h3>Core colours</h3><div class="ccs">{chips}</div>'
        f'<h3>Across the range</h3><p class="op-sub">The logo on each range&rsquo;s dark colour, and on white. Each range keeps its colour family and takes on this option&rsquo;s tone.</p>'
        f'<div class="tiles">{tiles}</div>{note}</section>')

page = f'''<!doctype html>
<html lang="en-AU">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Colour options | Ovoss</title>
<meta name="description" content="Four colour palettes for Ovoss, compared on the Implant Care packs and across the range.">
<meta name="robots" content="noindex, nofollow">
<link rel="icon" href="assets/logo/svg/monogram-navy.svg" type="image/svg+xml">
<link rel="stylesheet" href="assets/css/site.css">
<style>
  body {{ background: #fff; }}
  .co-bar {{ position: sticky; top: 0; z-index: 10; display: flex; align-items: center; justify-content: space-between; gap: 16px; height: 60px; padding: 0 var(--gut); background: rgba(255,255,255,.9); backdrop-filter: blur(14px); -webkit-backdrop-filter: blur(14px); border-bottom: 1px solid var(--line); }}
  .co-bar img {{ width: 84px; height: auto; }}
  .co-bar a {{ font-size: 14px; color: var(--muted); text-decoration: none; }}
  .co-bar a:hover {{ color: var(--ink); }}
  .co {{ max-width: 1240px; margin: 0 auto; padding: clamp(36px, 6vw, 72px) var(--gut) 80px; }}
  .co-head {{ display: grid; gap: 14px; margin-bottom: clamp(28px, 4vw, 44px); }}
  .co-head h1 {{ margin: 0; font-weight: 600; text-transform: uppercase; letter-spacing: .14em; font-size: clamp(26px, 3.2vw, 40px); line-height: 1.1; }}
  .co-head p {{ margin: 0; max-width: 36em; font-size: clamp(16px, 1.3vw, 18px); line-height: 1.55; }}
  .co-head p + p {{ color: var(--muted); font-size: 15px; }}

  .opt-cards {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; }}
  .opt-card {{ font: inherit; color: inherit; text-align: left; background: #fff; border: 1px solid var(--line); border-radius: 10px; padding: 0 0 12px; cursor: pointer; overflow: hidden; display: grid; gap: 10px; transition: border-color .15s, box-shadow .15s; }}
  .opt-card img {{ width: 100%; aspect-ratio: 16 / 10; object-fit: cover; background: var(--studio); }}
  .opt-card:hover {{ border-color: rgba(16,35,63,.3); }}
  .opt-card[aria-selected="true"] {{ border-color: var(--ink); box-shadow: 0 0 0 1px var(--ink); }}
  .oc-name {{ display: flex; align-items: baseline; gap: 8px; padding: 0 14px; font-weight: 600; font-size: 15px; letter-spacing: .02em; }}
  .oc-name b {{ font-weight: 600; color: var(--muted); }}
  .oc-strip {{ display: flex; gap: 3px; padding: 0 14px; }}
  .oc-strip i {{ flex: 1; height: 8px; border-radius: 2px; }}

  .opt-panel {{ margin-top: clamp(36px, 5vw, 60px); }}
  .op-head {{ display: grid; gap: 8px; margin-bottom: 22px; }}
  .op-head h2 {{ margin: 0; font-size: 18px; font-weight: 600; text-transform: uppercase; letter-spacing: .14em; display: flex; gap: 12px; }}
  .op-head h2 span {{ color: var(--muted); }}
  .op-head p {{ margin: 0; max-width: 40em; color: var(--muted); }}
  .hero {{ margin: 0 0 clamp(36px, 5vw, 56px); border-radius: 10px; overflow: hidden; background: var(--studio); }}
  .hero img {{ width: 100%; }}
  .opt-panel h3 {{ margin: 0 0 6px; }}
  .op-sub {{ color: var(--muted); max-width: 40em; margin: 0 0 18px; font-size: 15px; }}
  .ccs {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin: 16px 0 clamp(36px, 5vw, 56px); }}
  .cc-c {{ height: 84px; border-radius: 8px; }}
  .cc-c.edge {{ box-shadow: inset 0 0 0 1px var(--line); }}
  .cc-t {{ display: grid; padding-top: 8px; font-size: 14px; line-height: 1.45; }}
  .cc-t span {{ color: var(--muted); font-variant-numeric: tabular-nums; }}
  .cc-t small {{ color: var(--faint); font-size: 13px; }}
  .tiles {{ display: grid; grid-template-columns: repeat(5, 1fr); gap: 12px; }}
  .rt {{ display: grid; grid-template-rows: auto 10px auto auto; border-radius: 8px; overflow: hidden; box-shadow: inset 0 0 0 1px var(--line); }}
  .rt-dark, .rt-white {{ display: grid; place-items: center; aspect-ratio: 16 / 9; }}
  .rt-white {{ background: #fff; }}
  .wm {{ width: 58%; height: auto; }}
  .rt-t {{ display: grid; padding: 10px 12px 12px; font-size: 14px; line-height: 1.4; border-top: 1px solid var(--line); }}
  .rt-t span {{ color: var(--faint); font-size: 12.5px; font-variant-numeric: tabular-nums; }}
  .range-note {{ margin: 14px 0 0; color: var(--muted); font-size: 14px; }}
  .co-foot {{ max-width: 1240px; margin: 0 auto; padding: 28px var(--gut) 48px; border-top: 1px solid var(--line); color: var(--faint); font-size: 13px; }}

  @media (max-width: 900px) {{
    .opt-cards {{ grid-template-columns: repeat(2, 1fr); }}
    .ccs {{ grid-template-columns: repeat(2, 1fr); }}
    .tiles {{ grid-template-columns: repeat(3, 1fr); }}
  }}
  @media (max-width: 560px) {{
    .tiles {{ grid-template-columns: repeat(2, 1fr); }}
    .opt-card {{ gap: 8px; padding-bottom: 10px; }}
    .oc-name, .oc-strip {{ padding: 0 10px; }}
    .oc-name {{ font-size: 14px; }}
  }}
</style>
</head>
<body>
<svg width="0" height="0" style="position:absolute" aria-hidden="true">{SYMBOL}</svg>
<header class="co-bar"><img src="assets/logo/svg/wordmark-navy.svg" alt="Ovoss" width="104" height="23"><a href="index.html">Brand guidelines</a></header>
<main class="co">
  <div class="co-head">
    <h1>Colour options</h1>
    <p>Four palettes for Ovoss, shown on the Implant Care packs and across the range. Only the colour changes. The logo, type and layout stay as they are.</p>
    <p>Pick an option to see it in full. Colours on screen are a guide, and the chosen palette gets checked on a printed proof.</p>
  </div>
  <div class="opt-cards" role="tablist" aria-label="Colour options">
    {"".join(cards)}
  </div>
  {"".join(panels)}
</main>
<footer class="co-foot">Prepared by Good Apples for Cuross Health &middot; November 2026</footer>
<script>
(() => {{
  const tabs = [...document.querySelectorAll('.opt-card')];
  const show = (key, focus) => {{
    tabs.forEach(t => {{ const on = t.dataset.key === key; t.setAttribute('aria-selected', on); t.tabIndex = on ? 0 : -1; if (on && focus) t.focus(); }});
    document.querySelectorAll('.opt-panel').forEach(p => p.hidden = p.id !== key);
    history.replaceState(null, '', '#' + key);
  }};
  tabs.forEach((t, i) => {{
    t.addEventListener('click', () => show(t.dataset.key));
    t.addEventListener('keydown', e => {{
      const d = {{ ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1 }}[e.key];
      if (d) {{ e.preventDefault(); show(tabs[(i + d + tabs.length) % tabs.length].dataset.key, true); }}
    }});
  }});
  const start = location.hash.slice(1);
  if (tabs.some(t => t.dataset.key === start)) show(start);
}})();
</script>
</body>
</html>
'''
open(os.path.join(ROOT, 'colour-options.html'), 'w', encoding='utf-8').write(page)
print('built colour-options.html')
