"""Animate plates into 5-second clips with Kling v3 Pro on fal.ai (image to video, no audio).

Dry run by default: prints what would be sent and the bill. Spends only with --go.
    python3 experiments/003-spider-probe/video/kling.py            # dry run
    python3 experiments/003-spider-probe/video/kling.py --go       # submit, poll, download
    python3 experiments/003-spider-probe/video/kling.py --go --only j2
Clips land in video/out/<id>.mp4 with a jobs.json log. FAL_KEY is read from the macOS Keychain at call time.
"""
import base64, io, json, subprocess, sys, time, urllib.request
from pathlib import Path
from PIL import Image

HERE = Path(__file__).resolve().parent
ALIGN = HERE.parent / 'alignment'
OUT = HERE / 'out'
URL = 'https://queue.fal.run/fal-ai/kling-video/v3/pro/image-to-video'
RATE, SECONDS = 0.112, 5                      # USD per second with audio off, measured 2026-09-09
NEG = 'blur, distortion, extra legs, text'
# Kling structure: subject -> movement -> scene -> camera -> light; 40-70 words; camera locked off.
JOBS = {
    'k1': ('out3/k1-plate.png', 'A wolf spider steps slowly forward out of the torchlight across wet moss and fallen oak leaves, its eight legs moving in a natural walking gait. The forest floor stays still. Locked-off camera. One low warm torch, deep black beyond, dew glinting on the moss.'),
    'k2': ('out3/k2-plate.png', 'The wolf spider walks forward over dewy moss, each leg lifting and placing deliberately, body steady; dew drops tremble as it passes. Locked-off macro camera, shallow depth of field. Deep black background, one low warm light from the left.'),
    'k3': ('out3/k3-plate.png', 'The wolf spider walks steadily from left to right along the mossy log, eight legs moving in a natural gait, body level, never leaving the log. Locked-off side-on camera. Deep black background, one low warm light.'),
    's3': ('out5/s3-iridescent.png', 'The peacock spider steps forward across the dark moss, legs lifting deliberately, its iridescent blue and red body catching the light as it turns slightly. The moss stays still. Locked-off macro camera. One cool soft light, deep black background.'),
    'j1': ('out4/j1-plate.png', 'The moon jellyfish drifts slowly upward, its bell pulsing in a steady rhythm, tentacles trailing and swaying; kelp sways gently and fine particles drift through the torchlight. Locked-off camera. Dark rock pool at night, one low side light.'),
    'j2': ('out4/j2-plate.png', 'The jellyfish pulses and drifts slowly, long fine tentacles flowing behind it; bioluminescent plankton sparks flicker around it and the seagrass sways. Locked-off camera, close and low. Dark open water.'),
    'j3': ('out4/j3-plate.png', 'Three comb jellies drift independently, their iridescent comb rows rippling with travelling light; the seaweed frond sways softly beside them. Locked-off camera. Black water, one soft light.'),
}


def key():
    return subprocess.run(['security', 'find-generic-password', '-s', 'FAL_KEY', '-w'], capture_output=True, text=True, check=True).stdout.strip()


def data_uri(p):
    im = Image.open(p).convert('RGB'); im = im.resize((1920, 1080), Image.LANCZOS) if im.size != (1920, 1080) else im
    b = io.BytesIO(); im.save(b, 'JPEG', quality=90)
    return 'data:image/jpeg;base64,' + base64.b64encode(b.getvalue()).decode()


def call(url, k, body=None):
    req = urllib.request.Request(url, data=json.dumps(body).encode() if body is not None else None,
                                 headers={'Authorization': f'Key {k}', 'Content-Type': 'application/json'}, method='POST' if body is not None else 'GET')
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read())


def main():
    go = '--go' in sys.argv
    only = sys.argv[sys.argv.index('--only') + 1].split(',') if '--only' in sys.argv else list(JOBS)
    jobs = {j: JOBS[j] for j in only}
    missing = [j for j, (p, _) in jobs.items() if not (ALIGN / p).exists()]
    for j, (p, prompt) in jobs.items():
        print(f'{j}: {p}  ({len(prompt.split())} words)')
    bill = len(jobs) * SECONDS * RATE
    print(f'\n{len(jobs)} clips x {SECONDS}s x ${RATE}/s = ${bill:.2f}')
    if missing:
        raise SystemExit(f'missing plates: {missing}')
    if not go:
        print('dry run: nothing sent. Add --go to spend.'); return
    k = key(); OUT.mkdir(exist_ok=True); log = OUT / 'jobs.json'
    state = json.loads(log.read_text()) if log.exists() else {}
    for j, (p, prompt) in jobs.items():
        r = call(URL, k, {'prompt': prompt, 'start_image_url': data_uri(ALIGN / p), 'duration': str(SECONDS), 'generate_audio': False,
                          'negative_prompt': NEG, 'cfg_scale': 0.6})
        state[j] = {'request_id': r.get('request_id'), 'status_url': r.get('status_url'), 'response_url': r.get('response_url'), 'prompt': prompt, 'submitted': time.time()}
        print('submitted', j, r.get('request_id')); log.write_text(json.dumps(state, indent=1))
    pending = set(jobs)
    while pending:
        time.sleep(20)
        for j in list(pending):
            s = call(state[j]['status_url'], k)
            if s.get('status') == 'COMPLETED':
                res = call(state[j]['response_url'], k); url = res['video']['url']
                urllib.request.urlretrieve(url, OUT / f'{j}.mp4'); state[j]['video'] = url; state[j]['done'] = time.time()
                print('done', j); pending.discard(j); log.write_text(json.dumps(state, indent=1))
            elif s.get('status') not in ('IN_QUEUE', 'IN_PROGRESS'):
                print('failed', j, s); state[j]['error'] = s; pending.discard(j); log.write_text(json.dumps(state, indent=1))
    print(f'finished. Spent about ${bill:.2f}')


if __name__ == '__main__':
    main()
