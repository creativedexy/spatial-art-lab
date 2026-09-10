// Phase 7. Where the time goes on the way to a visible map.
//
// Until now the page's own answer to "is it loaded yet" was one boolean set
// at the very end, which is the same shape as the problem: `buildWorld` awaits
// the terrain, the land cover, the footprints, the 2045 scheme and two GLBs
// before a single pixel is drawn, so a phone shows the background colour for
// the whole download and there is no way to say which part of it hurt.
//
// A mark is a name and a millisecond. Nothing here decides anything or holds
// a reference to a scene; it exists so the deferral work in this phase can be
// argued from numbers rather than from how it feels on a laptop with the
// files already in cache.
const marks = [];
const t0 = performance.now();

export function mark(name) {
  marks.push({ name, at: performance.now() - t0 });
}

export function timeline() {
  let prev = 0;
  return marks.map(({ name, at }) => {
    const row = { name, at: +at.toFixed(1), took: +(at - prev).toFixed(1) };
    prev = at;
    return row;
  });
}

mark('boot');
// Read by scripts/measure_payload.py, and by nothing in the page.
if (typeof window !== 'undefined') window.__stage = { timeline, mark };
