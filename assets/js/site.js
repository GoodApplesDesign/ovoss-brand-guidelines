// Ovoss brand guidelines: menu, scroll-spy, copy buttons, tabs, logo colourway selector, diagrams that animate in
(function () {
  var body = document.body;

  // mobile menu
  var btn = document.querySelector('.menu-btn');
  function setNav(open) { body.classList.toggle('nav-open', open); if (btn) btn.setAttribute('aria-expanded', open ? 'true' : 'false'); }
  if (btn) btn.addEventListener('click', function () { setNav(!body.classList.contains('nav-open')); });
  document.addEventListener('click', function (e) {
    if (!body.classList.contains('nav-open')) return;
    if (e.target.closest('.nav a') || (!e.target.closest('.sidebar') && !e.target.closest('.menu-btn'))) setNav(false);
  });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') setNav(false); });

  // scroll-spy: highlight the section in view
  var links = {};
  document.querySelectorAll('.nav-subs a[data-spy]').forEach(function (a) { if (a.closest('.is-current')) links[a.dataset.spy] = a; });
  var current = null;
  if ('IntersectionObserver' in window && Object.keys(links).length) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (!en.isIntersecting || !links[en.target.id]) return;
        if (current) current.classList.remove('is-active');
        current = links[en.target.id]; current.classList.add('is-active');
      });
    }, { rootMargin: '-30% 0px -60% 0px' });
    Object.keys(links).forEach(function (id) { var s = document.getElementById(id); if (s) io.observe(s); });
  }

  // click to copy colour values
  document.querySelectorAll('.copyable').forEach(function (b) {
    b.addEventListener('click', function () {
      var v = b.dataset.copy || b.textContent.trim();
      var done = function () { b.classList.add('copied'); setTimeout(function () { b.classList.remove('copied'); }, 1400); };
      if (navigator.clipboard) navigator.clipboard.writeText(v).then(done, function () {});
    });
  });

  // colour values: one toggle opens or folds every range card's values
  document.querySelectorAll('[data-values-toggle]').forEach(function (b) {
    var grid = b.nextElementSibling;
    b.addEventListener('click', function () {
      var open = !grid.classList.contains('open');
      grid.classList.toggle('open', open);
      b.setAttribute('aria-expanded', open ? 'true' : 'false');
      b.textContent = open ? 'Hide colour values' : 'Show colour values';
    });
  });

  // tabs: show one panel at a time (e.g. gradient / flat colourways)
  document.querySelectorAll('[data-tabs]').forEach(function (box) {
    var tabs = box.querySelectorAll('[role="tab"]'), panels = box.querySelectorAll('[data-panel]');
    tabs.forEach(function (t) {
      t.addEventListener('click', function () {
        tabs.forEach(function (o) { o.setAttribute('aria-selected', o === t ? 'true' : 'false'); });
        panels.forEach(function (p) { p.hidden = p.dataset.panel !== t.dataset.tab; });
      });
    });
  });


  // diagrams that animate in once, when they scroll into view
  document.querySelectorAll('[data-animate]').forEach(function (el) {
    if (!('IntersectionObserver' in window)) return;
    el.classList.add('armed');
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (e) { if (e.isIntersecting) { el.classList.add('in-view'); io.disconnect(); } });
    }, { threshold: 0.45 });
    io.observe(el);
  });

  // logo variant selector
  document.querySelectorAll('[data-selector]').forEach(function (sel) {
    var stage = sel.querySelector('.stage'), img = stage.querySelector('img');
    var res = sel.querySelector('.result');
    sel.querySelectorAll('.chip').forEach(function (c) {
      c.addEventListener('click', function () {
        sel.querySelectorAll('.chip').forEach(function (o) { o.setAttribute('aria-pressed', o === c ? 'true' : 'false'); });
        stage.style.background = c.dataset.bg;
        img.style.opacity = 0;
        setTimeout(function () { img.src = c.dataset.logo; img.alt = c.dataset.name; img.style.opacity = 1; }, 180);
        res.innerHTML = '<strong>' + c.dataset.name + '</strong>' + c.dataset.note;
      });
    });
  });
})();

