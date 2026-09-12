"""The one piece of the tiles layer that can be checked without a key.

Task 002. Everything else about the layer needs Google to answer — but the
arithmetic that decides WHERE the real town lands does not, and it is the part
most likely to be quietly wrong. Getting it wrong does not throw: the town
simply sits somewhere else, or faces the wrong way, and the first version of
the local session's test did exactly that because it trusted a plugin's axis
convention.

So: build a basis by hand, put a point at a known place in our own frame, and
require the matrix to bring it back to the coordinates we started with. Local
metres are x east, y above ordnance datum, z SOUTH — the sign that catches
everybody — and the lift is checked too, because the offset between our LiDAR
and their photogrammetry is applied there and nowhere else.

  python3 scripts/test_tiles_frame.py
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GV = ROOT / "experiments" / "002-living-map" / "golden-valley"
THREE = ROOT / "experiments" / "002-living-map" / "terrain" / "vendor" / "three.module.min.js"

# A basis deliberately not axis-aligned: an identity-shaped one would pass
# with the transpose, the negation and the ordering all wrong.
NODE = r"""
import * as THREE from 'three';
import { intoLocalFrame, wantsTiles } from '%s';

// East, north, up as an orthonormal set rotated well away from the axes, and
// an origin far from zero — which is what the real one is, since the tileset
// is recentred but not to our box.
const yaw = 0.7, pitch = 0.35;
const u = new THREE.Vector3(Math.sin(pitch), Math.cos(pitch), 0).normalize();
let e = new THREE.Vector3(Math.cos(yaw), 0, Math.sin(yaw));
e.sub(u.clone().multiplyScalar(e.dot(u))).normalize();
const n = new THREE.Vector3().crossVectors(u, e).normalize();
const o = new THREE.Vector3(1234.5, -678.9, 4321.0);

const CASES = [
  [0, 0, 0], [123, 64, 0], [-138, 43, -190], [1000, 12.25, -1000],
  [-999.5, 0.5, 999.5],
];

function run(lift) {
  const m = intoLocalFrame({ o, e, n, u }, lift);
  return CASES.map(([x, y, z]) => {
    // Where a point at our (x, y, z) sits in the tiles' own world...
    const world = o.clone()
      .addScaledVector(e, x)
      .addScaledVector(u, y)
      .addScaledVector(n, -z);
    // ...and where the frame matrix says it is in ours.
    const back = world.applyMatrix4(m);
    return { want: [x, y + lift, z], got: back.toArray() };
  });
}

// Every camera the piece actually puts you at, with the two quantities the
// melt gate is given: height above the ground beneath, and distance to the
// ground at the centre of the frame. Measured on the running map, 12 Sep.
const CAMERAS = [
  // the five place photographs — all must keep the real town
  { name: 'gchq',                   above:  67, focus:  254, want: true },
  { name: 'gchq-meadow',            above:  79, focus:  184, want: true },
  { name: 'campus-courtyards',      above: 190, focus:  378, want: true },
  { name: 'panels-and-glasshouses', above: 210, focus:  537, want: true },
  { name: 'cyber-central',          above: 175, focus: 1032, want: true },
  // the five held shots, at rest
  { name: 'the-vale',               above: 386, focus: 1218, want: true },
  { name: 'the-campus',             above: 197, focus:  649, want: true },
  { name: 'the-meadow-roof',        above: 235, focus:  814, want: true },
  { name: 'the-homes',              above: 133, focus:  707, want: true },
  { name: 'the-panels',             above: 207, focus:  561, want: true },
  // and everything that must fall back to our own model
  { name: 'walk, level ahead',      above:  14, focus: 1400, want: false },
  { name: 'walk, looking down',     above:  14, focus:   80, want: false },
  { name: 'arrival at 1.6 m',       above: 1.6, focus:  900, want: false },
  { name: 'arrival, at the ground', above: 1.6, focus:    4, want: false },
  { name: 'low hover, steep down',  above:  55, focus:   78, want: false },
];

const gate = CAMERAS.map((c) => ({
  ...c,
  // Approaching from either state: a camera that belongs in the real town must
  // reach it from cold, and one that does not must not be held there warm.
  fromOff: wantsTiles(false, c.above, c.focus),
  fromOn: wantsTiles(true, c.above, c.focus),
}));

