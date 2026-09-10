# 003 — The Curious Café, Bath Road: a drone swoop through

**Run 002 of `place-vision`,** and the first to go indoors: outside the skill's
stated scope ("not eye-level walkthroughs"), on purpose. What works here
extends the skill.

**Venue:** The Curious Café & Bistro, 204 Bath Road, Cheltenham GL53 7NE.
Family-run for 16+ years; brunch, homemade cakes, burgers, a sister deli at
the same address. In their words: "boutique decor", "a gorgeous garden",
"bustling but intimate", "cosy". Not a client: **an internal portfolio test.**

**Access: none, for now** (Dex, 10 Sep). The interior is **imagined** from
their own description, not taken from their photos, and must never be shown
as their real café. A phone scan replaces it later, dropped into the same web
code.

**Deliverable:** an interactive web swoop: through the front door, past the
cake counter and the tables, out to the garden.

## The pipeline for no access

1. **Hero stills** (Codex, free): the start and end of the swoop.
2. **World** (World Labs Marble): one image into an explorable 3D splat.
   The free plan generates but cannot export; **Standard at $20/month exports
   `.spz`/`.ply`**. Awaiting Dex's yes, and his account.
3. **Web** (three.js + World Labs' Spark renderer): a scroll- or click-driven
   camera path through the splat. The same code later takes a phone scan.

**Frozen people are a feature.** A world built from a still freezes everyone
in it, so the swoop becomes a frozen-moment one-take through a busy café. That
satisfies the no-empty-frames rule, which an empty-room scan never would.

## Frames, the rule answered

| frame | place of interest | buildings | people |
|---|---|---|---|
| A: just inside the door, looking through | the cake counter and the open garden doors at the back | the café interior: a Victorian Bath Road shopfront room, boutique décor | a busy brunch service: tables full, staff at the counter |
| B: the garden, looking back in | the garden with the café's back doors open | the rear of the building, the room glimpsed inside | people at garden tables, someone carrying plates out |
