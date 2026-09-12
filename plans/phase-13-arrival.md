# Phase 13 — arrival, the design

**Produced by Codex** (`gpt-5.6-sol`, read-only over the repo at `665efcd`,
12 Sep 2026) as a work package, then checked here.

**What I verified myself, and it holds:**

- `groundAt(-280, -150)` = 38.90 m against its claimed 38.89; `groundAt(-410, -380)`
  = 40.65 against its claimed 40.63. Both within 2 cm, so the standing
  positions are real ground, not plausible-looking numbers.
- The look target `[-190, 47.341, -200]` is `campus-courtyards` in `places.json`,
  exactly.

**What I did NOT verify:** the building footprints quoted from
`gv-2045-buildings.json`, the bearings, and the claim that The Homes contains
no named square or civic focus.

**Worth keeping whatever else changes:** it declines to give three of the five
shots an arrival, on the grounds that they have no "there" to get to, and says
so rather than inventing one. That matches the plan's own line — "not every
viewpoint has a there to get to" — and it is the answer that is easy to get
wrong in the direction of more work.

**Both frames are 2045-only.** Before frames stay parked.

---

## Choose two

- **Cyber Central → The Courtyards at Fiddlers Brook.** This is the essential arrival: the 15.8 ha wetland corridor only becomes intelligible beside its narrow watercourse, with the campus occupied behind it. This carries frame 5’s planted foreground, architecture and human life.
- **Panels and glasshouses → Working glasshouse edge.** At eye level the proposition becomes concrete: crops beneath spaced panels, waste-heat glasshouses and campus buildings in one working landscape.

Both are **2045-only**. TODAY arrivals remain parked.

Keep these aerial:

- **The Vale:** no “there”; it is a regional relationship—town, Doughnut and escarpment.
- **The Homes:** no “there”; the geometry contains 70 repeated house footprints but no named square, street or civic focus. Inventing one would be dishonest.
- **The Meadow Roof:** it has a subject, but no credible public ground-level destination. GCHQ’s secured, elevated roof is understood from above; ground access would either hide the meadow or fabricate access.

## Destination frames

### 1. The Courtyards at Fiddlers Brook

- **Camera:** `[-280.00, 40.49, -150.00]`; terrain `38.89 m AOD`, eye `+1.60 m`.
- **Look:** `[-190.00, 47.341, -200.00]`, the existing `campus-courtyards` target in `places.json`; bearing `061°`, elevation `+3.8°`, vertical FOV `48°`.
- **Time:** late August, `16:45`, warm low afternoon sun.
- **Place of interest:** **The Courtyards**, seen across the narrow Fiddlers Brook and its wet meadow. The nearest brook centreline is about 13 m from the camera.
- **Buildings:** the `13.6 m` campus block on footprint `[(-235.84,-168.28),(-221.61,-203.51),(-205.84,-197.14),(-220.08,-161.91)]`, plus the `11.9 m` block immediately behind on `[(-180.80,-136.34),(-216.03,-150.57),(-209.66,-166.33),(-174.43,-152.10)]`.
- **People:** campus workers crossing the planted court, two people sitting outside the glazed ground floor, walkers and one cyclist passing the wetland edge.
- **Composition:** reeds, wildflowers and people in the lower third; occupied architecture across the middle; sky no more than 25%.

**Forbid:** broad river, lake or flood basin; empty nature-reserve foreground; invented large bridge; generic curtain-wall office park; moved/taller blocks; token distant people; drone-height camera; more than half empty meadow or sky.

### 2. Working glasshouse edge

- **Camera:** `[-410.00, 42.23, -380.00]`; terrain `40.63 m AOD`, eye `+1.60 m`. This is a crop gap between the agrivoltaic rows.
- **Look:** `[-338.93, 43.11, -321.56]`, the centre and mid-façade of the glasshouse below; bearing `129°`, elevation `+0.5°`, vertical FOV `48°`.
- **Time:** the same late-August `16:45`.
- **Place of interest:** **Panels and glasshouses**, specifically the waste-heat growing house.
- **Buildings:** the `62 × 13 m`, `6.5 m` glasshouse on `[(-365.24,-339.20),(-307.75,-315.97),(-312.62,-303.92),(-370.11,-327.14)]`; behind it, the `15.3 m` campus block on `[(-218.23,-211.86),(-204.00,-247.09),(-188.24,-240.72),(-202.47,-205.49)]`.
- **People:** growers wheeling harvested produce from the glasshouse, one technician working beneath a raised panel row, and two campus staff walking through the service court.
- **Composition:** crops and thin panel rows in the foreground, glasshouse dominant in the middle, campus behind; sky no more than 20%.

**Forbid:** continuous black solar carpet; panels higher than roughly `2 m` or closer than the `11 m` row spacing; bare gravel solar farm; glasshouse becoming a warehouse, domestic polytunnel or giant conservatory; duplicated buildings; generic towers; empty fields or people reduced to specks.

## Back up

A persistent **“Back to Cyber Central”** or **“Back to Panels and glasshouses”** control should:

1. Plain-crossfade the held photograph onto the matching live 2045 endpoint at the identical camera.
2. Run the measured descent path backward, `B → A`, live and stylised—about `3.2 s`, as `returnToMap()` already does.
3. Complete the reverse approach to the exact originating viewpoint, restore its FOV and camera fence, and leave the switch at 2045.

Do not reverse-generate the photographic clip. Its final hand-back would occur in the dense aerial frame—the part already measured as hardest to match. The live reverse path is deterministic, survives a missing clip, and avoids both a visible aerial seam and a blur-zoom.
