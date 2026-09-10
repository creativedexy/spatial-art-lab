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
| 001 | [`001-path-leg.md`](001-path-leg.md) | the first generated leg | open |

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
