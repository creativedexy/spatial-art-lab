"""Build review/index.html: Probe A's motion test plus the six Codex alignment stills.
Media is embedded so the page opens through vbopen. python3 experiments/003-spider-probe/build_review.py"""
from pathlib import Path
import base64, html, io
from PIL import Image

HERE = Path(__file__).resolve().parent
e = html.escape


def uri(p, maxw=1400):
    p = HERE / p
    if p.suffix == '.mp4':
        return 'data:video/mp4;base64,' + base64.b64encode(p.read_bytes()).decode()
    im = Image.open(p).convert('RGB'); im.thumbnail((maxw, maxw)); b = io.BytesIO(); im.save(b, 'JPEG', quality=84)
    return 'data:image/jpeg;base64,' + base64.b64encode(b.getvalue()).decode()


STILLS = [
    ('01-specimen-cameras.png', 'Specimen with its cameras', 'The spider method: scan, points, the ring of cameras that saw it.', 'Probe A'),
    ('02-tracking-live.png', 'Tracking, live', 'A pose skeleton and joint IDs on an orb-weaver in its web.', 'Probe B'),
    ('03-specimen-archive.png', 'Specimen archive', 'Plexus network, magnified inset, classification labels: the card as the work.', 'Carole Ann, X.F'),
    ('04-web-geometry.png', 'The web as geometry', 'Radial threads, rings and measurement ticks; the animal small at the centre.', 'Probe C'),
    ('05-time-trail.png', 'Time trail on moss', 'The spider’s path through time as copies of itself, the present in a frame.', 'Bilawal Sidhu'),
    ('06-ascii-specimen.png', 'ASCII specimen', 'The spider drawn in monospace characters inside tracking brackets.', 'Ployz, X.F'),
]
STILLS2 = [
    ('07-bark-trail.png', 'Bark trail', 'A wolf spider running a mossy log; five fading copies; skeleton on the present one.', 'round 2'),
    ('08-dew-web-track.png', 'Dew web, tracked', 'An orb-weaver at dawn, dew as points along silk, legs tracked with joint markers.', 'round 2'),
    ('09-leaf-litter.png', 'Leaf litter', 'Ground-level macro among leaves and fern; timestamps follow its route.', 'round 2'),
    ('10-night-torch.png', 'Night torch, three tracked', 'A patch of forest floor with IDs 01 to 03, each with a short trail.', 'round 2'),
]
fig = lambda d, rows: ''.join(f'''<figure><button data-full><img src="{uri(d + f)}" alt="{e(t)}"></button><figcaption><span>{e(tag)}</span><b>{e(t)}</b>{e(dd)}</figcaption></figure>''' for f, t, dd, tag in rows)
cards2 = fig('alignment/out2/', STILLS2)
STILLS3 = [
    ('k1-hud.png', 'K1 · establishing, HUD target', 'Scan sweep, edge ticks, SURFACE RESPONSE | MOSS, one red alert.', 'round 3 · target'),
    ('k1-plate.png', 'K1 · plate', 'No HUD: the first frame a video model would animate.', 'round 3 · plate'),
    ('k2-hud.png', 'K2 · lock-on, HUD target', 'Leg-tip brackets, pose skeleton, L2 FEMUR / R3 TIBIA callouts, telemetry rail.', 'round 3 · target'),
    ('k2-plate.png', 'K2 · plate', 'Macro stride over dewy moss, room on the right for the sidebar.', 'round 3 · plate'),
    ('k3-hud.png', 'K3 · time trail, HUD target', 'Five fading earlier positions, the present framed, TRACK AGE timecode.', 'round 3 · target'),
    ('k3-plate.png', 'K3 · plate', 'Side-on crossing of the log, trail room behind.', 'round 3 · plate'),
]
cards3 = fig('alignment/out3/', STILLS3)
cards = ''.join(f'''<figure><button data-full><img src="{uri('alignment/out/' + f)}" alt="{e(t)}"></button><figcaption><span>{i + 1:02d} · {e(tag)}</span><b>{e(t)}</b>{e(d)}</figcaption></figure>'''
                for i, (f, t, d, tag) in enumerate(STILLS))
video = f'<video src="{uri("render/probe-a-v001.mp4")}" loop muted playsinline controls></video>'
video2 = f'<video src="{uri("render/probe-a-v002.mp4")}" loop muted playsinline controls></video>'
video3 = f'<video src="{uri("render/probe-a-v003.mp4")}" autoplay loop muted playsinline controls></video>'

