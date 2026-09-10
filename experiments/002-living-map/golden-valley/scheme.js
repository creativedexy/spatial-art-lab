// What the scheme actually is, on screen, while it arrives.
//
// Phase 8. The map could already show 2045. What it could not do was say what
// 2045 is — and the figures a client is being asked to buy were sitting in a
// JSON file nobody reading the map can see: 77.4 hectares over 29 fields, a
// third of it built and no more, 6,234 new trees.
//
// A fixed legend would have been the easy version and the wrong one. The wave
// is the piece; a number that sits still while the thing it describes sweeps
// across the vale is furniture. So the band fills as the front crosses, and it
// fills with MEASURED area rather than the totals tweened by the dial
// position: `scripts/golden_valley_progress.py` compares the two class maps
// square metre by square metre and bins the differences by easting, so what
// the band shows at any dial position is what is actually behind the front.
// The fields are not spread evenly — the wetland follows the brook and is
// westernmost, the built ground is central, the orchards ring it — and a
// linear tween would have been close to right and impossible to defend.
//
// Two figures, deliberately not merged, because they measure different things
// and quietly averaging them would be the sort of number that falls apart in
// a room:
//
//   68.6 ha  the ground that CHANGES — what you can see happen
//   77.4 ha  the allocation, over 29 fields — what the scheme covers
//
// The difference is field area that keeps the class it already had: a field
// allocated arable that was already farmland is in the scheme and does not
// change colour.

const url = (f) => new URL(f, import.meta.url).href;

/** The order the band stacks in: the case for the scheme, left to right. */
const ORDER = ['orchard', 'wetland', 'agrivoltaic', 'scrub', 'grass', 'road_minor'];

/** What each changed class is called in English, and what it is. */
const SAYS = {
  orchard: ['Orchard', 'new planting ringing everything built'],
  wetland: ['Wet meadow', 'the brook corridor let out of its culvert'],
  agrivoltaic: ['Agrivoltaics', 'panels over a crop that is still farmed'],
  scrub: ['Scrub', 'rough edges left to do their own thing'],
  grass: ['Built ground', 'what the new buildings stand on'],
  road_minor: ['New streets', 'between the blocks'],
};

const ha = (n) => (n >= 10 ? n.toFixed(0) : n.toFixed(1));

/**
 * @param {{ future, root: HTMLElement }} ctx
 */
export async function addScheme({ future, root }) {
  const [meta, progress] = await Promise.all([
    fetch(url('gv-2045-meta.json')).then((r) => r.json()),
    fetch(url('gv-2045-progress.json')).then((r) => r.json()),
  ]);

  const classes = ORDER.filter((k) => progress.classes[k]);
  const totals = Object.fromEntries(
    classes.map((k) => [k, progress.classes[k][progress.bins - 1]]));
  const grand = classes.reduce((s, k) => s + totals[k], 0);

  const band = document.createElement('button');
  band.id = 'scheme';
  band.type = 'button';
  band.setAttribute('aria-expanded', 'false');
  band.setAttribute('aria-controls', 'scheme-sheet');

  const bar = document.createElement('span');
  bar.className = 'bar';
  const segments = classes.map((k) => {
    const seg = document.createElement('span');
    seg.className = 'seg';
    seg.style.background = meta.classes[k]?.colour ?? '#7d9460';
    seg.style.flexGrow = '0';
    bar.appendChild(seg);
    return { key: k, el: seg };
  });
  const say = document.createElement('span');
  say.className = 'say';
  band.append(bar, say);

  const sheet = document.createElement('div');
  sheet.id = 'scheme-sheet';
  sheet.hidden = true;
  sheet.innerHTML = `
    <h3>The Golden Valley in 2045</h3>
    <p class="lede">${meta.fields} fields, ${meta.newBuildings} new buildings
      and ${meta.newTrees.toLocaleString('en-GB')} new trees, allocated by rule
      rather than drawn: wetland where the water already is, campus within
      reach of GCHQ and a road, homes against the existing edge, agrivoltaics
      on the west-facing slopes, and an orchard ring within 150 m of anything
      built. Built area is capped at a third and comes out at
      ${(100 * (meta.areasHectares.homes + meta.areasHectares.campus)
        / Object.values(meta.areasHectares).reduce((a, b) => a + b, 0)).toFixed(0)}%.</p>
    <table>
      <tbody>${Object.entries(meta.areasHectares)
        .sort((a, b) => b[1] - a[1])
        .map(([k, v]) => `<tr><th>${k[0].toUpperCase()}${k.slice(1)}</th>
          <td>${v.toFixed(1)} ha</td></tr>`).join('')}
      </tbody>
      <tfoot><tr><th>Allocated</th><td>${Object.values(meta.areasHectares)
        .reduce((a, b) => a + b, 0).toFixed(1)} ha</td></tr></tfoot>
    </table>
    <p class="foot">The band above measures something narrower: the
      ${ha(grand)} hectares whose ground actually changes. The difference is
      field that keeps the class it already had — arable that was already
      farmland is in the scheme and does not change colour.</p>`;

  root.append(sheet);
  band.addEventListener('click', () => {
    const open = sheet.hidden;
    sheet.hidden = !open;
    band.setAttribute('aria-expanded', String(open));
    document.body.classList.toggle('scheme-open', open);
  });

  let shownAt = -1;
  return {
    band,
    sheet,
    totals,
    grandHectares: grand,

    /** Read the front's position and fill the band to match. */
    update() {
      const x = future.frontX;
      // The bin whose right edge the front has reached. Clamped rather than
      // wrapped: the front starts a kilometre west of the box and finishes
      // past its east edge, and both ends mean "none yet" and "all of it".
      const i = Math.round((x - progress.fromMetres) / progress.metresPerBin);
      const bin = Math.max(0, Math.min(progress.bins - 1, i));
      if (bin === shownAt) return;
      shownAt = bin;
      let arrived = 0;
      for (const s of segments) {
        const v = x <= progress.fromMetres ? 0 : progress.classes[s.key][bin];
        arrived += v;
        // Grown by area rather than by count, so the band is the split.
        s.el.style.flexGrow = String(v);
        s.el.style.opacity = v > 0.01 ? '1' : '0';
      }
      band.classList.toggle('empty', arrived < 0.05);
      say.textContent = arrived < 0.05
        ? 'What 2045 does to this ground'
        : (arrived >= grand - 0.05
          ? `${ha(grand)} ha changed · ${meta.fields} fields · `
            + `${meta.newBuildings} buildings · `
            + `${meta.newTrees.toLocaleString('en-GB')} trees`
          : `${ha(arrived)} of ${ha(grand)} ha changed`);
    },

    /** The band's own reading, for a test that wants the truth not the text. */
    arrivedHectares() {
      const i = Math.round(
        (future.frontX - progress.fromMetres) / progress.metresPerBin);
      const bin = Math.max(0, Math.min(progress.bins - 1, i));
      return future.frontX <= progress.fromMetres ? 0
        : classes.reduce((s, k) => s + progress.classes[k][bin], 0);
    },

    /** Every class, named, for the sheet and for anyone reading the code. */
    legend: classes.map((k) => ({
      key: k, name: SAYS[k]?.[0] ?? k, is: SAYS[k]?.[1] ?? '',
      hectares: totals[k], colour: meta.classes[k]?.colour,
    })),
  };
}
