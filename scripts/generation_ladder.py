"""The generation ladder — does our structure carry a photoreal model?

The question this exists to settle, cheaply and with evidence rather than
opinion: **do we need to spend sessions in Blender adding detail, or is what
we already have enough to condition a generator on?**

The bet is that an image or video model does not need our render to be
realistic, it needs it to be *unambiguous*. It can invent brick, slate, tarmac
wear and undergrowth. It cannot invent that GCHQ is 14.8 m on a 52.7 m base,
that the ridge runs with the street, or the shape of the ground under it —
and those we have, measured to the metre. If that is right, Blender is the
wrong place to spend, because hand-modelling this hill does not transfer to
the next postcode and the measurement does.

Four rungs, cheapest first, each a gate on the next. Stop at any rung that
answers the question.

  0  dry-run        free      prints every request, spends nothing
  1  still, beauty  pennies   our render → photoreal. Does it keep the town?
  2  still, depth   pennies   the same view conditioned on structure instead.
                              Rung 2 beating rung 1 means the geometry is
                              doing the work and Blender detail is irrelevant.
  3  video, low     ~£0.40    a departure from the low approach, where the
                              detail density is manageable
  4  video, aerial  ~£0.40    the same from the wide shot, which Session B
                              measured as three times harder. If 3 works and
                              4 does not, that is the answer, not a failure.

**What to look at is the failure mode, not the score.** Three different
failures point three different ways:

  it invents the wrong buildings   → a conditioning problem. More detail in
                                     our input will not help; better structure
                                     conditioning might.
  everything goes plastic          → a prompt or model problem. Free to fix.
  it cannot tell brick from render → material hints would help, and those are
                                     cheap raster work in the pipeline we own
                                     (OSM tags, the land class map) — not a
                                     Blender session.

Only a failure that *geometry* would fix earns a session in Blender, and I
would be surprised.

Usage:
  export FAL_KEY=...              # never commit it, never paste it anywhere
  pip install fal-client pillow
  python3 scripts/generation_ladder.py --dry-run          # always first
  python3 scripts/generation_ladder.py --rungs 1
  python3 scripts/generation_ladder.py --rungs 2
  python3 scripts/generation_ladder.py --rungs 3,4

Model ids are the part that goes stale. Every one below is a *suggestion*,
not a verified entry: check it on fal.ai and pass --model-<rung> to override.
--dry-run prints exactly what would be sent so a wrong id costs nothing.
"""
import argparse
import json
import os
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PASSES = ROOT / "experiments" / "002-living-map" / "passes" / "out"
OUT = ROOT / "experiments" / "002-living-map" / "ladder"

# What we are asking for, in words. Deliberately about *materials and light*
# and never about layout: the layout is the thing we are supplying, and a
# prompt that describes it invites the model to reinvent it.
LOOK = (
    "Aerial photograph of the western edge of Cheltenham, Gloucestershire, "
    "England. Late afternoon sun, low and warm, long shadows. Red brick and "
    "pale render semi-detached houses with grey slate and clay tile roofs, "
    "asphalt roads with painted markings, mature deciduous trees in full "
    "summer leaf, mown playing fields and pasture divided by hedgerows. "
    "Photographic, shot on a full-frame camera from a light aircraft, "
    "natural colour, gentle atmospheric haze. No text, no watermark, no people."
)
KEEP = (
    " Keep the layout, the building positions, the road network and the "
    "terrain exactly as given; change only materials, texture and light."
)
MOTION = (
    "Slow continuous aerial descent, camera moving forward and down. "
    "Buildings and terrain stay rigid; correct parallax; one unbroken shot, "
    "no cuts, no new structures appearing. No text, no people, no vehicles."
)

RUNGS = {
    1: {
        "kind": "image",
        "why": "our own render, straight to photoreal — the cheapest signal",
        "model": "fal-ai/flux/dev/image-to-image",
        "inputs": ["aerial-beauty.png"],
        "args": lambda p: {
            "prompt": LOOK + KEEP,
            "image_url": p[0],
            # Low enough that the geometry survives, high enough that the
            # clay-model look does not. This is the number to sweep first if
            # the rung is ambiguous.
            "strength": 0.62,
            "num_images": 2,
        },
    },
    2: {
        "kind": "image",
        "why": "the same view conditioned on depth instead of on our picture",
        "model": "fal-ai/flux-control-lora-depth",
        "inputs": ["aerial-depth.png"],
        "args": lambda p: {
            "prompt": LOOK,
            # Verified against the endpoint's OpenAPI schema, not the docs page:
            # the field is control_lora_image_url, and preprocess_depth defaults
            # to True — which would run a depth *estimator* over our measured
            # depth pass and throw away the very thing this rung tests.
            "control_lora_image_url": p[0],
            "preprocess_depth": False,
            # Our frame is 1280x720; the endpoint default is landscape_4_3,
            # which would letterbox or crop the structure we are conditioning on.
            "image_size": "landscape_16_9",
            "num_images": 2,
        },
    },
    3: {
        "kind": "video",
        "why": "a departure from the low approach — few large masses, the "
               "case Session B measured as easy",
        "model": "fal-ai/kling-video/v1.6/pro/image-to-video",
        "inputs": ["approach-beauty.png"],
        "args": lambda p: {
            "prompt": MOTION + " " + LOOK,
            "image_url": p[0],
            "duration": "5",
        },
    },
    4: {
        "kind": "video",
        "why": "the same from the wide aerial — thousands of tiny buildings, "
               "the case Session B measured at twice the error",
        "model": "fal-ai/kling-video/v1.6/pro/image-to-video",
        "inputs": ["aerial-beauty.png"],
        "args": lambda p: {
            "prompt": MOTION + " " + LOOK,
            "image_url": p[0],
            "duration": "5",
        },
    },
}


