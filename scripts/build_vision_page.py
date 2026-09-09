import json
u = json.load(open('/tmp/vuris.json'))

CSS = """
:root{--ink:#000;--soft:#f7f7f5;--line:#e3e3de;--mute:#6b6b66;--good:#1a7f4b;--bad:#b3341f;--warn:#a8760a}
*{box-sizing:border-box}
body{margin:0;background:#fff;color:var(--ink);font:14px/1.55 system-ui,'Segoe UI',Helvetica,Arial,sans-serif}
.wrap{max-width:1240px;margin:0 auto;padding:56px 28px 96px}
h1{font:400 48px/1.06 Georgia,'Times New Roman',serif;margin:0 0 12px;letter-spacing:-.012em}
h2{font:400 28px/1.2 Georgia,'Times New Roman',serif;margin:64px 0 6px}
h3{font:400 20px/1.25 Georgia,serif;margin:34px 0 4px}
.lede{color:var(--mute);max-width:66ch;margin:0 0 6px;font-size:15px}
.unit{color:var(--mute);font-size:11px;text-transform:uppercase;letter-spacing:.1em;margin:0 0 22px}
.hero{border:1px solid var(--line);border-radius:12px;overflow:hidden;margin:0}
.hero img{display:block;width:100%;height:auto}
.cap{padding:14px 18px 17px;border-top:1px solid var(--line)}
.cap b{display:block;margin:8px 0 4px;font-size:15px}
.cap .t{color:var(--mute);font-size:13.5px;max-width:88ch;display:block}
.grid{display:grid;gap:20px;grid-template-columns:repeat(2,1fr)}
.g3{grid-template-columns:repeat(3,1fr)}
.card{margin:0;border:1px solid var(--line);border-radius:12px;overflow:hidden;background:#fff;box-shadow:0 1px 2px rgba(0,0,0,.03)}
.card img{display:block;width:100%;height:auto}
.tag{display:inline-block;font-size:10px;font-weight:700;letter-spacing:.09em;text-transform:uppercase;padding:3px 7px;border-radius:4px;color:#fff}
.ok{background:var(--good)}.no{background:var(--bad)}.mid{background:var(--warn)}.neu{background:#57574f}
.step{display:inline-block;font:400 12px/1 Georgia,serif;letter-spacing:.16em;text-transform:uppercase;color:var(--mute);margin:0 0 8px}
table{border-collapse:collapse;width:100%;margin:8px 0 0;font-size:13.5px}
th,td{text-align:left;padding:10px 12px;border-bottom:1px solid var(--line);vertical-align:top}
th{font-size:11px;text-transform:uppercase;letter-spacing:.08em;color:var(--mute);font-weight:600}
td.n{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
.plain{border:1px solid var(--line);border-radius:10px;background:var(--soft);padding:20px 24px;margin:24px 0 0}
.plain h4{font:400 13px/1 Georgia,serif;text-transform:uppercase;letter-spacing:.12em;margin:0 0 12px;color:var(--mute)}
.plain p{margin:0 0 11px;max-width:72ch}.plain p:last-child{margin:0}
.seq{border-left:3px solid var(--line);padding-left:22px;margin:34px 0 0}
@media(max-width:900px){.grid,.g3{grid-template-columns:1fr}h1{font-size:34px}}
"""


def hero(src, step, title, body):
    return (f'<figure class="hero"><img src="{src}" alt="{title}">'
            f'<div class="cap"><span class="step">{step}</span>'
            f'<b>{title}</b><span class="t">{body}</span></div></figure>')


def card(src, tag, cls, title, body):
    return (f'<figure class="card"><img src="{src}" alt="{title}">'
            f'<div class="cap"><span class="tag {cls}">{tag}</span>'
            f'<b>{title}</b><span class="t">{body}</span></div></figure>')


