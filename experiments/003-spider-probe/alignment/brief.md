# Alignment stills: spiders seen by a machine

**For:** Codex, free subscription, built-in image_gen. £0. No reference images attached on purpose: these must be original, not copies of the artists on the board.

Make six stills with the built-in image generation tool. Save each as PNG into `experiments/003-spider-probe/alignment/out/` with the filenames below, resampled to 1600 × 900 (16:9) with `sips` if the native size differs. Then write `out/notes.md` (one line per frame: filename, what came out, anything that failed the rules) and `out/prompts.json` (the exact prompts used).

## Rules for every frame
- Pure black background (#000). Near-monochrome: white and warm gold points, with at most one small accent colour.
- The subject is a real spider, anatomically right (eight legs, two body parts), shown as measurement data: a dense cloud of tiny glowing points, not a solid CGI surface.
- The machine must be visible: thin hairline geometry (camera frames, tracking boxes, rings, measurement ticks) and a few isolated bright white dots.
- It must read as a still taken from motion: slight trails, streaks or a timecode.
- Any text is tiny, sparse, monospace, letter-spaced, at the edges. Keep words short and real: "ARANEAE", "ID 07", "00:01:12:04", "TRACK 3". No paragraphs, no gibberish blocks.
- No neon cyberpunk palette, no sci-fi HUD clutter, no glow haze filling the frame. At least 40% of the frame is true black.

## The six frames
1. `01-specimen-cameras.png`: a jumping spider as a warm gold and white point cloud, three-quarter view, surrounded by a ring of 20 thin white upright rectangles (photogrammetry camera frames seen at different angles) and a handful of loose white feature points.
2. `02-tracking-live.png`: an orb-weaver on its web at night, macro. Thin white bounding boxes with small ID labels track each leg joint; faint lines connect the joints like a pose skeleton; the spider itself is dissolving into points at the edges.
3. `03-specimen-archive.png`: a spider as a plexus network (points joined to nearby points by hairlines), centred, with a small magnified inset in corner brackets top right and a column of short classification labels bottom left, like a museum specimen card.
4. `04-web-geometry.png`: an orb web drawn as luminous construction geometry: radial threads, concentric rings, measurement ticks. The spider at the centre is a dense cluster of gold points; tiny particles drift along the threads.
5. `05-time-trail.png`: a spider walking across moss, rendered as a trail of successive semi-transparent point-cloud copies of itself (its path through time), with one thin frame marking the present moment and small timestamps along the path. The moss is a sparse green-white point cloud.
6. `06-ascii-specimen.png`: a spider rendered entirely in a grid of tiny monospace characters (ASCII art), white and gold on black, with thin tracking brackets around it and a scan line passing through.
