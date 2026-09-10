# generate/ — the queue between this branch and a machine with keys

The cloud session builds the map and renders the plates. It has no API keys
and should never have any. The local session on the Mac has the keys and the
subscriptions. This folder is how one asks the other for something.

**If you are the local session:** read the highest-numbered request below that
has no `## Result` section, do it, write the outputs into the folder the
request names, then append a `## Result` section saying what you ran, what it
cost and what came back. Commit on the same branch. That is the whole
protocol.

## Requests

| # | request | for | status |
|---|---|---|---|
| 001 | [`001-path-leg.md`](001-path-leg.md) | the first generated leg | **closed**: an empty footpath fails the interesting-imagery rule; do not run B or C |

## The interesting-imagery rule (Dex, 10 Sep 2026)

**No empty frames.** An empty field, an empty path, a plot with nothing on it,
or a sky with a strip of town along the bottom is not worth generating, however
photoreal it comes out. Every frame has to earn its place with three things,
and a brief has to name all three before anything is generated:

| must show | what counts | what does not |
|---|---|---|
| **A place of interest** | a named, recognisable subject as the focal point: GCHQ, the Golden Valley innovation centre and its meadow roof, a named plaza, a Cheltenham landmark | "the site", "the town", a horizon |
| **Buildings** | built form legible as architecture, filling a real share of the frame | a thin band of rooftops on the horizon |
| **People** | people doing something — walking, sitting, cycling, gathered — wherever the camera is low enough to see them; from the air, visible life instead (full car parks, busy plazas, traffic) | nobody, anywhere |

**The check, on the brief and again on the result:** name the place, the
buildings and the people in each frame. If any of the three cannot be named,
do not generate it. And no more than half of any finished frame may be empty
ground or empty sky; if it is, it fails and is regenerated or dropped.

**Transitions are a blurry zoom-in, not a journey.** Get from one interesting
frame to the next with a push-in and motion blur, done in the page or in ffmpeg
for nothing. There is no need to travel an empty path between them, and no
need to generate video for a transition at all. This also retires most of the
registration problem: a blurred push-in does not need its last frame to match
the next one to the pixel.

## Rules that do not change

- **Never commit, echo or paste an API key.** A dry run reports only whether
  one is *set*.
- **`inspiration/` is private reference.** Third-party copyright. Do not
  republish it, do not ship it in a deliverable, and do not feed it to a
  generator as a style reference without asking first.
- **Plates are rendered with the interface hidden.** The amber path ribbon is
  how a viewer *chooses* a route; a generator conditioned on it will paint a
  glowing strip down the middle of the finished footage.
- **Cheap first.** Every request names the cheapest rung that could answer it.
  If the cheap rung answers it, stop.

## Reference — what the map looks like today

`reference/` holds stills straight from the live map, so a prompt can be
written against what the thing actually looks like rather than against
somebody's memory of it. They are renders of our own scene: no third-party
imagery, safe to send anywhere.

| file | what it shows |
|---|---|
| `aerial-hub.png` | the hub view, network lit — the Cycle Spine crossing the vale past GCHQ, the Circular running north into the fields |
| `aerial-high.png` | the same from higher, where the pixel floor is doing all the work |
| `golden-valley-site.png` | the Circular crossing the Golden Valley fields, 160 m from the phase 1 site |
| `travelling-the-circular.png` | mid-leg, riding the route at 14 m with the path lit ahead and faded out underneath |
