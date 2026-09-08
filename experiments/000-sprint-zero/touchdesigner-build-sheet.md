# Sprint 0 — TouchDesigner build sheet

For TouchDesigner **2025.33230**, macOS 26.5.1, Apple M5 Pro. Roughly 30–40 minutes.
This completes Sprint 0 and is the base network that Experiment 001 (Cosmic breath) grows from.

Before anything else: **open TD and note the licence tier** in the title bar or
`Dialogs → Licences`. Non-Commercial caps the output resolution at 1280x1280. That
number decides the export size for 001, so record it in the session log.

## Step 1 — new project, saved immediately

`File → Save As` → `experiments/000-sprint-zero/touchdesigner/sprint0-noise-v001.toe`

Save before you build. A `.toe` that has never been saved is the classic first-session loss.

## Step 2 — the three-operator network

In an empty network, press `Tab` to open the OP Create dialog each time.

| # | Operator | Name it | Why it exists |
|---|---|---|---|
| 1 | `TOP → Noise` | `noise1` | Generates the field. Everything else only shapes it. |
| 2 | `TOP → Level` | `level1` | Contrast and black point. This is what makes it feel like a volume rather than grey soup. |
| 3 | `TOP → Null` | `null1` | A fixed output handle. Always end a chain on a Null so you can rewire upstream without breaking anything downstream. |

Wire `noise1 → level1 → null1`. Click the lower-right viewer flag on `null1` so it
displays in the background.

## Step 3 — the parameters that matter

Select `noise1`, open the parameter panel (`p`):

- **Type** — start on `Sparse`. Try `Alligator` and `Hermite` later; they are different worlds.
- **Period** — the single most important control. Low = large soft clouds, high = fine grain. Sweep it slowly and watch.
- **Harmonics** — adds detail layers. 2–4 gives filaments; 0 gives smooth blobs.
- **Roughness** — how much each harmonic contributes. Above ~0.6 it starts to look like static.
- **Monochrome** — leave on. The whole brief is monochrome.
- **Resolution** — start at 1280x720. Do not raise it until the look is settled.

Select `level1`:

- **Black Level** — raise it to crush the mid-greys into black. This is the darkness the brief asks for.
- **Contrast** — pushes the surviving structure apart.
- **Gamma** — subtler than contrast; use it last for fine adjustment.

## Step 4 — movement, one variable

On `noise1`, in the **Transform** page, put this in **Translate → tx**:

```
absTime.seconds * 0.03
```

That drifts the field sideways slowly and forever. `absTime.seconds` is wall-clock seconds
since TD started; the multiplier is the speed. 0.03 is deliberately near-still — the piece
is called Cosmic *breath*, not cosmic wind. Try 0.3 once to feel how wrong fast looks.

For breathing rather than drifting, use the noise **Translate → tz** instead:

```
absTime.seconds * 0.02
```

3D noise moving through its third dimension evolves in place instead of sliding. This is
the better instinct for the brief and worth comparing directly against tx.

## Step 5 — three variants, saved and recorded

Save these as three separate `.toe` files (or three Noise TOPs side by side, viewer flags off):

1. **Sparse** — low Period, 0–1 Harmonics, high Black Level. Mostly darkness, few forms.
2. **Cloudy** — low Period, 2 Harmonics, low Roughness, moderate Black Level.
3. **Fine-grained** — high Period, 4 Harmonics, Roughness ~0.7.

Write the actual numbers into the session log. The numbers are the deliverable, not the images.

## Done when

The `.toe` reopens, the three variants exist with their parameters recorded, the movement
is slow and adjustable, and you can say out loud what Noise, Level and Null each do.

## If you get stuck

Ask with the version in the prompt, not just "in TouchDesigner":

> For TouchDesigner 2025.33230, [what happened] when I [what I did], with `noise1 → level1 → null1`.
> Explain the cause before the fix, and give me one change to try at a time.
