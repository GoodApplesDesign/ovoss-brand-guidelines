// Ovoss studio: carton textures for the other ranges, for the range line-up renders.
// Works on a COPY of the studio copy (.ai_copies/carton_range.ai); never opens, saves or closes Joey's files.
// Each "Implant Care" subline (outlined groups named "Implant Care") is swapped for the range name, set in the
// same font (Noto Serif Italic), scaled so "Implant Care" would match the original exactly, centred on it.
// Writes tex/range/carton-<slug>.png at the same rect and scale as export_textures.jsx.
// Run: osascript -e 'with timeout of 600 seconds' -e 'tell application "Adobe Illustrator" to do javascript file (POSIX file "<abs path>/export_range_cartons.jsx")' -e 'end timeout'
(function () {
  var MM = 2.834645669, LOG = [];
  var HERE = File($.fileName).parent;
  var COPIES = HERE.fsName + "/.ai_copies", OUT = new Folder(HERE.fsName + "/tex/range");
  if (!OUT.exists) OUT.create();
  var RANGES = [["Perio Care", "perio-care"], ["Daily Care", "daily-care"], ["Restore", "restore"], ["Implant Care", "implant-care"]];
  var src = new File(COPIES + "/carton_copy.ai"), cp = new File(COPIES + "/carton_range.ai");
  if (!src.exists) return "STOPPED: run export_textures.jsx first (no carton_copy.ai)";
  if (cp.exists) cp.remove();
  if (!src.copy(cp.fsName)) return "copy failed";
  var keep = null; try { keep = app.activeDocument; } catch (e) {}
  var oldUIL = app.userInteractionLevel; app.userInteractionLevel = UserInteractionLevel.DONTDISPLAYALERTS;
  var oldCS = app.coordinateSystem;
  var d = app.open(cp);
  if (d.fullName.fsName.indexOf("/_build/studio/.ai_copies/") < 0) return "STOPPED: not a copy " + d.fullName.fsName;
  try {
    app.coordinateSystem = CoordinateSystem.DOCUMENTCOORDINATESYSTEM;
    for (var l = 0; l < d.layers.length; l++) if (d.layers[l].name.indexOf("Dieline") == 0) d.layers[l].visible = false;
    var art = d.layers.getByName("Artwork"); art.locked = false; art.visible = true; d.activeLayer = art;
    var font = app.textFonts.getByName("NotoSerif-Italic");
    var subs = [];
    for (var i = 0; i < d.groupItems.length; i++) if (d.groupItems[i].name == "Implant Care") subs.push(d.groupItems[i]);
    if (!subs.length) return "STOPPED: no 'Implant Care' groups";
    function firstFill(g) {
      if (g.compoundPathItems.length) return g.compoundPathItems[0].pathItems[0].fillColor;
      if (g.pathItems.length) return g.pathItems[0].fillColor;
      for (var k = 0; k < g.groupItems.length; k++) { var c = firstFill(g.groupItems[k]); if (c) return c; }
      return null;
    }
    function paint(g, col) {
      for (var k = 0; k < g.compoundPathItems.length; k++) for (var m = 0; m < g.compoundPathItems[k].pathItems.length; m++) g.compoundPathItems[k].pathItems[m].fillColor = col;
      for (var k2 = 0; k2 < g.pathItems.length; k2++) g.pathItems[k2].fillColor = col;
      for (var k3 = 0; k3 < g.groupItems.length; k3++) paint(g.groupItems[k3], col);
    }
    function outlined(txt) {
      var t = art.textFrames.add(); t.contents = txt;
      t.textRange.characterAttributes.textFont = font; t.textRange.characterAttributes.size = 10;
      t.position = [0, 0];
      return t.createOutline();
    }
    var lockupOf = function (g) { return g.parent; };
    for (var r = 0; r < RANGES.length; r++) {
      var label = RANGES[r][0], made = [];
      for (var s = 0; s < subs.length; s++) {
        var g = subs[s], gb = g.geometricBounds, col = firstFill(g);
        // upside down (the lid) when the subline sits above the wordmark in its lockup
        var wm = null, lk = lockupOf(g);
        for (var q = 0; q < lk.groupItems.length; q++) if (lk.groupItems[q].name == "ovoss wordmark") wm = lk.groupItems[q];
        var flipped = wm && ((gb[1] + gb[3]) / 2 > (wm.geometricBounds[1] + wm.geometricBounds[3]) / 2);
        var pair = art.groupItems.add();
        var ref = outlined("Implant Care"); ref.name = "REF"; ref.move(pair, ElementPlacement.PLACEATEND);
        var nw = outlined(label); nw.name = "NEW"; nw.move(pair, ElementPlacement.PLACEATEND);
        ref = pair.groupItems.getByName("REF"); nw = pair.groupItems.getByName("NEW");
        var rb = ref.geometricBounds, k = (gb[2] - gb[0]) / (rb[2] - rb[0]) * 100;
        pair.resize(k, k);
        if (flipped) pair.rotate(180);
        rb = ref.geometricBounds;
        pair.translate(gb[0] - rb[0], gb[1] - rb[1]);
        var nb = nw.geometricBounds;
        nw.translate((gb[0] + gb[2]) / 2 - (nb[0] + nb[2]) / 2, 0);
        ref.remove();
        if (col) paint(nw, col);
        g.hidden = true;
        made.push(pair);
      }
      d.artboards[0].artboardRect = [0, 320.03 * MM, 276.44 * MM, 0];
      d.artboards.setActiveArtboardIndex(0);
      var o = new ExportOptionsPNG24(); o.artBoardClipping = true; o.horizontalScale = 500; o.verticalScale = 500; o.antiAliasing = true; o.transparency = false;
      d.exportFile(new File(OUT.fsName + "/carton-" + RANGES[r][1] + ".png"), ExportType.PNG24, o);
      LOG.push("carton-" + RANGES[r][1] + ".png");
      for (var mm2 = 0; mm2 < made.length; mm2++) made[mm2].remove();
      for (var s2 = 0; s2 < subs.length; s2++) subs[s2].hidden = false;
    }
  } finally {
    d.close(SaveOptions.DONOTSAVECHANGES); // our copy only (path checked above)
    app.coordinateSystem = oldCS; app.userInteractionLevel = oldUIL;
    if (keep) try { app.activeDocument = keep; } catch (e) {}
  }
  return "Exported: " + LOG.join(", ");
})();
