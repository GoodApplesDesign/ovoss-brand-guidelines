// Ovoss Mist pack files (Joey, 11 Nov 2026), built from COPIES of the three pack .ai files.
// Never opens, saves or closes Joey's files: each source is copied into .ai_copies/mist/ and only that copy is
// opened, changed, saved and closed. Stops if a source file is open in Illustrator with unsaved edits.
//
// Per pack:
//  - Artwork (CMYK): light tint behind the panels, the wave fill in the darker Mist wave colour, claims a step deeper,
//    the old solid dentist badge removed, the old wave trim and the Vs moved to the foil layer, benefit bullets
//    unprinted (ticks replace them). Carton: the wave eased on the back and right panels so it meets at the glue corner.
//  - FINISH - Foil: the logo Vs, the wave trim, the dentist badge (line version, all foil) and the benefit ticks, in one
//    spot colour per range ("FOIL - Implant Care Blue"), 100%, overprint.
//  - FINISH - Spot UV High Build: the logo letters (not the TM), the wave trim and the dentist badge, spot
//    "SPOT UV - High Build", 100%, overprint.
//  - Notes (non-printing): the finishing spec.
// Then exports the render textures (colour, foil only, high build only) into tex/, and the range carton colours.
// Run: osascript -e 'with timeout of 900 seconds' -e 'tell application "Adobe Illustrator" to do javascript file (POSIX file "<abs path>/make_mist_packs.jsx")' -e 'end timeout'
(function () {
  var MM = 2.834645669, LOG = [], STEP = "";
  var HERE = File($.fileName).parent;
  $.evalFile(new File(HERE.fsName + "/mist_cfg.js"));
  var SRC = HERE.fsName + "/../../../Ovoss Packaging/";
  var WORK = new Folder(HERE.fsName + "/.ai_copies/mist"); if (!WORK.exists) WORK.create();
  var TEX = HERE.fsName + "/tex/";
  // 1. stop if a source is open with unsaved edits
  for (var i = 0; i < app.documents.length; i++) { var d0 = app.documents[i], p0 = ""; try { p0 = d0.fullName.fsName; } catch (e) {}
    for (var q = 0; q < CFG.packs.length; q++) if (p0 == new File(SRC + CFG.packs[q].src).fsName && !d0.saved) return "STOPPED: unsaved edits in " + CFG.packs[q].src; }
  var keep = null; try { keep = app.activeDocument; } catch (e) {}
  var oldUIL = app.userInteractionLevel; app.userInteractionLevel = UserInteractionLevel.DONTDISPLAYALERTS;
  var oldCS = app.coordinateSystem;

  function cmyk(a) { var c = new CMYKColor(); c.cyan = a[0]; c.magenta = a[1]; c.yellow = a[2]; c.black = a[3]; return c; }
  function near(c, a) { return c && c.typename == "CMYKColor" && Math.abs(c.cyan - a[0]) < 1.5 && Math.abs(c.magenta - a[1]) < 1.5 && Math.abs(c.yellow - a[2]) < 1.5 && Math.abs(c.black - a[3]) < 1.5; }
  function spot(d, nm, alt) {
    var sp = null; try { sp = d.spots.getByName(nm); } catch (e) {}
    if (!sp) { sp = d.spots.add(); sp.name = nm; }
    sp.colorType = ColorModel.SPOT; sp.color = cmyk(alt);
    var sc = new SpotColor(); sc.spot = sp; sc.tint = 100; return sc;
  }
  function swatch(d, nm, a, grp) { var s = null; try { s = d.swatches.getByName(nm); } catch (e) {} if (!s) { s = d.swatches.add(); s.name = nm; } s.color = cmyk(a); if (grp) try { grp.addSwatch(s); } catch (e) {} return s; }
  function paint(it, col, over) { // fill everything in it with col; overprint for finishes
    var t = it.typename;
    if (t == "GroupItem") { for (var k = 0; k < it.pageItems.length; k++) paint(it.pageItems[k], col, over); }
    else if (t == "CompoundPathItem") { for (var k2 = 0; k2 < it.pathItems.length; k2++) paint(it.pathItems[k2], col, over); }
    else if (t == "PathItem") { if (it.filled || !it.stroked) { it.filled = true; it.fillColor = col; it.fillOverprint = !!over; } if (it.stroked) { it.strokeColor = col; it.strokeOverprint = !!over; } }
  }
  function layer(d, nm, above) { var L = null; try { L = d.layers.getByName(nm); } catch (e) {} if (!L) { L = d.layers.add(); L.name = nm; } if (above) L.move(above, ElementPlacement.PLACEBEFORE); L.locked = false; L.visible = true; return L; }
  function all(d, test) { var out = [], k; for (k = 0; k < d.pathItems.length; k++) if (test(d.pathItems[k])) out.push(d.pathItems[k]);
    for (k = 0; k < d.compoundPathItems.length; k++) if (test(d.compoundPathItems[k])) out.push(d.compoundPathItems[k]); return out; }
  function byName(d, nm) { for (var k = 0; k < d.pageItems.length; k++) if (d.pageItems[k].name == nm) return d.pageItems[k]; return null; }
  function centre(b) { return [(b[0] + b[2]) / 2, (b[1] + b[3]) / 2]; }

  // carton: ease the wave on the back and right panels so the two ends meet at the glue corner
  function fixSeam(p, s) {
    var pts = p.pathPoints, n = pts.length, ybot = 1e9, k, top = [];
    for (k = 0; k < n; k++) ybot = Math.min(ybot, pts[k].anchor[1]);
    for (k = 0; k < n; k++) if (pts[k].anchor[1] > ybot + 0.01 * MM) top.push(pts[k].anchor);
    function yAt(xmm) { var x = xmm * MM, lo = null, hi = null;
      for (var j = 0; j < top.length; j++) { var a = top[j]; if (a[0] <= x && (!lo || a[0] > lo[0])) lo = a; if (a[0] >= x && (!hi || a[0] < hi[0])) hi = a; }
      if (!lo) return hi[1] / MM; if (!hi || hi[0] == lo[0]) return lo[1] / MM; return (lo[1] + (hi[1] - lo[1]) * (x - lo[0]) / (hi[0] - lo[0])) / MM; }
    var y0 = yAt(s.x0), y1 = yAt(s.x1), h = (y0 + y1) / 2;
    for (k = 0; k < n; k++) { var a = pts[k].anchor; if (a[1] <= ybot + 0.01 * MM) continue; var x = a[0] / MM, c = 0, t;
      if (x <= s.backEnd) { t = Math.max(0, Math.min(1, (x - s.x0) / (s.backEnd - s.x0))); c = (h - y0) * (0.5 + 0.5 * Math.cos(Math.PI * t)); }
      else if (x >= s.rightStart) { t = Math.max(0, Math.min(1, (x - s.rightStart) / (s.x1 - s.rightStart))); c = (h - y1) * (0.5 - 0.5 * Math.cos(Math.PI * t)); }
      if (c) { var ny = a[1] + c * MM; pts[k].anchor = [a[0], ny]; pts[k].leftDirection = [a[0], ny]; pts[k].rightDirection = [a[0], ny]; } }
    return p.name + " ends " + y0.toFixed(2) + " / " + y1.toFixed(2) + " -> " + h.toFixed(2);
  }

  // mouthwash back label: ease its two ends to the front label's wave heights, which sit next to them on the bottle
  function easeEnds(p, e, key) {
    var pts = p.pathPoints, n = pts.length, ybot = 1e9, k, top = [];
    for (k = 0; k < n; k++) ybot = Math.min(ybot, pts[k].anchor[1]);
    for (k = 0; k < n; k++) if (pts[k].anchor[1] > ybot + 0.01 * MM) top.push(pts[k].anchor);
    function yAt(xmm) { var x = xmm * MM, lo = null, hi = null;
      for (var j = 0; j < top.length; j++) { var a = top[j]; if (a[0] <= x && (!lo || a[0] > lo[0])) lo = a; if (a[0] >= x && (!hi || a[0] < hi[0])) hi = a; }
      if (!lo) return hi[1] / MM; if (!hi || hi[0] == lo[0]) return lo[1] / MM; return (lo[1] + (hi[1] - lo[1]) * (x - lo[0]) / (hi[0] - lo[0])) / MM; }
    var dl = e.left[key] - yAt(e.x0), dr = e.right[key] - yAt(e.x1);
    for (k = 0; k < n; k++) { var a = pts[k].anchor; if (a[1] <= ybot + 0.01 * MM) continue; var x = a[0] / MM, c = 0, t;
      if (x <= e.x0 + e.ease) { t = Math.max(0, Math.min(1, (x - e.x0) / e.ease)); c += dl * (0.5 + 0.5 * Math.cos(Math.PI * t)); }
      if (x >= e.x1 - e.ease) { t = Math.max(0, Math.min(1, (e.x1 - x) / e.ease)); c += dr * (0.5 + 0.5 * Math.cos(Math.PI * t)); }
      if (c) { var ny = a[1] + c * MM; pts[k].anchor = [a[0], ny]; pts[k].leftDirection = [a[0], ny]; pts[k].rightDirection = [a[0], ny]; } }
    return p.name + " ends -> " + e.left[key] + " / " + e.right[key];
  }
  // TM -> (R) (Greg, 11 Nov: the trade mark is through). Each "TM" item is replaced by an Avenir Next Demi Bold (R),
  // 1.45x the TM's letter height, turned with its wordmark, set at the TM's corner nearest the S and the top line.
  function swapTM(d) {
    var tms = all(d, function (it) { return it.name == "TM"; }), n = 0, font = app.textFonts.getByName("AvenirNext-DemiBold");
    for (var i = 0; i < tms.length; i++) { var tm = tms[i], b = tm.geometricBounds, par = tm.parent, s2 = null;
      for (var k = 0; k < par.pageItems.length; k++) if (par.pageItems[k].name == "S2") s2 = par.pageItems[k];
      var tc = centre(b), ang = 0;
      if (!s2) { var best = 1e12, s2s = all(d, function (it) { return it.name == "S2"; });   // TM grouped apart from its letters
        for (var q2 = 0; q2 < s2s.length; q2++) { var c2 = centre(s2s[q2].geometricBounds), dd = Math.pow(c2[0] - tc[0], 2) + Math.pow(c2[1] - tc[1], 2); if (dd < best) { best = dd; s2 = s2s[q2]; } } }
      if (s2) { var sc2 = centre(s2.geometricBounds); ang = Math.round((Math.atan2(tc[1] - sc2[1], tc[0] - sc2[0]) * 180 / Math.PI - 45) / 90) * 90; }
      ang = ((ang % 360) + 360) % 360;
      var w = b[2] - b[0], h = b[1] - b[3], H = (ang == 90 || ang == 270) ? w : h;
      var col = null; try { col = tm.typename == "CompoundPathItem" ? tm.pathItems[0].fillColor : tm.fillColor; } catch (e) {}
      var t = tm.layer.textFrames.add(); t.contents = "\u00AE"; t.textRange.characterAttributes.textFont = font; t.textRange.characterAttributes.size = 20;
      var o = t.createOutline(), ob = o.geometricBounds, kk = (H * 1.45) / (ob[1] - ob[3]) * 100; o.resize(kk, kk);
      if (ang) o.rotate(ang);
      ob = o.geometricBounds;
      // the upright top-left corner, turned with the wordmark
      var cx = { 0: [0, 1], 90: [0, 3], 180: [2, 3], 270: [2, 1] }[ang];
      o.translate(b[cx[0]] - ob[cx[0]], b[cx[1]] - ob[cx[1]]);
      if (col) paint(o, col, false);
      o.move(tm, ElementPlacement.PLACEBEFORE); o.name = "R"; tm.remove(); n++; }
    return "TM->R " + n;
  }
  function topEdge(p) { // the wave's top edge anchors, left to right (the wave paths are 1 mm polylines with a flat base)
    var pts = p.pathPoints, ybot = 1e9, out = [], k;
    for (k = 0; k < pts.length; k++) ybot = Math.min(ybot, pts[k].anchor[1]);
    for (k = 0; k < pts.length; k++) if (pts[k].anchor[1] > ybot + 0.01 * MM) out.push([pts[k].anchor[0], pts[k].anchor[1]]);
    out.sort(function (a, b) { return a[0] - b[0]; }); return out;
  }
  function interpY(arr, x) { if (x <= arr[0][0]) return arr[0][1]; if (x >= arr[arr.length - 1][0]) return arr[arr.length - 1][1];
    for (var k = 1; k < arr.length; k++) if (arr[k][0] >= x) { var a = arr[k - 1], b = arr[k]; return a[1] + (b[1] - a[1]) * (x - a[0]) / (b[0] - a[0]); }
    return arr[arr.length - 1][1]; }

  function exportPNG(d, job, file) {
    var r = job.rect;
    if (job.dieLayer) { var g = d.layers.getByName(job.dieLayer).pageItems[0].geometricBounds; r = [g[0] / MM, g[1] / MM, g[2] / MM, g[3] / MM]; }
    d.artboards[0].artboardRect = [r[0] * MM, r[1] * MM, r[2] * MM, r[3] * MM]; d.artboards.setActiveArtboardIndex(0);
    var o = new ExportOptionsPNG24(); o.artBoardClipping = true; o.horizontalScale = job.scale; o.verticalScale = job.scale; o.antiAliasing = true; o.transparency = false;
    d.exportFile(new File(file), ExportType.PNG24, o);
  }
  function show(d, on) { // on: names of non-dieline layers to show; dielines hidden except the tube's printed eye mark
    for (var k = 0; k < d.layers.length; k++) { var L = d.layers[k], nm = L.name;
      if (nm.indexOf("Dieline") == 0) L.visible = (nm == "Dieline - Artwork + Reg.") && on.join("|").indexOf("Artwork") >= 0;
      else { var v = false; for (var j = 0; j < on.length; j++) if (nm == on[j]) v = true; L.visible = v; } }
  }

  try {
    var badgeDoc = null;
    for (var pi = 0; pi < CFG.packs.length; pi++) {
      var P = CFG.packs[pi], R = CFG.ranges["implant-care"];
      var src = new File(SRC + P.src), cp = new File(WORK.fsName + "/" + P.out);
      if (cp.exists) cp.remove(); if (!src.copy(cp.fsName)) throw "copy failed " + P.src;
      var d = app.open(cp);
      if (d.fullName.fsName.indexOf("/_build/studio/.ai_copies/mist/") < 0) throw "not a copy: " + d.fullName.fsName;
      app.coordinateSystem = CoordinateSystem.DOCUMENTCOORDINATESYSTEM;
      var art = d.layers.getByName("Artwork"); art.locked = false; art.visible = true;
      var foilL = layer(d, "FINISH - Foil (" + R.foilName.replace("FOIL - ", "") + ")", art);
      var hbL = layer(d, "FINISH - Spot UV High Build", foilL);
      var notesL = layer(d, "Notes (non-printing)", null); notesL.move(d.layers[0], ElementPlacement.PLACEBEFORE); notesL.printable = false;
      STEP = P.key + " spots"; var FOIL = spot(d, R.foilName, R.foil); STEP = P.key + " spot HB"; var HB = spot(d, CFG.hbName, CFG.hbAlt);
      var sg = null; try { sg = d.swatchGroups.add(); sg.name = "Ovoss Mist"; } catch (e) {}
      swatch(d, "Deep Navy", CFG.navy, sg); var TINT = swatch(d, "Mist Tint - " + R.name, R.paper, sg).color;
      var WAVE = swatch(d, "Mist Wave - " + R.name, R.wave, sg).color; var CLAIMS = swatch(d, "Claims Grey", CFG.claims, sg).color;
      try { sg.addSwatch(d.swatches.getByName(R.foilName)); sg.addSwatch(d.swatches.getByName(CFG.hbName)); } catch (e) {}
      var log = [P.out];

      STEP = P.key + " tint";
      // tint behind everything on the panels
      for (var ti = 0; ti < P.tints.length; ti++) { var tr = P.tints[ti];
        var rect = art.pathItems.rectangle(tr[1] * MM, tr[0] * MM, (tr[2] - tr[0]) * MM, (tr[1] - tr[3]) * MM);
        rect.name = "Mist tint"; rect.stroked = false; rect.filled = true; rect.fillColor = TINT; rect.move(art, ElementPlacement.PLACEATEND); }

      STEP = P.key + " waves";
      // waves: seam (carton), fill colour, trim -> foil (the visible band only) + high build
      for (var wi = 0; wi < P.waves.length; wi++) {
        var ice = byName(d, P.waves[wi][0]), sil = byName(d, P.waves[wi][1]);
        if (P.seam) { log.push(fixSeam(ice, P.seam)); log.push(fixSeam(sil, P.seam)); }
        if (P.ends && P.ends[wi]) { log.push(easeEnds(ice, P.ends[wi], "ice")); log.push(easeEnds(sil, P.ends[wi], "sil")); }
        ice.fillColor = WAVE;
        // the visible trim: between the fill's top edge and the trim's top edge, wherever the trim sits above the fill.
        // Cut out wherever a barcode's white box sits, so no foil (or high build) lands on the barcode.
        var it = topEdge(ice), st = topEdge(sil), x0 = it[0][0], x1 = it[it.length - 1][0], cuts = [], spans = [], bk, cx;
        for (bk = 0; bk < d.groupItems.length; bk++) if (d.groupItems[bk].name.indexOf("BARCODE") == 0) { var gbx = d.groupItems[bk].geometricBounds, topMax = -1e9;
          for (var xx = gbx[0]; xx <= gbx[2]; xx += 0.5 * MM) topMax = Math.max(topMax, interpY(st, xx), interpY(it, xx));
          if (gbx[3] < topMax) cuts.push([gbx[0] - 0.3 * MM, gbx[2] + 0.3 * MM]); }  // only where the box actually overlaps the trim
        cuts.sort(function (a, b) { return a[0] - b[0]; }); cx = x0;
        for (bk = 0; bk < cuts.length; bk++) { if (cuts[bk][1] < x0 || cuts[bk][0] > x1) continue; if (cuts[bk][0] > cx) spans.push([cx, cuts[bk][0]]); cx = Math.max(cx, cuts[bk][1]); }
        if (cx < x1) spans.push([cx, x1]);
        var band = foilL.groupItems.add(); band.name = "Foil - wave trim";
        for (var sp2 = 0; sp2 < spans.length; sp2++) { var a0 = spans[sp2][0], a1 = spans[sp2][1], xs = [a0];
          for (bk = 0; bk < it.length; bk++) if (it[bk][0] > a0 && it[bk][0] < a1) xs.push(it[bk][0]); xs.push(a1);
          var bp = []; for (bk = 0; bk < xs.length; bk++) bp.push([xs[bk], Math.max(interpY(it, xs[bk]), interpY(st, xs[bk]))]);
          for (bk = xs.length - 1; bk >= 0; bk--) bp.push([xs[bk], interpY(it, xs[bk])]);
          var bpath = band.pathItems.add(); bpath.setEntirePath(bp); bpath.closed = true; bpath.stroked = false; bpath.filled = true; }
        band = foilL.groupItems.getByName("Foil - wave trim"); paint(band, FOIL, true); log.push("trim spans " + spans.length);
        var hbBand = band.duplicate(hbL, ElementPlacement.PLACEATEND); hbBand.name = "High build - wave trim"; paint(hbBand, HB, true); hbBand.blendingMode = BlendModes.MULTIPLY;
        sil.remove(); d.selection = null;
      }

      STEP = P.key + " claims";
      // claims a step deeper (Slate -> Claims Grey) on the text that was Slate
      var nClaims = 0;
      for (var tf = 0; tf < d.textFrames.length; tf++) { var T = d.textFrames[tf];
        try { if (near(T.textRange.characterAttributes.fillColor, CFG.slate)) { T.textRange.characterAttributes.fillColor = CLAIMS; nClaims++; } } catch (e) {} }
      log.push("claims frames " + nClaims);

      STEP = P.key + " ticks";
      // benefit bullets -> unprinted; ticks (the logo V) on the foil layer
      // the tick is the upright logo V: one in a lockup whose "Implant Care" line sits below the wordmark
      var Vs = all(d, function (it) { return it.name == "V" && it.typename == "PathItem"; }), vRef = Vs[0], nTicks = 0;
      for (var vi = 0; vi < Vs.length; vi++) { var wmG = Vs[vi].parent, lkG = wmG.parent;
        if (lkG && lkG.typename == "GroupItem" && lkG.name == "Lockup") { var icG = null;
          for (var gq = 0; gq < lkG.groupItems.length; gq++) if (lkG.groupItems[gq].name == "Implant Care") icG = lkG.groupItems[gq];
          if (icG && centre(icG.geometricBounds)[1] < centre(wmG.geometricBounds)[1]) { vRef = Vs[vi]; break; } } }
      for (var tf2 = 0; tf2 < d.textFrames.length; tf2++) { var B = d.textFrames[tf2], txt = "";
        try { txt = B.contents; } catch (e) {} if (txt.indexOf("\u2022") < 0 || B.layer.locked || !B.layer.visible || B.locked || B.hidden) continue;
        var left = B.geometricBounds[0], od = B.duplicate(), og = od.createOutline(), dots = [];
        (function scan(it) { var t = it.typename;
          if (t == "GroupItem") { for (var k = 0; k < it.pageItems.length; k++) scan(it.pageItems[k]); return; }
          var b = it.geometricBounds, w = (b[2] - b[0]) / MM, h = (b[1] - b[3]) / MM;
          var solid = t == "PathItem" || (t == "CompoundPathItem" && it.pathItems.length == 1);  // a bullet is one solid dot; an "o" has a hole
          if (solid && w > 0.55 && w < 1.0 && Math.abs(w - h) < 0.08 && b[0] < left + 1 * MM) dots.push([centre(b), w]); })(og);
        og.remove();
        for (var c = 0; c < B.characters.length; c++) { var ch = B.characters[c]; if (ch.contents == "\u2022") ch.characterAttributes.fillColor = new NoColor(); }
        log.push("bullets " + dots.length);
        for (var dt = 0; dt < dots.length; dt++) { var ctr = dots[dt][0], dia = dots[dt][1] * MM, th = 1.35 * dia;
          var tk = vRef.duplicate(foilL, ElementPlacement.PLACEATBEGINNING), tb = tk.geometricBounds, sc = th / (tb[1] - tb[3]) * 100;
          tk.resize(sc, sc); tb = tk.geometricBounds; var tc = centre(tb);
          tk.translate(ctr[0] - tc[0], ctr[1] + 0.15 * dia - tc[1]); tk.name = "Foil - benefit tick"; paint(tk, FOIL, true); nTicks++; }
      }
      log.push("ticks " + nTicks);

      STEP = P.key + " logos";
      // logos: every letter to high build (not the TM / R); every V to foil
      var letters = all(d, function (it) { return it.name == "O1" || it.name == "V" || it.name == "O2" || it.name == "S1" || it.name == "S2"; });
      for (var li = 0; li < letters.length; li++) { var Lt = letters[li];
        var hd = Lt.duplicate(hbL, ElementPlacement.PLACEATEND); hd.name = "High build - logo " + Lt.name; paint(hd, HB, true); hd.blendingMode = BlendModes.MULTIPLY;
        if (Lt.name == "V") { Lt.move(foilL, ElementPlacement.PLACEATBEGINNING); Lt.name = "Foil - logo V"; paint(Lt, FOIL, true); } }
      log.push("logo letters " + letters.length);

      STEP = P.key + " badge";
      // dentist badge: solid disc -> line badge (type, tooth, tick and a thin ring), all foil + high build, 80%
      var old = byName(d, "Dentist recommended mark");
      if (old) {
        var ob = old.geometricBounds, oc = centre(ob), D = ob[2] - ob[0], nd = D * CFG.badgeScale, ringW = CFG.ringMM * MM;
        if (!badgeDoc) { badgeDoc = app.open(new File(CFG.badgeSvg));
          if (badgeDoc.pageItems.length > 1) { var bgp = badgeDoc.layers[0].groupItems.add(); bgp.name = "BADGE";
            for (var bi = badgeDoc.layers[0].pageItems.length - 1; bi >= 0; bi--) { var bit = badgeDoc.layers[0].pageItems[bi]; if (bit.name != "BADGE") bit.move(bgp, ElementPlacement.PLACEATBEGINNING); } } }
        var bsrc = badgeDoc.pageItems[0]; for (var bj = 0; bj < badgeDoc.pageItems.length; bj++) if (badgeDoc.pageItems[bj].name == "BADGE") bsrc = badgeDoc.pageItems[bj];
        var bg = bsrc.duplicate(foilL, ElementPlacement.PLACEATBEGINNING);
        app.activeDocument = d;
        var bb = bg.geometricBounds, k2 = nd / (bb[2] - bb[0]) * 100; bg.resize(k2, k2); bb = bg.geometricBounds; var bc = centre(bb);
        bg.translate(oc[0] - bc[0], oc[1] - bc[1]);
        // drop the invisible reference circle used for sizing
        (function strip(it) { if (it.typename == "GroupItem") { for (var k = it.pageItems.length - 1; k >= 0; k--) strip(it.pageItems[k]); return; }
          if (it.typename == "PathItem" && !it.filled && !it.stroked) it.remove(); })(bg);
        var ring = foilL.pathItems.ellipse(oc[1] + (nd - ringW) / 2, oc[0] - (nd - ringW) / 2, nd - ringW, nd - ringW);
        ring.filled = false; ring.stroked = true; ring.strokeWidth = ringW;
        var badge = foilL.groupItems.add(); badge.name = "Foil - dentist badge (line)";
        ring.move(badge, ElementPlacement.PLACEATEND); bg.move(badge, ElementPlacement.PLACEATEND);
        badge = foilL.groupItems.getByName("Foil - dentist badge (line)"); paint(badge, FOIL, true);
        var hbB = badge.duplicate(hbL, ElementPlacement.PLACEATEND); hbB.name = "High build - dentist badge"; paint(hbB, HB, true); hbB.blendingMode = BlendModes.MULTIPLY;
        old.remove();
        log.push("badge " + (D / MM).toFixed(1) + "mm -> " + (nd / MM).toFixed(1) + "mm");
      }

      STEP = P.key + " reg"; log.push(swapTM(d));
      STEP = P.key + " notes";
      // notes
      var nt = notesL.textFrames.add(); nt.position = [P.notesAt[0] * MM, P.notesAt[1] * MM];
      nt.contents = "FINISHES (Ovoss Mist, " + R.name + ")\r" +
        "Supplied as separate spot colour layers, 100%, set to overprint. Dielines are not printed.\r" +
        "1. " + R.foilName + ": hot foil, metallic, colour to match CMYK " + R.foil.join("/") + " (visual).\r" +
        "   Printer to propose the closest stock foil. On: logo V, wave trim, dentist badge, benefit ticks.\r" +
        "2. " + CFG.hbName + ": raised gloss UV (high build). On: logo letters, wave trim, dentist badge.\r" +
        "   Its layer is set to Multiply with a light grey alternate, so the artwork shows through on screen. The plate is 100% spot.\r" +
        "   Badge type is fine detail: printer to confirm the minimum line for high build and foil.\r" +
        "Artwork layer is CMYK. The tint prints under the foil; no varnish under the foil. Barcode keeps its white box.";
      try { nt.textRange.characterAttributes.textFont = app.textFonts.getByName("AvenirNext-Medium"); } catch (e) {}
      nt.textRange.characterAttributes.size = 7; nt.textRange.characterAttributes.fillColor = cmyk([0, 0, 0, 100]);

      d.saveAs(cp); LOG.push(log.join(" | "));

      STEP = P.key + " textures";
      // textures for the renders: colour (artwork + foil in its visual colour), foil only, high build only
      var dir = new Folder(TEX + "mist-raw"); if (!dir.exists) dir.create();
      for (var ji = 0; ji < P.tex.length; ji++) { var J = P.tex[ji];
        show(d, ["Artwork", foilL.name]); exportPNG(d, J, dir.fsName + "/" + J.name + ".png");
        show(d, [foilL.name]); exportPNG(d, J, dir.fsName + "/" + J.name + "-foil.png");
        show(d, [hbL.name]); exportPNG(d, J, dir.fsName + "/" + J.name + "-hb.png"); }

      STEP = P.key + " ranges";
      // range cartons (renders only): range colours + range name, same finishes
      if (P.key == "carton") {
        var subs = []; for (var gi = 0; gi < d.groupItems.length; gi++) if (d.groupItems[gi].name == "Implant Care") subs.push(d.groupItems[gi]);
        var tintR = byName(d, "Mist tint"), iceR = byName(d, "Ice wave"), tops = [byName(d, "Top tuck"), byName(d, "Bottom tuck")];
        var font = app.textFonts.getByName("NotoSerif-Italic");
        for (var slug in CFG.ranges) { var RR = CFG.ranges[slug], made = [];
          show(d, ["Artwork", foilL.name]);
          FOIL.spot.color = cmyk(RR.foil); tintR.fillColor = cmyk(RR.paper); iceR.fillColor = cmyk(RR.wave);
          for (var u = 0; u < tops.length; u++) if (tops[u]) tops[u].fillColor = cmyk(RR.dark);
          if (RR.name != "Implant Care") for (var s = 0; s < subs.length; s++) {
            var g = subs[s], gb = g.geometricBounds, col = null, wm = null, lk = g.parent;
            try { col = g.compoundPathItems.length ? g.compoundPathItems[0].pathItems[0].fillColor : g.pathItems[0].fillColor; } catch (e) {}
            for (var q2 = 0; q2 < lk.groupItems.length; q2++) if (lk.groupItems[q2].name == "ovoss wordmark") wm = lk.groupItems[q2];
            var flipped = false; if (wm) flipped = (gb[1] + gb[3]) / 2 > (wm.geometricBounds[1] + wm.geometricBounds[3]) / 2;
            var pair = art.groupItems.add();
            var t1 = art.textFrames.add(); t1.contents = "Implant Care"; t1.textRange.characterAttributes.textFont = font; t1.textRange.characterAttributes.size = 10; t1.position = [0, 0];
            var t2 = art.textFrames.add(); t2.contents = RR.name; t2.textRange.characterAttributes.textFont = font; t2.textRange.characterAttributes.size = 10; t2.position = [0, 0];
            var o1 = t1.createOutline(); o1.name = "REF"; o1.move(pair, ElementPlacement.PLACEATEND);
            var o2 = t2.createOutline(); o2.name = "NEW"; o2.move(pair, ElementPlacement.PLACEATEND);
            var ref = pair.groupItems.getByName("REF"), nw = pair.groupItems.getByName("NEW");
            var rb = ref.geometricBounds, kk = (gb[2] - gb[0]) / (rb[2] - rb[0]) * 100; pair.resize(kk, kk); if (flipped) pair.rotate(180);
            rb = ref.geometricBounds; pair.translate(gb[0] - rb[0], gb[1] - rb[1]);
            var nb = nw.geometricBounds; nw.translate((gb[0] + gb[2]) / 2 - (nb[0] + nb[2]) / 2, 0); ref.remove();
            if (col) paint(nw, col, false); g.hidden = true; made.push(pair);
          }
          var rdir = new Folder(TEX + "mist-raw/" + slug); if (!rdir.exists) rdir.create();
          show(d, ["Artwork", foilL.name]); exportPNG(d, P.tex[0], rdir.fsName + "/carton.png");
          for (var m2 = 0; m2 < made.length; m2++) made[m2].remove(); for (var s2 = 0; s2 < subs.length; s2++) subs[s2].hidden = false;
        }
      }
      d.close(SaveOptions.DONOTSAVECHANGES); // our saved copy; the range swaps and layer toggles above are not kept
    }
    if (badgeDoc) badgeDoc.close(SaveOptions.DONOTSAVECHANGES); // the badge SVG we opened read-only
  } catch (err) { LOG.push("ERROR at " + STEP + ": " + err + " line " + err.line);
    for (var ci = app.documents.length - 1; ci >= 0; ci--) { var cd = app.documents[ci], cpth = ""; try { cpth = cd.fullName.fsName; } catch (e) {}
      if (cpth.indexOf("/_build/studio/.ai_copies/mist/") >= 0 || cpth == new File(CFG.badgeSvg).fsName) cd.close(SaveOptions.DONOTSAVECHANGES); } // ours only
  } finally {
    app.coordinateSystem = oldCS; app.userInteractionLevel = oldUIL;
    if (keep) try { app.activeDocument = keep; } catch (e) {}
  }
  return LOG.join("\n");
})();
