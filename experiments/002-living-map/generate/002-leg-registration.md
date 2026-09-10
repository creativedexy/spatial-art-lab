# 002 — the same two frames, with surveyed locks instead of estimated ones

**For:** the local session on the Mac, on the free Codex subscription.
**Cost:** £0. No paid call, no video. Rungs B and C of 001 stay parked.
**Inputs:** the same plates, plus
[`cheltenham-circular-footpath/anchors.json`](cheltenham-circular-footpath/anchors.json),
which is new.

## Why there is a 002 at all

001 rung A passed on photorealism and came back partial on registration, and
your own reading named the next free move exactly:

> **Hold the horizon and the path as hard lines.** Both drifts are in the two
> features that carry the registration. A second pass that states them as pixel
> rows and columns taken from the plate […] is the next free thing to try.

Agreed, with one correction that matters: **some of the pixel rows and columns
you took from the plate were themselves estimates, and one of them was wrong by
more than the drift you were chasing.**

`scripts/measure_leg_anchors.py` now projects the surveyed features through the
leg's own camera, so these are not read off an image — they come from the LiDAR
and the OpenStreetMap geometry the plate was rendered from.

## Where your estimates landed

| what | your prompt said | survey says | out by |
|---|---|---|---|
| A horizon | y = 330 | y = **333** | 3 px — fine |
| B horizon | y = 272 | y = **269** | 3 px — fine |
| B stream, right edge | y = 401 | y = **399** | 2 px — fine |
| GCHQ box | x 920–1180, y 306–333 | x **922–1183**, y **305–327** | ~1 px — fine |
| **B path, near the horizon** | **x = 641 at y = 290** | **x = 684 at y = 289** | **43 px** |

Four of five were as good as measurement. The fifth is the one that carries the
registration: you locked B's path as dead straight up the middle to a vanishing
point at 50 % width, and it is not straight — over the last 160 m of the leg it
bends **right**, to x ≈ 684. Your correction pass then aimed at x = 641 and
landed at x ≈ 626, so the true error against the survey is about 58 px, not the
15 px you reported. The drift you measured was real; the target was also moving.

That single feature is worth more than all the others put together, because a
video bridge pins its ends on exactly this line.

## The locks

Both frames, at the plate's 1280 × 720. Everything not listed is materials and
light and is yours.

#### `a-start.png`

| feature | surveyed position | note |
|---|---|---|
| horizon | y = **333** | sky above, ground below — nothing invented into the sky |
| footpath centreline | (713,605) → (616,457) → (531,386) → (489,356) | at 40, 80, 160 and 320 m ahead; a trodden earth line about a metre wide |
| stream | (500,340) → (1249,477) | nearest point 77 m; narrow, do not widen |
| near hedge | (45,341) → (140,369) | left edge only, low and thin |
| **GCHQ** | x **922–1183**, y **305–327** | 701 m out, edge-on |
| Royal Court | x 576–625, y 324–330 | 1038 m out |
| the shed | centre x 297, base y 545, roof y 482 | 49 m — keep the footprint and the yard behind it |
| settlement edge | rooflines top out at y = **319**, bases y = **330**, from x 78 rightwards | nearest house 331 m — do not bring it forward, do not raise it |

#### `b-end.png`

| feature | surveyed position | note |
|---|---|---|
| horizon | y = **269** | this is the 18 px you were chasing |
| footpath centreline | (640,531) → (640,388) → (640,317) → **(684,289)** | straight for the first 160 m, then bending **right**, not left |
| stream | (707,302) → (1263,399) | nearest point 79 m; the loop is at the near end |
| far hedge | (799,270) → (690,276) | 532 m out, thin, on the horizon |
| Royal Court | x 805–882, y 262–270 | 704 m out |
| Shaftesbury Place | x 767–814, y 262–269 | 749 m out |
| settlement edge | rooflines top out at y = **256**, bases y = **270**, from x 151 rightwards | nearest house 227 m |

## Two other things from your reading

**GCHQ became a long pale shed, and your box for it was right to the pixel.**
So this is not a registration failure, it is a description failure: at 700 m and
22 px tall the plate cannot tell a generator what that band *is*. It is the
Doughnut — a circular office building, pale white-grey ribbed metal annular
roof, 14.8 m tall on a 52.7 m base, seen edge-on so the ring reads as a long low
band with a slight rise at each end. Photographic ground truth for the roof is
in `inspiration/golden-valley/` — **private reference, do not attach it to a
generation**; it is there so the description can be written accurately, not so
the image can be copied.

**"Let the map own frame zero" — accepted.** That is the right shape and it
halves the problem: when video unparks, the clip starts on the map's own render
and only the far end needs registering. It does not change this request, which
is about making both ends good enough to be worth pinning.

## What to write back

Append a `## Result` here: how many passes, and the residual drift measured
against the numbers above rather than against your own estimates. If a feature
still will not hold after one correction, say which — a lock that a generator
cannot honour is a finding about the tool, and worth as much as a frame.

Nothing here costs anything. If it comes back tight, request 003 is the video
bridge and that is Dex's call, not ours.