audit = [
    ("Terrain, ridge, horizon", "ok", "Ours is right",
     "Hill crest, the fall to the Severn Vale, the field boundaries west."),
    ("Street layout and road network", "ok", "Ours is right",
     "Radial estates, the A40, the perimeter road all match the photograph."),
    ("GCHQ position and ring form", "ok", "Ours is right",
     "Right place, right shape, right diameter."),
    ("GCHQ roof <b>colour</b>", "ok", "Was wrong. Now fixed.",
     "Ours was dark teal against a real pale ribbed metal, and the extrusion&rsquo;s top cap "
     "carried the facade colour. That one value made rung 1 read the building as a pond. "
     "Split into wall and roof, roof set pale."),
    ("Field surface variety", "ok", "Was absent. Now fixed.",
     "Session L gave every field its working lines, taken from the field&rsquo;s own long axis. "
     "They come through visibly in the generated frames."),
    ("Roof material variety", "mid", "Partly there",
     "Session L&rsquo;s five material families split slate from tile from profiled metal. Still one "
     "colour per family rather than per building."),
    ("Car parks", "no", "Still absent",
     "The real site has enormous concentric car parks full of cars beside the ring. Large "
     "visual area, no class for it in the mask. The generator invents them from the reference."),
    ("Garden and plot subdivision", "no", "Still absent",
     "Hedges, lawns, sheds, parked cars between plots. Reads as grain at this altitude."),
]
arows = "".join(
    f'<tr><td><b>{n}</b></td><td><span class="tag {c}">{"ok" if c=="ok" else ("missing" if c=="no" else "partial")}</span></td>'
    f'<td>{v}</td><td>{d}</td></tr>' for n, c, v, d in audit)

