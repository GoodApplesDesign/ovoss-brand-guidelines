# Ovoss brand guidelines

A static site: open `index.html` in a browser, or host the folder on any static host (GitHub Pages works as-is).

## Editing
The root `*.html` pages are generated, so don't edit them directly. Instead:

1. Edit the page sources in `_build/src/pages/` (shared shell: `_build/src/layout.html`). Styles live in `assets/css/site.css`.
2. Rebuild:
   ```
   python3 _build/build.py
   ```

### Page source conventions
- Line 1 is a JSON comment with the page title and intro.
- `<section id="x" data-nav="Label">` adds a link in the sidebar.
- `<!--include:name-->` inlines `_build/src/partials/name.svg`.

## Logos, diagrams and downloads
- Logo SVGs in `assets/logo/svg/` are exported from `Ovoss_Wordmark.ai` (Illustrator).
- `python3 _build/make_diagrams.py` rebuilds the clear space diagrams and the wave.
- `python3 _build/make_downloads.py` rebuilds the zips, PNGs, Adobe swatches and CSS tokens. Needs Google Chrome.

## Fonts
Avenir Next is a system font on Mac and iPhone and isn't served. The serif italic (Noto Serif, SIL Open Font License) is embedded in `site.css` so it also loads when the site is opened straight from the folder.

## Product renders
The images in `assets/img/` are rendered from the print artwork. Bottle shape and the back label size are provisional until Ardoz confirms them.
