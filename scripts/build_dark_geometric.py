"""Build the dark-geometric research plan: inspiration/dark-geometric/index.html.

Data lives in inspiration/dark-geometric/research.json, images in img/.
Images are embedded as data URIs so the page opens from disk, from vbopen, or
anywhere else with no server and no broken relative paths. Edit the JSON (or
the copy below) and rerun: python3 scripts/build_dark_geometric.py
"""
from pathlib import Path
import base64, html, json

ROOT = Path(__file__).resolve().parents[1]
DIR = ROOT / 'inspiration/dark-geometric'
D = json.loads((DIR / 'research.json').read_text())
_cache = {}


def img(name):
    """Register an image in img/ and return its key ('' if absent). Each image is
    embedded once, in the IMG map at the foot of the page, however often it is used."""
    if not name or not (DIR / 'img' / name).exists():
        return ''
    if name not in _cache:
        _cache[name] = 'data:image/jpeg;base64,' + base64.b64encode((DIR / 'img' / name).read_bytes()).decode()
    return name


e = lambda s: html.escape(str(s or ''))
ANCHOR_SHORT = {'Y1': 'spider', 'Y2': '4D deer', 'Y3': 'vortex', 'Y4': 'agave'}
LAYERS = D['layers']
MARK = {2: '<i class="dot full" title="yes"></i>', 1: '<i class="dot half" title="partly"></i>', 0: '<i class="dot none" title="no"></i>'}


def chips(words):
    return ''.join(f'<span class="chip">{e(w)}</span>' for w in words or [])


def plate(name, alt, cls='plate'):
    src = img(name)
    if not src:
        return f'<div class="{cls} missing"><span>No capture yet · open the source</span></div>'
    return f'<button class="{cls}" data-full="{e(name)}" aria-label="Enlarge: {e(alt)}"><img data-k="{e(src)}" alt="{e(alt)}"></button>'


def card(it):
    src_link = f'<a href="{e(it["url"])}" target="_blank" rel="noopener">Source ↗</a>' if it.get('url') else ''
    ev = f'<details class="ev"><summary>How it was made · {e(it.get("evidence", "").rstrip(":"))}</summary><p>{e(it.get("technique", ""))}</p></details>' if it.get('technique') else ''
    tags = [f'<b>{a}</b> {ANCHOR_SHORT[a]}' for a in it.get('rhymes', [])] + [e(x) + ' (board)' for x in it.get('rhymes_board', [])]
    rh = f'<p class="rh">Rhymes with {" · ".join(tags)}</p>' if tags else ''
    year = f' · {e(it["year"])}' if it.get('year') else ''
    return f'''<article class="card">{plate(it.get("image"), it["title"])}<div class="cb">
<p class="id">{e(it["id"])}</p><h4>{e(it["title"])}</h4><p class="by">{e(it["creator"])}{year}</p>
<p>{e(it.get("visible", ""))}</p>{ev}{rh}<div class="chips">{chips(it.get("vocabulary"))}</div><p class="src">{src_link}</p></div></article>'''


# Anchors -------------------------------------------------------------------
spider = D['anchors'][0]
callouts = ''.join(
    f'<g><line x1="{c["x"]}" y1="{c["y"]}" x2="{c["lx"]}" y2="{c["ly"]}"/><circle cx="{c["lx"]}" cy="{c["ly"]}" r="2.1"/>'
    f'<text x="{c["lx"]}" y="{c["ly"] + 0.75}">{i + 1}</text><circle class="pt" cx="{c["x"]}" cy="{c["y"]}" r="0.55"/></g>'
    for i, c in enumerate(D['anatomy']))
legend = ''.join(f'<li><b>{i + 1}</b><div><h4>{e(c["name"])}</h4><p>{e(c["what"])}</p><div class="chips">{chips(c["words"])}</div></div></li>'
                 for i, c in enumerate(D['anatomy']))
anchors = ''.join(f'''<article class="anchor">{plate(a["image"], a["title"])}<div class="cb">
<p class="id">{e(a["id"])} · your reference</p><h4>{e(a["title"])}</h4><p class="by">{e(a["creator"])}</p><p>{e(a["visible"])}</p>
<p class="ev"><b>{e(a["evidence"])}</b> {e(a["technique"])}</p><p class="src"><a href="{e(a["url"])}" target="_blank" rel="noopener">Source ↗</a></p></div></article>'''
                  for a in D['anchors'][1:])