// The gate must never chatter: nothing may be on from cold yet off when warm.
const chatter = gate.filter((g) => g.fromOff && !g.fromOn);

console.log(JSON.stringify({
  flat: run(0), lifted: run(2.75), gate, chatter,
}));
"""

checks = []


def check(name, ok, detail=""):
    checks.append(bool(ok))
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))


def main():
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        # Node resolves a bare 'three' only through node_modules, and the map
        # resolves it through an import map. One tiny package bridges them so
        # the module under test is the one that ships, unmodified.
        pkg = tmp / "node_modules" / "three"
        pkg.mkdir(parents=True)
        (pkg / "package.json").write_text(
            json.dumps({"name": "three", "type": "module", "main": "three.js"}))
        (pkg / "three.js").write_text(THREE.read_text())
        # Node resolves a bare import relative to the importing FILE, not the
        # working directory, so the module has to sit beside that node_modules.
        # Copied byte for byte rather than edited: a test that adjusts the
        # thing it is testing is testing the adjustment.
        copy = tmp / "tiles.js"
        copy.write_bytes((GV / "tiles.js").read_bytes())
        src = tmp / "run.mjs"
        src.write_text(NODE % "./tiles.js")
        r = subprocess.run(["node", str(src)], capture_output=True, text=True,
                           cwd=tmp)
        print("the frame that places the real town")
        if r.returncode:
            check("the module loads outside a browser", False,
                  " / ".join(r.stderr.strip().splitlines()[:6])[:400]
                  if r.stderr else "")
            return 1
        out = json.loads(r.stdout.strip().splitlines()[-1])

    worst = 0.0
    for row in out["flat"]:
        worst = max(worst, max(abs(a - b) for a, b in zip(row["want"], row["got"])))
    check("a point in our metres comes back as the same point",
          worst < 1e-3, f"worst {worst * 1000:.3f} mm over {len(out['flat'])} points")

    # The sign that would pass a symmetric check while putting the town
    # backwards: a point 190 m north must come back at z = -190.
    south = next(r for r in out["flat"] if r["want"][2] == -190)
    check("north is negative z, not positive",
          abs(south["got"][2] - (-190)) < 1e-3,
          f"z {south['got'][2]:.3f} for a point 190 m north of the centre")

    lifted = 0.0
    for row in out["lifted"]:
        lifted = max(lifted, max(abs(a - b) for a, b in zip(row["want"], row["got"])))
    check("the lift raises the tiles and nothing else",
          lifted < 1e-3, f"2.75 m applied, worst error {lifted * 1000:.3f} mm")

    # The melt gate. Height alone shipped once and cost the two closest places:
    # gchq sits 67 m up but 212 m from the building it frames, and its tiles
    # measured 6.02 against a target of 6. So the gate is asked how far away
    # what you are LOOKING AT is, with height kept only as a floor.
    gate = out["gate"]
    kept = [g for g in gate if g["want"]]
    dropped = [g for g in gate if not g["want"]]

    wrong = [g["name"] for g in kept if not g["fromOff"]]
    check("every place and shot keeps the real town",
          not wrong,
          f"{len(kept)} cameras" if not wrong else "lost: " + ", ".join(wrong))

    wrong = [g["name"] for g in dropped if g["fromOn"]]
    check("the walk and every arrival fall back to our model",
          not wrong,
          f"{len(dropped)} cameras" if not wrong else "kept: " + ", ".join(wrong))

    # The regression itself, named so it cannot come back quietly: a gate on
    # height alone drops gchq (67 m) and gchq-meadow (79 m).
    low = [g for g in kept if g["above"] < 105]
    check("a camera low over the ground but far from its subject is not dropped",
          low and all(g["fromOff"] for g in low),
          ", ".join(f"{g['name']} {g['above']}m up, {g['focus']}m out"
                    for g in low))

    check("the gate cannot chatter", not out["chatter"],
          "nothing switches on from cold that switches off when warm"
          if not out["chatter"]
          else ", ".join(g["name"] for g in out["chatter"]))

    print(f"\n{sum(checks)}/{len(checks)} checks passed")
    return 0 if all(checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