page = f'''<!doctype html><html lang="en-GB"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Spider alignment review</title>
<style>:root{{--line:#e3e3e0;--mut:#555}}*{{box-sizing:border-box}}body{{margin:0;background:#fff;color:#000;font:15px/1.55 system-ui,-apple-system,sans-serif}}
.wrap{{max-width:1240px;margin:auto;padding:48px 32px 70px}}.eyebrow{{font:600 11px system-ui;letter-spacing:.12em;text-transform:uppercase;color:var(--mut)}}
h1,h2{{font-family:Georgia,serif;font-weight:400}}h1{{font-size:clamp(36px,5.5vw,68px);line-height:1.04;margin:14px 0}}h2{{font-size:32px;margin:48px 0 6px;border-top:1px solid #000;padding-top:18px}}
.lede{{font-size:18px;max-width:64ch;color:#222}}video{{width:100%;display:block;border-radius:12px;background:#000;margin-top:18px}}
.grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:22px;margin-top:18px}}figure{{margin:0;border:1px solid var(--line);border-radius:12px;overflow:hidden}}
figure button{{display:block;width:100%;border:0;padding:0;background:#000;cursor:zoom-in}}figure img{{width:100%;display:block}}
figcaption{{padding:12px 16px 16px;font-size:14px;color:#333}}figcaption span{{display:block;font:600 11px system-ui;letter-spacing:.1em;text-transform:uppercase;color:var(--mut)}}figcaption b{{display:block;font-size:16px;color:#000;margin:3px 0}}
.note{{background:#f5f5f2;border:1px solid var(--line);border-radius:12px;padding:16px 20px;margin-top:18px;max-width:880px}}.note h3{{font-family:Georgia,serif;font-variant:small-caps;font-weight:400;font-size:20px;margin:0 0 6px}}
#lb{{position:fixed;inset:0;background:rgba(0,0,0,.95);display:none;align-items:center;justify-content:center;padding:20px;cursor:zoom-out}}#lb.on{{display:flex}}#lb img{{max-width:100%;max-height:100%}}
@media(max-width:700px){{.wrap{{padding:32px 16px}}.grid{{grid-template-columns:1fr}}}}</style></head><body><div class="wrap">
<p class="eyebrow">Spatial art lab · 003 spider probe · phase: Develop · 22 Sep 2026</p>
<h1>A spider, seen by a machine, in a living place.</h1>
<p class="lede">Newest first. Your picks from round 1 (02 tracking, 05 time trail) are now a motion test in Blender and four new stills with nature first. Say which frames feel like yours; that is the alignment.</p>
<h2>Round 3 · key frames for a 15-second sequence</h2>
<p class="lede">Three shots, each twice: the HUD target (what the finished frame should look like, in Jayse's grammar) and the clean plate (no lines, no text) that a video model would animate. TouchDesigner then tracks the real motion in the clip and draws the HUD, so the lines stay exact instead of melting.</p>
<div class="grid">{cards3}</div>
<div class="note"><h3>In plain English</h3><p>This is the target. The plates are photographic, which is what makes them feel alive, but the "seen by a machine" point-cloud quality I asked for barely came through, so for now that comes from the HUD alone. The next step is paid: turning the three plates into three 5-second clips.</p></div>
<h2>v003 · Jayse's HUD, rendered in TouchDesigner</h2>
<p class="lede">The HUD layer TouchDesigner will run, tested outside it on a clean Blender plate: the machine finds the lone bright points on the leg tips, locks on with brackets that tighten as confidence rises, pulls elbowed callouts with live speed and confidence, keeps a telemetry sidebar with a cadence trace, and sweeps the moss. Built and rendered by TouchDesigner 2025 from <code>td/build_hud.py</code>, with no hand-editing: the script builds the network, records 240 frames and quits.</p>
{video3}
<div class="note"><h3>What to judge</h3><p>The HUD's grammar, not its polish: do the tightening brackets, callouts and sidebar feel like the Jayse direction? Known weak spots: it holds up to four or five tracks and re-acquires often, and the type is small. The bigger limit is the stand-in spider, which the generated plates are meant to replace.</p></div>
<h2>v002 · your 02 and 05, in motion</h2>
<p class="lede">The spider walks across moss past a locked-off camera with a slow push. Its legs carry a hairline pose skeleton with joint markers and IDs, only its gold body leaves a trail of fading copies (its path through time), and a frame holds the present. 10 seconds, no sound yet.</p>
{video2}
<h2>Round 2 stills · nature first</h2>
<p class="lede">The same brief rebuilt from your two picks, with the habitat taking a real share of the frame: bark, dew, leaf litter, fern. Free on Codex.</p>
<div class="grid">{cards2}</div>
<div class="note"><h3>In plain English</h3><p>Round 2 is where the stills start to look like your references: the machine is still there, but the forest is doing half the work. The motion test proves the tracking and the time trail work as moving image in Blender. What neither has yet is a real animal. The stand-in spider is the gap, and the free way to close it is your phone.</p></div>
<h2>Earlier · v001 orbit</h2>
<p class="lede">Blender 5.2, rendered headless from <code>probe_a_spider.py</code>. A stand-in spider (built from code, walking) sampled into glowing points, a ring of camera frames where a scanning rig would stand, the leg tips tracked with brackets and IDs, and moss underneath. 10 seconds, 1280&times;720, no sound yet.</p>
{video}
<div class="note"><h3>What this is and is not</h3><p>The motion, the camera frames, the tracking and the palette are the real pipeline. The spider itself is a placeholder: smooth shapes, not a scanned animal. Swap in your phone scan (or a real specimen scan) and the same scene renders it; that swap is the next step, and it is where the “living thing” quality will come from.</p></div>
<h2>Earlier · round 1 stills (you picked 02 and 05)</h2>
<p class="lede">Free, on the Codex subscription, from one brief with no reference images, so these are ours rather than copies. Each is a still from an imagined motion piece.</p>
<div class="grid">{cards}</div>
<div class="note"><h3>In plain English</h3><p>All six hold the rules: black, gold and white points, the machine visible, a real spider. What they do not yet have enough of is nature: only the time trail puts the spider in a living place. If nature is paramount, the next round should put these same machines around moss, bark, leaves and dew, not in empty black.</p></div>
</div><div id="lb"><img alt=""></div>
<script>const lb=document.getElementById('lb');document.addEventListener('click',e=>{{const b=e.target.closest('[data-full]');if(b){{lb.firstChild.src=b.querySelector('img').src;lb.classList.add('on');return}}if(e.target.closest('#lb'))lb.classList.remove('on')}});</script>
</body></html>'''
(HERE / 'review').mkdir(exist_ok=True)
(HERE / 'review/index.html').write_text(page)
print(f'review/index.html {len(page) / 1e6:.1f} MB')
