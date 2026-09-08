"""Generate a descent clip for the living map, from our own anchor frames.

Bridges two owned images into a continuous video descent — Veo 3.1 via the
Gemini API, or a first/last-frame model on fal.ai.

Give it BOTH frames. Session C measured what happens otherwise: the seam
where the clip hands back to the live map is insensitive to video quality and
very sensitive to where the clip lands — five metres of drift is a five-fold
jump in error. So frame B should be rendered from our own scene at the
destination camera (`scripts/capture_descent_path.py` writes exactly that as
`descent/frames/*-landing-frameB.png`), not chosen by the generator and not a
loose photograph. See experiments/002-living-map/descent/seam-report.json.

There are two species of descent and they want different prompts:

  return     map -> clip -> back to the map. Both anchors come from our
             scene, and the clip must stay in the map's stylised white-model
             look or the seam fails on style even when it lands perfectly.
             Use --style clay (the default).
  departure  map -> clip -> an authored photoreal scene. Only the in-seam
             has to hold; the clip is *meant* to become the real place.
             Use --style photoreal, and expect to cut, not hand back.

Usage:
  export GEMINI_API_KEY=...        # or FAL_KEY=... for --provider fal
  pip install google-genai         # or: pip install fal-client
  python3 scripts/generate_descent.py FRAME_A [FRAME_B] OUT_DIR \
      [--provider gemini|fal] [--model ...] [--style clay|photoreal] \
      [--prompt "..."] [--candidates 3] [--dry-run]

--dry-run prints the exact request and spends nothing: always run it once
against a new provider or model before paying for candidates.

Each candidate is saved as OUT_DIR/candidate-N.mp4 with a run log
OUT_DIR/run-log.json recording provider, model, prompt, timings and file
sizes — the session-log discipline for paid generation.
"""
import argparse
import json
import os
import sys
import time
import re
import shutil
import subprocess
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

MOTION = (
    "Smooth continuous aerial descent. The camera flies forward and down "
    "from the high aerial view in the first frame, easing into the exact "
    "position and framing of the last frame. Terrain and buildings stay "
    "rigid and consistent; no new structures appear; correct parallax; "
    "one unbroken shot, no cuts. No people, no vehicles, no text."
)
STYLES = {
    # Matches the map's own look, so the hand-back survives on style as well
    # as on geometry.
    "clay": MOTION + (
        " Architectural white model: matte off-white buildings with no "
        "windows or textures, soft pale green terrain, clean studio lighting, "
        "flat even shadows. Not photorealistic, no photographic detail, no "
        "foliage, no signage."
    ),
    # For descents that deliberately arrive somewhere real.
    "photoreal": MOTION + (
        " Photographic aerial cinematography, soft afternoon light, gentle "
        "atmospheric haze, realistic materials and shadows."
    ),
}

# Which argument names each fal model uses for the first and last frame.
# fal changes schemas; --dry-run prints what would be sent, and the model's
# page on fal.ai is the authority. Verified entries only.
FAL_MODELS = {
    "fal-ai/kling-video/v1.6/pro/image-to-video": {
        "first": "image_url", "last": "tail_image_url",
        "duration": "duration", "allowed": ["5", "10"],
    },
    "fal-ai/luma-dream-machine": {
        "first": "image_url", "last": "end_image_url",
        "duration": None, "allowed": None,
    },
}
DEFAULT_MODEL = {
    "gemini": "veo-3.1-generate-preview",
    "fal": "fal-ai/kling-video/v1.6/pro/image-to-video",
}


def clip_seconds(path):
    """How long the delivered clip actually is — models round durations up."""
    try:
        exe = shutil.which("ffmpeg")
        if not exe:
            import imageio_ffmpeg
            exe = imageio_ffmpeg.get_ffmpeg_exe()
        out = subprocess.run([exe, "-i", str(path)], capture_output=True, text=True).stderr
        h, m, sec = re.search(r"Duration: (\d+):(\d+):([\d.]+)", out).groups()
        return round(int(h) * 3600 + int(m) * 60 + float(sec), 2)
    except Exception:
        return None


def find_video_url(payload):
    """fal responses nest the video differently per model; find the URL."""
    if isinstance(payload, dict):
        if isinstance(payload.get("url"), str) and ".mp4" in payload["url"]:
            return payload["url"]
        for value in payload.values():
            found = find_video_url(value)
            if found:
                return found
    elif isinstance(payload, list):
        for value in payload:
            found = find_video_url(value)
            if found:
                return found
    return None


def generate_gemini(args, prompt, index, dest):
    from google import genai
    from google.genai import types

    cfg = {"aspect_ratio": "16:9"}
    if args.frame_b:
        cfg["last_frame"] = types.Image.from_file(location=args.frame_b)
    client = genai.Client()
    op = client.models.generate_videos(
        model=args.model,
        prompt=prompt,
        image=types.Image.from_file(location=args.frame_a),
        config=types.GenerateVideosConfig(**cfg),
    )
    while not op.done:
        time.sleep(10)
        op = client.operations.get(op)
    if op.error:
        return {"error": str(op.error)}
    video = op.response.generated_videos[0].video
    client.files.download(file=video)
    video.save(str(dest))
    return {}