html = f"""<!doctype html><html lang="en-GB"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Golden Valley &mdash; the descent</title><style>{CSS}</style></head><body>
<div class="wrap">

<h1>Somewhere between the inspiration and a film.</h1>
<p class="lede">Five frames of a descent: from the measured map of west Cheltenham, down
past GCHQ, onto the Golden Valley site as it stands today, then the same view with the
scheme built, and finally standing in it. Every frame generated on the Codex subscription
with a self-inspection pass.</p>
<p class="unit">Five frames at &pound;0, regenerated against the corrected renderer &middot;
plus US$0.14 of paid A/B to check two single-value fixes</p>

<div class="seq">

<h2>One &mdash; the map, made real</h2>
<p class="unit">Conditioned on our surveyed aerial &middot; materials from a real photograph of the same place</p>
{hero(u['f1'], 'frame one', 'The hill, the town, the doughnut',
      'GCHQ reads as a building with pale metal roofs and concentric car parks, not as water. '
      'The terrain, street pattern, woods and the Severn Vale horizon are ours; the brick, slate, '
      'tile and light are the generator&rsquo;s.')}

<h2>Two &mdash; the descent</h2>
<p class="unit">Conditioned on our low approach camera</p>
{hero(u['f2'], 'frame two', 'Past GCHQ',
      'Pale ribbed roof, glazed inner ring, planted courtyard, brick base, car parks full of cars, '
      'mature limes and oaks. This is the same building that rung 1 turned into a pond, corrected '
      'by naming its real material rather than by adding a single polygon.')}

<h2>Three and four &mdash; the pitch</h2>
<p class="lede">The same surveyed camera, twice. Nothing moves between them but the scheme.
The woodland block, the stream, the ploughed field, the hedgerow and the sewage works with
its tanks and solar arrays are all held fixed, because they are all in our model already.</p>
<p class="unit">Golden Valley site &middot; today, and built</p>
<div class="grid">
{card(u['f3'], 'today', 'neu', 'The site as it stands',
      'Open pasture, the wood, the stream, the hedgerow, the works on the ridge.')}
{card(u['f4'], 'built', 'ok', 'The site with the scheme',
      'Meadow roof, PV on the flats, buff stone and timber banding, sett plazas through '
      'wildflower, retained oaks, people. Every landscape anchor unmoved.')}
</div>

<h2>Five &mdash; arrival</h2>
<p class="unit">A new camera &middot; eye level, in the plaza</p>
{hero(u['f5'], 'frame five', 'Standing in it',
      'The end of the descent. The one frame with no surveyed geometry under it, because we do '
      'not have the scheme modelled &mdash; this is the inspiration end of the spectrum, and it is '
      'the frame that says what the whole thing is for.')}
</div>

<h2>What the ground truth actually told us</h2>
<p class="lede">The developer&rsquo;s own aerial is a photomontage over a real photograph of this exact
hill. Comparing our model against it, feature by feature, says where detail is worth adding
&mdash; and it is not geometry.</p>
<p class="unit">Our measured map versus a real aerial photograph of the same place</p>
<table><thead><tr><th>Feature</th><th>Status</th><th>Verdict</th><th>Note</th></tr></thead>
<tbody>{arows}</tbody></table>

<h3>What one colour value bought</h3>
<p class="unit">Rung 1, US$0.06 each &middot; identical prompt, identical model, identical geometry &mdash; GCHQ&rsquo;s roof changed from dark teal to pale metal in our renderer</p>
<div class="grid">
{card(u['r1before'], 'before &middot; dark teal roof', 'no', 'The pond',
      'A flat dark ellipse in green. The model read the most recognisable building in '
      'Gloucestershire as water.')}
{card(u['r1after'], 'after &middot; pale metal roof', 'mid', 'No pond &mdash; but no ring either',
      'The water misread is gone, which was the hypothesis. Rung 1 still cannot hold the ring: '
      'it substituted a shed and a playing field. Beauty-conditioning was always the weak path.')}
</div>

<h3>And what the corrected depth pass bought</h3>
<p class="unit">Rung 2, US$0.08 each &middot; before: linear depth, 1.07 grey levels of relief. After: Session L&rsquo;s disparity encoding, 10.30 levels</p>
<div class="grid">
{card(u['r2before'], 'before &middot; 1.07 levels', 'no', 'The wrong town',
      'GCHQ absent, street network invented. The control net was handed a bare ground ramp.')}
{card(u['r2after'], 'after &middot; 10.30 levels', 'ok', 'Our streets, our fields',
      'The estate curves, the field working lines and the A40 all match the survey now. '
      'Remaining defect: the model fogged the upper half and lost the ring in it &mdash; that is the '
      'prompt&rsquo;s &ldquo;atmospheric haze&rdquo;, and it is free to fix.')}
</div>

<div class="plain"><h4>In plain English</h4>
<p>The audit and the frames say the same thing from two directions. Our model has the
structure right &mdash; terrain, streets, GCHQ&rsquo;s position and shape, the woods, the stream.
What it lacks is <i>class and colour</i>: which roofs are slate and which are clay tile,
that GCHQ&rsquo;s roof is pale, that there are car parks there, that fields are ploughed as well
as grazed. None of that is modelling. All of it is data we either already hold in the OSM
tags or can state in one line to a generator.</p>
<p>The dark teal roof is the cleanest example available. One wrong colour value in our
renderer cost a paid generation and produced a lake where the most recognisable building in
Gloucestershire should be. Naming the real material fixed it for nothing. That is the whole
argument about where detail belongs, in a single object.</p>
<p>The recommendation flips only if a frame fails in a way that more <i>geometry</i> would
fix. Across six paid rungs and five free frames, none has.</p></div>

<h2>What this cost, against what the paid route cost</h2>
<table><thead><tr><th>Route</th><th class="n">Cost</th><th class="n">Frames</th><th>Result</th></tr></thead>
<tbody>
<tr><td>Paid ladder, video rungs 3 and 4</td><td class="n">US$0.95</td><td class="n">2 clips</td>
<td>Our clay render, moving. Kling image-to-video preserves the style of the frame it is given.</td></tr>
<tr><td>Paid ladder, image rungs</td><td class="n">US$0.30</td><td class="n">4</td>
<td>Settled the Blender question and found the depth-encoding bug. Kept value.</td></tr>
<tr><td><b>Codex subscription, with a verify pass</b></td><td class="n"><b>&pound;0</b></td><td class="n"><b>5</b></td>
<td><b>The sequence above.</b> Takes multiple references at once, inspects its own output,
names the drift and corrects it.</td></tr>
</tbody></table>
<p class="lede" style="margin-top:16px">Honest caveat: the free frames are not survey-exact.
Codex reported the drift itself each time &mdash; GCHQ sits slightly high in frames one and two,
foreground footprints differ. For a vision sequence that is acceptable. For a film where the
map has to hand over to the clip on a matched frame, it is not, and that is the next problem.</p>

<p class="unit" style="margin-top:36px">Experiment 002 &middot; spatial-art-lab &middot;
branch claude/maps-generative-video-ia8733</p>
</div></body></html>"""

out = '/Users/user/Projects/3D Design/experiments/002-living-map/vision/index.html'
open(out, 'w').write(html)
print('wrote', out, len(html) // 1024, 'KB')