def find_url(payload, suffixes):
    """fal nests its output differently per model; find the first file URL."""
    if isinstance(payload, dict):
        u = payload.get("url")
        if isinstance(u, str) and any(s in u for s in suffixes):
            return u
        for v in payload.values():
            found = find_url(v, suffixes)
            if found:
                return found
    elif isinstance(payload, list):
        for v in payload:
            found = find_url(v, suffixes)
            if found:
                return found
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rungs", default="1", help="comma separated, e.g. 3,4")
    ap.add_argument("--dry-run", action="store_true",
                    help="print the exact requests and spend nothing")
    ap.add_argument("--passes", default=str(PASSES),
                    help="where capture_passes.py wrote its images")
    ap.add_argument("--out", default=str(OUT))
    for r in RUNGS:
        ap.add_argument(f"--model-{r}", default=None,
                        help=f"override rung {r}'s model id")
    args = ap.parse_args()

    passes = Path(args.passes)
    out = Path(args.out)
    rungs = [int(r) for r in args.rungs.split(",") if r.strip()]
    for r in rungs:
        if r not in RUNGS:
            sys.exit(f"no rung {r}; known: {', '.join(map(str, RUNGS))}")

    missing = [f for r in rungs for f in RUNGS[r]["inputs"] if not (passes / f).exists()]
    if missing:
        sys.exit(f"missing pass images: {', '.join(missing)}\n"
                 f"run:  python3 scripts/capture_passes.py")

    if args.dry_run:
        for r in rungs:
            spec = RUNGS[r]
            model = getattr(args, f"model_{r}") or spec["model"]
            body = spec["args"]([f"<uploaded {f}>" for f in spec["inputs"]])
            print(json.dumps({
                "rung": r, "kind": spec["kind"], "why": spec["why"],
                "model": model, "arguments": body,
                "inputs": [str(passes / f) for f in spec["inputs"]],
                "FAL_KEY": "set" if os.environ.get("FAL_KEY") else "NOT SET",
            }, indent=2))
        print("\ndry run — nothing sent. Check each model id on fal.ai before "
              "spending; --model-N overrides one.")
        return

    if not os.environ.get("FAL_KEY"):
        sys.exit("FAL_KEY is not set. Export it in this shell (never commit "
                 "it) and re-run. Try --dry-run first.")

    import fal_client

    out.mkdir(parents=True, exist_ok=True)
    log_path = out / "ladder-log.json"
    log = json.loads(log_path.read_text()) if log_path.exists() else {"runs": []}

    for r in rungs:
        spec = RUNGS[r]
        model = getattr(args, f"model_{r}") or spec["model"]
        entry = {"rung": r, "kind": spec["kind"], "why": spec["why"],
                 "model": model, "startedUtc": datetime.now(timezone.utc).isoformat(),
                 "inputs": spec["inputs"]}
        t0 = time.time()
        try:
            uploaded = [fal_client.upload_file(str(passes / f)) for f in spec["inputs"]]
            body = spec["args"](uploaded)
            entry["prompt"] = body.get("prompt")
            result = fal_client.subscribe(model, arguments=body, with_logs=False)
            suffixes = (".mp4", ".webm") if spec["kind"] == "video" else (
                ".png", ".jpg", ".jpeg", ".webp")
            url = find_url(result, suffixes)
            if not url:
                entry["error"] = f"no output URL: {json.dumps(result)[:400]}"
            else:
                ext = url.rsplit(".", 1)[-1].split("?")[0][:4]
                dest = out / f"rung{r}-{Path(spec['inputs'][0]).stem}.{ext}"
                with urllib.request.urlopen(url) as resp, open(dest, "wb") as f:
                    f.write(resp.read())
                entry["file"] = dest.name
                entry["bytes"] = dest.stat().st_size
        except Exception as exc:                     # keep the log honest
            entry["error"] = f"{type(exc).__name__}: {exc}"
        entry["seconds"] = round(time.time() - t0, 1)
        log["runs"].append(entry)
        print(json.dumps(entry, indent=2))
        log_path.write_text(json.dumps(log, indent=2))
        if entry.get("error"):
            sys.exit("stopping rather than spending on the next rung — log the "
                     "error above verbatim and work out why.")

    print(f"\nwrote {log_path}")
    print("Now look at the *failure mode*, not the score. Wrong buildings is a "
          "conditioning problem; plastic is a prompt problem; brick-versus-"
          "render is a material-hint problem. None of those is Blender.")


if __name__ == "__main__":
    main()