grids = ''.join(f'''<section class="grid6"><div class="g6h"><h4>{e(g["creator"])}</h4><p>{e(g["note"])}</p><a href="{e(g["url"])}" target="_blank" rel="noopener">Profile ↗</a></div>
<div class="g6">{"".join(plate(i, g["creator"], "plate sq") for i in g["images"])}</div></section>''' for g in D['grids'])

# Matrix ----------------------------------------------------------------------
head = ''.join(f'<th scope="col"><span>{e(l["short"])}</span></th>' for l in LAYERS)
rows = ''.join(f'<tr{" class=\"hl\"" if r.get("hl") else ""}><th scope="row">{e(r["name"])}<small>{e(r["who"])}</small></th>' + ''.join(f'<td>{MARK[v]}</td>' for v in r['marks']) + '</tr>'
               for r in D['matrix'])
totals = [sum(1 for r in D['matrix'] if r['marks'][i] == 2) for i in range(len(LAYERS))]
foot = '<tr class="tot"><th scope="row">Fully present in</th>' + ''.join(f'<td>{t}/{len(D["matrix"])}</td>' for t in totals) + '</tr>'
layer_key = ''.join(f'<li><b>{e(l["short"])}</b> {e(l["name"])}. <span>{e(l["question"])}</span></li>' for l in LAYERS)

# Lexicon -------------------------------------------------------------------
BY_ID = {a['id']: a for a in D['anchors']} | {it['id']: it for c in D['clusters'] for it in c['items']}
thumbs = lambda ids: '<div class="lt">' + ''.join(f'<figure>{plate(BY_ID[i]["image"], BY_ID[i]["title"], "plate lx")}<figcaption>{e(i)}</figcaption></figure>'
                                              for i in ids if i in BY_ID and BY_ID[i].get('image')) + '</div>'
lex = ''
for l in LAYERS:
    terms = [t for t in D['lexicon'] if t['layer'] == l['key']]
    if not terms:
        continue
    lex += f'<section class="lexg"><h3><span>{e(l["short"])}</span> {e(l["name"])}</h3><dl>' + ''.join(
        f'<div><dt>{e(t["term"])}</dt><dd>{e(t["meaning"])}</dd>{thumbs(t.get("examples", [])[:4])}</div>'
        for t in terms) + '</dl></section>'

# Clusters --------------------------------------------------------------------
clusters = ''.join(f'''<section class="cluster" id="{e(c["key"])}"><div class="clh"><p class="eyebrow">Field {i + 1} of {len(D["clusters"])} · {len(c["items"])} works</p>
<h3>{e(c["title"])}</h3><p>{e(c["summary"])}</p></div><div class="cards">{"".join(card(it) for it in c["items"])}</div></section>'''
                   for i, c in enumerate(D['clusters']))

tech = ''.join(f'''<tr><td>{plate(t.get("image"), t["title"], "plate thumb")}</td><td><b>{e(t["title"])}</b><small>Serves: {e(t["serves"])}</small></td>
<td><ol>{"".join(f"<li>{e(s)}</li>" for s in t["pipeline"])}</ol></td><td>{e(t["tools"])}</td><td>{e(t["cost"])}</td><td class="num">{e(t["time_to_first"])}</td>
<td class="num">{f'<a href="{e(t["url"])}" target="_blank" rel="noopener">Guide ↗</a>' if t.get("url") else ""}</td></tr>''' for t in D['techniques'])