// palette switch: the site is written in Original; Bright swaps colours, values, names, logos and renders in place.
// The swap table (palette.js) is made by _build/make_bright.py. The choice is remembered, and ?palette=bright links to it.
(function () {
  var B = window.OVOSS_BRIGHT, root = document.documentElement, KEY = 'ovoss-palette';
  var sw = document.querySelector('.pal-switch');
  if (!B || !sw) { root.classList.remove('pal-pending'); return; }
  function esc(s) { return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); }
  var files = {}; B.files.forEach(function (f) { files[f] = f.replace(/^assets\//, 'assets/bright/'); });
  var nameMap = {}; B.names.forEach(function (n) { nameMap[n[0]] = n[1]; });
  var hexRe = /#[0-9a-fA-F]{6}\b/g;
  var numRe = new RegExp('(^|[^0-9])(' + Object.keys(B.rgb).concat(Object.keys(B.cmyk)).map(esc).join('|') + ')(?![0-9])', 'g');
  var rgbaRe = new RegExp('(' + Object.keys(B.rgba).map(function (k) { return k.split(',').join('\\s*,\\s*'); }).join('|') + ')', 'g');
  var nameRe = new RegExp('\\b(' + B.names.map(function (n) { return esc(n[0]); }).join('|') + ')\\b', 'g');
  var pathRe = new RegExp('(' + B.files.map(esc).join('|') + ')', 'g');
  var URLS = { src: 1, href: 1, 'data-logo': 1 };
  function bright(s, a) {
    if (URLS[a]) return s.replace(pathRe, function (m) { return files[m]; });   // file links: only swap to the Bright file
    return s.replace(hexRe, function (h) { return B.hex[h.toUpperCase()] || h; })
      .replace(rgbaRe, function (m) { return B.rgba[m.replace(/\s+/g, '')]; })
      .replace(numRe, function (m, pre, k) { return pre + (B.rgb[k] || B.cmyk[k]); })
      .replace(nameRe, function (m) { return nameMap[m]; });
  }
  var ATTRS = ['style', 'fill', 'stroke', 'stop-color', 'src', 'href', 'data-bg', 'data-logo', 'data-name', 'data-note', 'alt', 'aria-label', 'title'];
  var items = [];
  var walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, { acceptNode: function (n) {
    return n.parentElement.closest('script, style, .pal-switch, [data-bright]') ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT; } });
  for (var n = walker.nextNode(); n; n = walker.nextNode()) if (bright(n.nodeValue) !== n.nodeValue) items.push([n, null, n.nodeValue]);
  document.querySelectorAll('body *, link[rel="icon"]').forEach(function (el) {
    if (el.closest('.pal-switch')) return;
    ATTRS.forEach(function (a) { var v = el.getAttribute(a); if (v && bright(v, a) !== v) items.push([el, a, v]); });
    if (el.hasAttribute('data-bright')) items.push([el, '#html', el.innerHTML]);
  });
  function apply(p) {
    var on = p === 'bright';
    items.forEach(function (it) {
      var el = it[0], a = it[1], o = it[2];
      var v = !on ? o : a === '#html' ? el.getAttribute('data-bright') : bright(o, a);
      if (a === null) el.nodeValue = v; else if (a === '#html') el.innerHTML = v; else el.setAttribute(a, v);
    });
    // logo colour selector: keep whichever option is picked, in the new palette
    document.querySelectorAll('[data-selector]').forEach(function (sel) {
      var c = sel.querySelector('.chip[aria-pressed="true"]'), stage = sel.querySelector('.stage'), res = sel.querySelector('.result');
      if (!c) return;
      stage.style.background = c.dataset.bg; stage.querySelector('img').src = c.dataset.logo;
      if (res) res.innerHTML = '<strong>' + c.dataset.name + '</strong>' + c.dataset.note;
    });
    if (on) root.setAttribute('data-palette', 'bright'); else root.removeAttribute('data-palette');
    sw.querySelectorAll('button').forEach(function (b) { b.setAttribute('aria-pressed', b.dataset.pal === p ? 'true' : 'false'); });
    try { localStorage.setItem(KEY, p); } catch (e) {}
    root.classList.remove('pal-pending');
  }
  sw.querySelectorAll('button').forEach(function (b) { b.addEventListener('click', function () { apply(b.dataset.pal); }); });
  var start = 'original';
  try { start = localStorage.getItem(KEY) || 'original'; } catch (e) {}
  apply(start === 'bright' ? 'bright' : 'original');
})();