def fal_arguments(args, prompt, upload):
    """The request body, built without uploading anything (so --dry-run is free)."""
    names = FAL_MODELS.get(args.model)
    if names is None:
        sys.exit(f"Unknown fal model {args.model!r}. Add its first/last frame "
                 f"argument names to FAL_MODELS, or pick one of: "
                 f"{', '.join(FAL_MODELS)}")
    body = {"prompt": prompt, names["first"]: upload(args.frame_a)}
    if args.frame_b:
        body[names["last"]] = upload(args.frame_b)
    if names["duration"]:
        # These models offer fixed lengths, so the clip is retimed rather than
        # cut to the path's duration. That is fine — the anchors, not the
        # clock, are what hold the seams.
        allowed = names["allowed"]
        pick = min(allowed, key=lambda d: abs(float(d) - args.seconds))
        if float(pick) != args.seconds:
            print(f"note: {args.model} offers {'/'.join(allowed)} s; asking "
                  f"for {pick} s instead of {args.seconds} s", file=sys.stderr)
        body[names["duration"]] = pick
    return body


def generate_fal(args, prompt, index, dest):
    import fal_client

    body = fal_arguments(args, prompt, fal_client.upload_file)
    result = fal_client.subscribe(args.model, arguments=body, with_logs=False)
    url = find_video_url(result)
    if not url:
        return {"error": f"no video URL in response: {json.dumps(result)[:400]}"}
    with urllib.request.urlopen(url) as r, open(dest, "wb") as f:
        f.write(r.read())
    return {}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("frame_a")
    ap.add_argument("frame_b", nargs="?", default=None,
                    help="the landing anchor: omit only for smoke tests "
                         "(image-to-video, nothing holding the out-seam)")
    ap.add_argument("out_dir")
    ap.add_argument("--provider", choices=("gemini", "fal"), default="gemini")
    ap.add_argument("--model", default=None)
    ap.add_argument("--style", choices=tuple(STYLES), default="clay")
    ap.add_argument("--prompt", default=None, help="overrides --style")
    ap.add_argument("--seconds", type=float, default=4.0)
    ap.add_argument("--candidates", type=int, default=3)
    ap.add_argument("--rate-usd-per-second", type=float, default=None,
                    help="the model's price per second of video, from the "
                         "provider's pricing page. Recorded with the clip's "
                         "real duration so the run log answers 'what did that "
                         "cost?'. Providers do not return a charge, and this "
                         "script will not invent a rate — the dashboard is "
                         "always the authority.")
    ap.add_argument("--dry-run", action="store_true",
                    help="print the request that would be sent, spend nothing")
    args = ap.parse_args()

    args.model = args.model or DEFAULT_MODEL[args.provider]
    prompt = args.prompt or STYLES[args.style]
    key_name = "GEMINI_API_KEY" if args.provider == "gemini" else "FAL_KEY"

    if args.dry_run:
        request = {"provider": args.provider, "model": args.model,
                   "prompt": prompt, "frameA": args.frame_a,
                   "frameB": args.frame_b, "candidates": args.candidates}
        if args.provider == "fal":
            request["arguments"] = fal_arguments(
                args, prompt, lambda p: f"<uploaded {Path(p).name}>")
        request[key_name] = "set" if os.environ.get(key_name) else "NOT SET"
        print(json.dumps(request, indent=2))
        return

    if not os.environ.get(key_name):
        sys.exit(f"{key_name} is not set. Export it in this shell (never "
                 f"commit it) and re-run. Try --dry-run first.")
    if not args.frame_b:
        print("warning: no landing anchor — the clip may end anywhere, and "
              "Session C measured that as the one thing that breaks the seam.",
              file=sys.stderr)

    generate = {"gemini": generate_gemini, "fal": generate_fal}[args.provider]
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    log = {
        "startedUtc": datetime.now(timezone.utc).isoformat(),
        "provider": args.provider,
        "model": args.model,
        "style": args.style,
        "prompt": prompt,
        "frameA": args.frame_a,
        "frameB": args.frame_b,
        "rateUsdPerSecond": args.rate_usd_per_second,
        "candidates": [],
    }

    for i in range(args.candidates):
        t0 = time.time()
        dest = out / f"candidate-{i}.mp4"
        entry = {"index": i}
        try:
            entry.update(generate(args, prompt, i, dest))
        except Exception as exc:                      # keep the log honest
            entry["error"] = f"{type(exc).__name__}: {exc}"
        entry["seconds"] = round(time.time() - t0, 1)
        if dest.exists():
            entry["file"] = dest.name
            entry["bytes"] = dest.stat().st_size
            entry["clipSeconds"] = clip_seconds(dest)
            if args.rate_usd_per_second and entry["clipSeconds"]:
                entry["estimatedCostUsd"] = round(
                    entry["clipSeconds"] * args.rate_usd_per_second, 4)
        log["candidates"].append(entry)
        print(json.dumps(entry))

    with open(out / "run-log.json", "w") as f:
        json.dump(log, f, indent=2)
    total = sum(c.get("estimatedCostUsd", 0) for c in log["candidates"])
    if total:
        print(f"estimated spend: ${total:.2f} — check the provider dashboard "
              f"for the actual charge")
    print(f"wrote {out}/run-log.json")


if __name__ == "__main__":
    main()