tracks = ''.join(f'''<li class="track"><div class="tn">{e(t["when"])}</div><div><h4>{e(t["name"])}</h4><p>{e(t["question"])}</p>
<p class="do"><b>Do:</b> {e(t["do"])}</p><p class="out"><b>Visual output:</b> {e(t["output"])}</p>
{f'<div class="strip">{"".join(plate(i, t["name"], "plate mini") for i in t.get("images", []))}</div>' if t.get("images") else ""}</div></li>''' for t in D['plan']['tracks'])
probes = ''.join(f'''<article class="probe">{plate(p["image"], p["name"])}<div class="cb"><p class="id">Probe {e(p["id"])} · one evening</p><h4>{e(p["name"])}</h4>
<p>{e(p["tests"])}</p><ol>{"".join(f"<li>{e(s)}</li>" for s in p["steps"])}</ol><p class="out"><b>You will know:</b> {e(p["know"])}</p></div></article>''' for p in D['plan']['probes'])
plain = lambda k: f'<aside class="plain"><h3>In plain English</h3>{"".join(f"<p>{e(p)}</p>" for p in D["plain"][k])}</aside>'
reading = ''.join(f'<li><a href="{e(r["url"])}" target="_blank" rel="noopener">{e(r["title"])}</a> · {e(r["note"])}</li>' for r in D['reading'])
n_examples = sum(len(c['items']) for c in D['clusters']) + len(D['anchors'])

