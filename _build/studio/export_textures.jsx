// Ovoss studio: export artwork-only textures from the print .ai files, for the 3D renders.
// Works on COPIES in .ai_copies/ (never opens, saves or closes Joey's real files).
// Run: osascript -e 'with timeout of 600 seconds' -e 'tell application "Adobe Illustrator" to do javascript file (POSIX file "<abs path>/export_textures.jsx")' -e 'end timeout'
var MM = 2.834645669, LOG = [];
var HERE = File($.fileName).parent;                       // _build/studio
var SRC = new Folder(HERE.fsName + "/../../../Ovoss Packaging");
var COPIES = new Folder(HERE.fsName + "/.ai_copies"), TEX = new Folder(HERE.fsName + "/tex");
if (!COPIES.exists) COPIES.create(); if (!TEX.exists) TEX.create();
var FILES = {
  carton: "Ovoss_Toothpaste_Carton_75ml.ai",
  tube: "Ovoss_Toothpaste_Tube_Label_75ml.ai",
  mw: "Ovoss_Mouthwash_Labels_500ml.ai"
};
// 1. If a source file is open with unsaved edits, the file on disk is stale: stop.
var stale = [];
for (var i = 0; i < app.documents.length; i++) { var d0 = app.documents[i], p0 = ""; try { p0 = d0.fullName.fsName; } catch (e) {}
  for (var f in FILES) if (p0 == new File(SRC.fsName + "/" + FILES[f]).fsName && !d0.saved) stale.push(FILES[f]); }
if (stale.length) { "STOPPED: unsaved edits open in Illustrator: " + stale.join(", ") + ". Save them first."; }
else {
  app.userInteractionLevel = UserInteractionLevel.DONTDISPLAYALERTS;
  var keep = null; try { keep = app.activeDocument; } catch (e) {}
  var oldCS = app.coordinateSystem;
  function exportArt(key, jobs, dieLayer) {
    var src = new File(SRC.fsName + "/" + FILES[key]), cp = new File(COPIES.fsName + "/" + key + "_copy.ai");
    if (cp.exists) cp.remove(); if (!src.copy(cp.fsName)) throw "copy failed " + src.fsName;
    var d = app.open(cp);
    if (d.fullName.fsName.indexOf("/_build/studio/.ai_copies/") < 0) throw "not a copy: " + d.fullName.fsName;
    app.coordinateSystem = CoordinateSystem.DOCUMENTCOORDINATESYSTEM;
    if (dieLayer) { var g = d.layers.getByName(dieLayer).pageItems[0].geometricBounds; jobs[0].rect = [g[0] / MM, g[1] / MM, g[2] / MM, g[3] / MM]; }
    // hide dielines; keep the tube's printed eye mark ("Artwork + Reg.")
    for (var l = 0; l < d.layers.length; l++) if (d.layers[l].name.indexOf("Dieline") == 0 && d.layers[l].name != "Dieline - Artwork + Reg.") d.layers[l].visible = false;
    for (var j = 0; j < jobs.length; j++) {
      var r = jobs[j].rect;
      d.artboards[0].artboardRect = [r[0] * MM, r[1] * MM, r[2] * MM, r[3] * MM];
      d.artboards.setActiveArtboardIndex(0);
      var o = new ExportOptionsPNG24(); o.artBoardClipping = true; o.horizontalScale = jobs[j].scale; o.verticalScale = jobs[j].scale; o.antiAliasing = true; o.transparency = false;
      d.exportFile(new File(TEX.fsName + "/" + jobs[j].name + ".png"), ExportType.PNG24, o);
      LOG.push(jobs[j].name + ".png");
    }
    d.close(SaveOptions.DONOTSAVECHANGES); // our copy only (path checked above)
  }
  // Carton: whole sheet (wave runs across the panels), mapped per face in studio.html.
  exportArt("carton", [{ name: "carton", rect: [0, 320.03, 276.44, 0], scale: 500 }]);
  // Mouthwash: front die 0-59 x 0-125, provisional back die +80 mm.
  exportArt("mw", [{ name: "mw-front", rect: [0, 125, 59, 0], scale: 700 }, { name: "mw-back", rect: [80, 125, 139, 0], scale: 700 }]);
  // Tube: the 114 x 103 mm label die cut.
  exportArt("tube", [{ name: "tube-label", rect: null, scale: 600 }], "Dieline - LABEL DIE CUT");
  app.coordinateSystem = oldCS;
  if (keep) try { app.activeDocument = keep; } catch (e) {}
  "Exported: " + LOG.join(", ");
}
