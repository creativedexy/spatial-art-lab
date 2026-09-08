"""Generate a first/last-frame descent clip for the living map.

Bridges two owned images into a continuous video descent using Veo 3.1's
frames-to-video mode via the Gemini API.

Give it BOTH frames. Session C measured what happens otherwise: the seam
where the clip hands back to the live map is insensitive to video quality and
very sensitive to where the clip lands — five metres of drift is a five-fold
jump in error. So frame B should be rendered from our own scene at the
destination camera (`scripts/capture_descent_path.py` writes exactly that as
`descent/frames/*-landing-frameB.png`), not chosen by the generator and not a
loose photograph. See experiments/002-living-map/descent/seam-report.json.

Usage:
  export GEMINI_API_KEY=...   (never commit the key)
  pip install google-genai
  python3 scripts/generate_descent.py FRAME_A FRAME_B OUT_DIR \
      [--prompt "..."] [--candidates 3] [--model veo-3.1-generate-preview]

Each candidate is saved as OUT_DIR/candidate-N.mp4 with a run log
OUT_DIR/run-log.json recording prompt, model, timings and file sizes —
the session-log discipline for paid generation.
"""
import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_PROMPT = (
    "Smooth continuous aerial descent. The camera flies forward and down "
    "from the high aerial view in the first frame, easing into the exact "
    "position and framing of the last frame. Terrain and buildings stay "
    "rigid and consistent; no new structures appear; realistic parallax; "
    "soft afternoon light, gentle atmospheric haze. No people, no text."
)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("frame_a")
    ap.add_argument("frame_b", nargs="?", default=None,
                    help="optional: omit to generate from frame A alone "
                         "(image-to-video, no last-frame anchor)")
    ap.add_argument("out_dir")
    ap.add_argument("--prompt", default=DEFAULT_PROMPT)
    ap.add_argument("--candidates", type=int, default=3)
    ap.add_argument("--model", default="veo-3.1-generate-preview")
    args = ap.parse_args()

    if not os.environ.get("GEMINI_API_KEY"):
        sys.exit("GEMINI_API_KEY is not set. Add it to the environment "
                 "(claude.ai code environment settings, or your shell) "
                 "and re-run.")

    from google import genai
    from google.genai import types

    client = genai.Client()
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    log = {
        "startedUtc": datetime.now(timezone.utc).isoformat(),
        "model": args.model,
        "prompt": args.prompt,
        "frameA": args.frame_a,
        "frameB": args.frame_b,
        "candidates": [],
    }

    for i in range(args.candidates):
        t0 = time.time()
        cfg = {"aspect_ratio": "16:9"}
        if args.frame_b:
            cfg["last_frame"] = types.Image.from_file(location=args.frame_b)
        op = client.models.generate_videos(
            model=args.model,
            prompt=args.prompt,
            image=types.Image.from_file(location=args.frame_a),
            config=types.GenerateVideosConfig(**cfg),
        )
        while not op.done:
            time.sleep(10)
            op = client.operations.get(op)
        entry = {"index": i, "seconds": round(time.time() - t0, 1)}
        if op.error:
            entry["error"] = str(op.error)
        else:
            video = op.response.generated_videos[0]
            path = out / f"candidate-{i}.mp4"
            client.files.download(file=video.video)
            video.video.save(str(path))
            entry["file"] = path.name
            entry["bytes"] = path.stat().st_size
        log["candidates"].append(entry)
        print(json.dumps(entry))

    with open(out / "run-log.json", "w") as f:
        json.dump(log, f, indent=2)
    print(f"wrote {out}/run-log.json")


if __name__ == "__main__":
    main()