page = f'''<!doctype html><html lang="en-GB"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Dark geometric research</title><style>
:root{{--ink:#000;--mut:#555;--line:#e3e3e0;--soft:#f5f5f2;--bg:#fff;--acc:#d62d20}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif}}
.wrap{{max-width:1240px;margin:auto;padding:0 32px}}header.wrap{{padding-top:56px}}
.eyebrow,.id{{font:600 11px/1.4 system-ui;letter-spacing:.12em;text-transform:uppercase;color:var(--mut);margin:0}}
h1,h2,h3.serif{{font-family:Georgia,"Times New Roman",serif;font-weight:400;letter-spacing:-.01em}}
h1{{font-size:clamp(40px,6.4vw,82px);line-height:1.02;margin:18px 0 20px;max-width:15ch}}
h2{{font-size:clamp(30px,3.6vw,44px);line-height:1.1;margin:0 0 10px}}h3{{font-size:19px;font-weight:600;margin:0 0 6px}}h4{{font-size:15px;margin:4px 0 2px}}
p{{margin:6px 0}}.lede{{font-size:19px;max-width:62ch;color:#222}}a{{color:inherit;text-underline-offset:3px}}
.tldr{{border:1px solid var(--ink);border-radius:12px;padding:16px 20px;margin:26px 0;max-width:820px}}.tldr b{{font-size:12px;letter-spacing:.1em;text-transform:uppercase}}
nav.toc{{display:flex;flex-wrap:wrap;gap:8px;margin:18px 0 8px}}nav.toc a{{border:1px solid var(--line);border-radius:999px;padding:5px 12px;font-size:13px;text-decoration:none}}nav.toc a:hover{{border-color:var(--ink)}}
section.part{{border-top:1px solid var(--ink);margin-top:64px;padding-top:22px}}.sub{{color:var(--mut);max-width:70ch;margin-bottom:22px}}
.plate{{display:block;width:100%;padding:0;border:0;background:#000;cursor:zoom-in;aspect-ratio:4/3;overflow:hidden;border-radius:10px 10px 0 0}}
.plate img{{width:100%;height:100%;object-fit:cover;display:block;transition:transform .4s}}.plate:hover img{{transform:scale(1.03)}}
.plate.tall{{aspect-ratio:auto;border-radius:12px}}.plate.tall img{{height:auto}}.plate.sq{{aspect-ratio:1;border-radius:6px}}.plate.thumb{{width:120px;aspect-ratio:4/3;border-radius:6px}}.plate.mini{{width:110px;aspect-ratio:1;border-radius:6px}}
.plate.lx{{width:100%;aspect-ratio:4/3;border-radius:4px}}.lt{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:5px;margin-top:8px}}.lt figure{{margin:0}}.lt figcaption{{font-size:10.5px;color:var(--mut);letter-spacing:.06em;margin-top:2px}}details.ev{{margin-top:8px;font-size:13.5px}}details.ev summary{{cursor:pointer;font-size:11px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;color:var(--mut)}}.rh b{{font-weight:600;color:var(--ink)}}.missing{{display:flex;align-items:center;justify-content:center;color:#bbb;font-size:12px;background:#111;aspect-ratio:4/3;border-radius:10px 10px 0 0}}
.card,.anchor,.probe{{border:1px solid var(--line);border-radius:12px;background:#fff;overflow:hidden;display:flex;flex-direction:column}}
.cb{{padding:14px 16px 16px}}.by{{color:var(--mut);font-size:13px;margin:0 0 8px}}.card p,.anchor p,.probe p{{font-size:14px}}
.ev{{color:#333}}.ev b{{font-weight:600;font-size:11px;letter-spacing:.06em;text-transform:uppercase;color:var(--mut)}}.rh{{font-size:13px!important;color:var(--mut)}}
.src{{margin-top:auto;padding-top:6px;font-size:13px}}.chips{{display:flex;flex-wrap:wrap;gap:5px;margin-top:8px}}
.chip{{font-size:12px;border:1px solid var(--line);border-radius:999px;padding:2px 9px;background:var(--soft)}}
.cards{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:18px}}.anchors{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:18px;margin-top:18px}}
.hero{{display:grid;grid-template-columns:minmax(0,5fr) minmax(0,6fr);gap:34px;align-items:start}}
.anat{{position:relative;background:#000;border-radius:12px;overflow:hidden}}.anat img{{width:100%;display:block}}
.anat svg{{position:absolute;inset:0;width:100%;height:100%}}.anat line{{stroke:#fff;stroke-width:.18;vector-effect:non-scaling-stroke;stroke-width:1}}
.anat circle{{fill:#000;stroke:#fff;stroke-width:.25}}.anat circle.pt{{fill:#fff;stroke:none}}.anat text{{fill:#fff;font:700 2.2px system-ui;text-anchor:middle;dominant-baseline:middle}}
ol.legend{{list-style:none;padding:0;margin:0;display:grid;gap:14px}}ol.legend li{{display:grid;grid-template-columns:30px 1fr;gap:12px;border-top:1px solid var(--line);padding-top:12px}}
ol.legend li>b{{width:26px;height:26px;border:1.5px solid var(--ink);border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:13px}}
.grid6{{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,3fr);gap:20px;margin-top:26px;border-top:1px solid var(--line);padding-top:16px}}
.g6{{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:6px}}.g6h p{{font-size:14px;color:#333}}
.plain{{background:var(--soft);border:1px solid var(--line);border-radius:12px;padding:18px 22px;margin:28px 0 0;max-width:860px}}
.plain h3{{font-family:Georgia,serif;font-variant:small-caps;letter-spacing:.06em;font-weight:400;font-size:20px}}.plain p{{font-size:15px;color:#222}}
table.mx{{border-collapse:collapse;width:100%;font-size:14px}}.mx th,.mx td{{border-bottom:1px solid var(--line);padding:10px 8px;text-align:center}}
.mx th[scope=row]{{text-align:left;font-weight:600;white-space:nowrap}}.mx th small{{display:block;font-weight:400;color:var(--mut);font-size:12px}}
.mx thead th{{font-size:12px;font-weight:600;vertical-align:bottom;border-bottom:1px solid var(--ink)}}.mx tr.tot td,.mx tr.tot th{{border-bottom:0;font-variant-numeric:tabular-nums;font-size:13px;color:var(--mut)}}
.mx tr.hl th[scope=row]{{box-shadow:inset 3px 0 0 var(--ink);padding-left:12px}}
.dot{{display:inline-block;width:13px;height:13px;border-radius:50%;border:1.5px solid var(--ink)}}.dot.full{{background:var(--ink)}}.dot.half{{background:linear-gradient(90deg,var(--ink) 50%,transparent 50%)}}.dot.none{{border-color:#d4d4d0}}
ul.key{{list-style:none;padding:0;margin:14px 0 0;display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px 22px;font-size:13px}}ul.key span{{color:var(--mut)}}
.scroll{{overflow-x:auto}}.lexg{{margin-top:26px}}.lexg h3 span,.clh .eyebrow{{color:var(--mut)}}
.lexg dl{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:0 26px;margin:10px 0 0}}.lexg dl div{{border-top:1px solid var(--line);padding:10px 0}}
dt{{font-family:Georgia,serif;font-size:19px}}dd{{margin:2px 0 0;font-size:14px;color:#333}}dd em{{display:block;font-style:normal;color:var(--mut);font-size:12px;margin-top:3px}}
.cluster{{margin-top:44px}}.clh{{max-width:760px;margin-bottom:16px}}.clh h3{{font-family:Georgia,serif;font-weight:400;font-size:30px;margin:6px 0}}
table.tech{{border-collapse:collapse;width:100%;font-size:13.5px}}.tech td,.tech th{{border-bottom:1px solid var(--line);padding:12px 10px;vertical-align:top;text-align:left}}
.tech th{{font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:var(--mut);border-bottom:1px solid var(--ink)}}.tech small{{display:block;color:var(--mut)}}.tech ol{{margin:0;padding-left:18px}}.num{{white-space:nowrap}}
ol.tracks{{list-style:none;padding:0;margin:0}}.track{{display:grid;grid-template-columns:150px 1fr;gap:24px;border-top:1px solid var(--line);padding:18px 0}}
.tn{{font:600 12px system-ui;letter-spacing:.08em;text-transform:uppercase}}.track p{{max-width:78ch}}.do b,.out b{{font-weight:600}}.strip{{display:flex;gap:6px;margin-top:10px;flex-wrap:wrap}}
.decoded{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:18px}}.decoded figure{{margin:0}}.decoded .plate{{border-radius:10px}}.decoded figcaption{{font-size:13.5px;color:#333;margin-top:8px}}.probes{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:18px}}.probe ol{{padding-left:18px;font-size:14px;margin:8px 0}}
.twov{{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin-top:22px}}.twov>div{{border:1px solid var(--line);border-radius:12px;padding:18px 20px}}
.twov h3{{font-family:Georgia,serif;font-weight:400;font-size:24px}}
footer{{margin:70px auto 60px;border-top:1px solid var(--ink);padding-top:18px;font-size:13px;color:var(--mut)}}footer li{{margin:4px 0}}
#lb{{position:fixed;inset:0;background:rgba(0,0,0,.94);display:none;align-items:center;justify-content:center;z-index:9;cursor:zoom-out;padding:24px}}#lb img{{max-width:100%;max-height:100%;object-fit:contain}}#lb.on{{display:flex}}
:focus-visible{{outline:2px solid var(--acc);outline-offset:3px}}
@media(max-width:980px){{.cards,.anchors,.probes,.decoded{{grid-template-columns:repeat(2,minmax(0,1fr))}}.hero,.grid6{{grid-template-columns:1fr}}.lexg dl,ul.key{{grid-template-columns:1fr 1fr}}.track{{grid-template-columns:1fr;gap:6px}}}}
@media(max-width:640px){{.wrap{{padding:0 16px}}.cards,.anchors,.probes,.decoded,.twov,.lexg dl,ul.key{{grid-template-columns:1fr}}.g6{{grid-template-columns:repeat(3,minmax(0,1fr))}}.tech thead{{display:none}}.tech tr{{display:block;border-bottom:1px solid var(--line);padding:10px 0}}.tech td{{display:block;border:0;padding:4px 0}}}}
@media print{{#lb,nav.toc{{display:none}}.card,.anchor,.probe{{break-inside:avoid}}}}
</style></head><body>
<header class="wrap"><p class="eyebrow">Spatial art lab · research plan 002 · phase: Discover · {e(D["meta"]["date"])}</p>
<h1>{e(D["meta"]["headline"])}</h1><p class="lede">{e(D["meta"]["lede"])}</p>
<div class="tldr"><b>TL;DR</b>{"".join(f"<p>{e(p)}</p>" for p in D["meta"]["tldr"])}</div>
<nav class="toc"><a href="#sent">1 · What you sent</a><a href="#anatomy">2 · Anatomy</a><a href="#pattern">3 · The pattern</a><a href="#words">4 · The words</a><a href="#field">5 · The field ({n_examples} works)</a><a href="#how">6 · How it is made</a><a href="#plan">7 · The plan</a></nav></header>
<main class="wrap">
<section class="part" id="sent"><h2>What you sent</h2><p class="sub">{e(D["copy"]["sent"])}</p>
<div class="hero">{plate(spider["image"], spider["title"], "plate tall")}<div><p class="id">{e(spider["id"])} · your reference</p><h3 class="serif" style="font-size:30px;margin:6px 0">{e(spider["title"])}</h3><p class="by">{e(spider["creator"])}</p><p>{e(spider["visible"])}</p><p class="ev"><b>{e(spider["evidence"])}</b> {e(spider["technique"])}</p><p class="src"><a href="{e(spider["url"])}" target="_blank" rel="noopener">Source ↗</a></p></div></div>
<div class="anchors">{anchors}</div>{grids}</section>
<section class="part" id="anatomy"><h2>Anatomy of the spider</h2><p class="sub">{e(D["copy"]["anatomy"])}</p>
<div class="hero"><div class="anat"><img data-k="{img(spider["image"])}" alt="The spider, annotated"><svg viewBox="0 0 100 155.4" preserveAspectRatio="none" aria-hidden="true">{callouts}</svg></div><ol class="legend">{legend}</ol></div>
<h3 class="serif" style="font-size:26px;margin:34px 0 4px">Decoded: two pictures laid on top of each other</h3><p class="sub">{e(D["copy"]["decoded"])}</p>
<div class="decoded">{"".join(f'<figure>{plate(d["image"], d["cap"])}<figcaption>{e(d["cap"])}</figcaption></figure>' for d in D["decoded"])}</div>
{plain("anatomy")}</section>
<section class="part" id="pattern"><h2>The pattern across everything you have saved</h2><p class="sub">{e(D["copy"]["pattern"])}</p>
<div class="scroll"><table class="mx"><thead><tr><th></th>{head}</tr></thead><tbody>{rows}{foot}</tbody></table></div><ul class="key">{layer_key}</ul>
<p class="sub" style="margin-top:14px"><i class="dot full"></i> present &nbsp; <i class="dot half"></i> partly or unconfirmed &nbsp; <i class="dot none"></i> absent</p>{plain("pattern")}</section>
<section class="part" id="words"><h2>The words</h2><p class="sub">{e(D["copy"]["words"])}</p>{lex}</section>
<section class="part" id="field"><h2>The field</h2><p class="sub">{e(D["copy"]["field"])}</p>{clusters}{plain("field")}</section>
<section class="part" id="how"><h2>How it is made, cheapest path first</h2><p class="sub">{e(D["copy"]["how"])}</p>
<div class="scroll"><table class="tech"><thead><tr><th></th><th>Technique</th><th>Pipeline</th><th>Tools</th><th>Cost</th><th>First result</th><th></th></tr></thead><tbody>{tech}</tbody></table></div><p class="sub" style="margin-top:14px">{e(D["copy"]["parked"])}</p></section>
<section class="part" id="plan"><h2>The research plan</h2><p class="sub">{e(D["plan"]["intro"])}</p><ol class="tracks">{tracks}</ol>
<h3 class="serif" style="font-size:28px;margin:36px 0 12px">Three probes: make, don't read</h3><p class="sub">{e(D["plan"]["probes_intro"])}</p><div class="probes">{probes}</div>
<div class="twov"><div><p class="eyebrow">The 10x you can ship</p><h3>{e(D["plan"]["ten"]["title"])}</h3><p>{e(D["plan"]["ten"]["body"])}</p></div><div><p class="eyebrow">The 100x to steer by</p><h3>{e(D["plan"]["hundred"]["title"])}</h3><p>{e(D["plan"]["hundred"]["body"])}</p></div></div>
{plain("plan")}</section></main>
<footer class="wrap"><p><b>Reading.</b></p><ul>{reading}</ul><p>{e(D["copy"]["footer"])}</p></footer>
<div id="lb" role="dialog" aria-label="Enlarged image"><img alt=""></div>
<script>const IMG=__IMG__;document.querySelectorAll('img[data-k]').forEach(i=>{{i.src=IMG[i.dataset.k]}});
const lb=document.getElementById('lb'),li=lb.querySelector('img');document.addEventListener('click',ev=>{{const b=ev.target.closest('[data-full]');if(b){{li.src=b.querySelector('img').src;lb.classList.add('on');return}}if(ev.target.closest('#lb'))lb.classList.remove('on')}});document.addEventListener('keydown',ev=>{{if(ev.key==='Escape')lb.classList.remove('on')}});</script>
</body></html>'''
page = page.replace('__IMG__', json.dumps(_cache))
(DIR / 'index.html').write_text(page)
print(f'Built {DIR / "index.html"}: {len(page) / 1e6:.1f} MB, {n_examples} works, {len(D["lexicon"])} terms')
