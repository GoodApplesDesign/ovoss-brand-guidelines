"""Builds the guidelines site: _build/src/pages/*.html + layout.html -> /*.html at the repo root.

Run from anywhere:  python3 _build/build.py
Build order when logos change: make_diagrams.py -> make_downloads.py -> build.py

Page source conventions
- First line: <!-- {"title": "Logo", "intro": "..."} -->   (JSON page meta)
- <section id="x" data-nav="Label"> ... </section>         becomes a sidebar sub-link
- <!--include:name-->                                       inlines _build/src/partials/name.svg (made by make_diagrams.py)
"""
import json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

PAGES = [  # (slug, nav label) in site order
    ('index', 'Overview'),
    ('logo', 'Logo'),
    ('colour', 'Colour'),
    ('type', 'Type'),
    ('packaging', 'Packaging'),
]
SECTION_RE = re.compile(r'<section[^>]*\bid="([^"]+)"[^>]*\bdata-nav="([^"]+)"')


def href(slug):
    return 'index.html' if slug == 'index' else f'{slug}.html'


def load(slug):
    src = open(os.path.join(HERE, 'src', 'pages', slug + '.html'), encoding='utf-8').read()
    src = re.sub(r'<!--include:([\w-]+)-->', lambda m: open(os.path.join(HERE, 'src', 'partials', m.group(1) + '.svg'), encoding='utf-8').read(), src)
    meta = json.loads(re.match(r'\s*<!--\s*(\{.*?\})\s*-->', src, re.S).group(1))
    body = re.sub(r'\s*<!--\s*\{.*?\}\s*-->\s*', '', src, count=1, flags=re.S)
    return meta, body, SECTION_RE.findall(body)


def nav(current, sections_by_slug):
    out = []
    for slug, label in PAGES:
        if slug == 'index':
            continue
        here = slug == current
        subs = ''.join(f'<li><a href="{href(slug)}#{sid}" data-spy="{sid}">{lab}</a></li>' for sid, lab in sections_by_slug[slug])
        out.append(f'<li class="nav-page{" is-current" if here else ""}">'
                   f'<a href="{href(slug)}"{" aria-current=page" if here else ""}>{label}</a>'
                   f'<ul class="nav-subs">{subs}</ul></li>')
    return '\n'.join(out)


def prevnext(i):
    links = []
    if i > 0:
        s, l = PAGES[i - 1]
        links.append(f'<a class="pn prev" href="{href(s)}"><span class="label">Previous</span><span class="pn-title">{l}</span></a>')
    else:
        links.append('<span></span>')
    if i < len(PAGES) - 1:
        s, l = PAGES[i + 1]
        links.append(f'<a class="pn next" href="{href(s)}"><span class="label">Next</span><span class="pn-title">{l}</span></a>')
    return ''.join(links)


def main():
    layout = open(os.path.join(HERE, 'src', 'layout.html'), encoding='utf-8').read()
    # cache-bust the CSS and JS so a push shows straight away
    import hashlib
    v = hashlib.md5(b''.join(open(os.path.join(ROOT, p), 'rb').read() for p in ('assets/css/site.css', 'assets/js/site.js', 'assets/js/palette.js'))).hexdigest()[:8]
    layout = layout.replace('{{v}}', v)
    loaded = {slug: load(slug) for slug, _ in PAGES}
    sections = {slug: v[2] for slug, v in loaded.items()}
    for i, (slug, label) in enumerate(PAGES):
        meta, body, _ = loaded[slug]
        page = (layout
                .replace('{{doc_title}}', ('Ovoss Brand Guidelines' if slug == 'index' else f'{meta["title"]} | Ovoss Brand Guidelines'))
                .replace('{{description}}', re.sub(r'<[^>]+>', '', meta['intro'])[:155])
                .replace('{{slug}}', slug)
                .replace('{{nav}}', nav(slug, sections))
                .replace('{{home_current}}', ' aria-current="page"' if slug == 'index' else '')
                .replace('{{title}}', meta['title'])
                .replace('{{intro}}', meta['intro'])
                .replace('{{content}}', body)
                .replace('{{prevnext}}', prevnext(i)))
        open(os.path.join(ROOT, href(slug)), 'w', encoding='utf-8').write(page)
        print('built', href(slug), f'({len(sections[slug])} sections)')


if __name__ == '__main__':
    main()
