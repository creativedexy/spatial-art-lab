// Two labels in the same place are worse than one label.
//
// Phase 8. Every marker in this map was tested on its own — big enough to hit,
// planted on the right ground, fading with distance — and at 390 px they came
// out as five overlapping plates in a single band across the middle of the
// screen, with the doughnut's name buried under three others. Each one was
// correct; the set was unreadable. Fading with distance does not help, because
// two half-faded labels on top of each other are still two labels on top of
// each other.
//
// So: nearest wins. Walk the markers from the camera outwards and keep one
// only if its plate does not touch a plate already kept. The one you are
// closest to is the one you are most likely to be looking at, and the far ones
// come back as soon as you move — which reads as parallax rather than as
// things switching off, because that is very nearly what it is.
//
// It runs across places AND descent hotspots together on purpose. They are two
// systems to us and one thing to a viewer, and they stand on the same ground:
// GCHQ has both, and before this the two labels simply drew through each other.

const PAD = 6;    // a little air, so "not overlapping" also looks like it

/**
 * @param {{el: HTMLElement, anchor: THREE.Vector3, keep?: boolean}[]} markers
 *   Already positioned for this frame; anything already hidden is skipped.
 * @param {THREE.Camera} camera
 */
export function thin(markers, camera) {
  const live = [];
  for (const m of markers) {
    if (m.el.hidden) continue;
    live.push({ m, d: camera.position.distanceToSquared(m.anchor) });
  }
  live.sort((a, b) => a.d - b.d);

  const kept = [];
  for (const { m } of live) {
    // The plate is the label, not the button: the stem below it is a drawn
    // line to the ground and two stems crossing is fine — it is two names
    // sitting on top of each other that cannot be read.
    const plate = m.el.querySelector('.label') ?? m.el;
    const r = plate.getBoundingClientRect();
    const box = { l: r.left - PAD, r: r.right + PAD, t: r.top - PAD, b: r.bottom + PAD };
    const clash = kept.some((k) => !(box.r < k.l || box.l > k.r
                                     || box.b < k.t || box.t > k.b));
    if (clash && !m.keep) m.el.hidden = true;
    else kept.push(box);
  }
  return kept.length;
}
