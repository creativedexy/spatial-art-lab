// Buildings that survive being walked up to.
//
// Phase 8, replacing the Meshy placement of task 001 part 2. Two models came
// back from image-to-3D soft and blobby, with every pane of glass turned into
// a hole, and the finding was the tool rather than the prompt: generative
// image-to-3D is wrong for straight-lined architecture. The campus block and
// the National Cyber Innovation Centre are a bar and a wedge. Bars and wedges
// are rules.
//
// So the facade is written rather than drawn, and written in the shader rather
// than baked to an image. Three reasons, in order of how much they matter:
//
//   It is exact on every footprint. The scheme generates its own blocks, and
//   they are not all one size; a rule in metres lands the same 3 m bay on a
//   38 m wall and on a 17 m one, and a texture would have had to stretch.
//
//   It stays crisp. The campus close-up is the plate that failed the
//   no-empty-frames rule at a hundred metres, and the whole point of doing
//   this is that someone can come closer. A 1024 px texture has a distance at
//   which it turns to porridge; an edge computed per fragment does not.
//
//   It weighs nothing. Phase 7 spent a day getting the first load from 25 MB
//   to 7.7, and the two GLBs this replaces were 11.32 MB of that before they
//   were compressed. This is about ninety lines of GLSL.
//
// The vocabulary comes from brief 003, which Dex approved: pale timber and
// buff stone, strong horizontal banding, never curtain wall. And the one
// absolute — **no transparent glass anywhere.** Transparency is what made the
// Meshy models read as damaged; a dark reflective pane is opaque and reads as
// glass because of what it does with the light, not because you can see
// through it.

/** Metres. The scheme's own storey height: 17 m over five floors. */
export const STOREY = 3.4;
/** Metres. One structural bay, and therefore one window. */
export const BAY = 3.0;

// Declarations shared by the facade fragment code. `aFacade` arrives in metres
// — distance along the wall, height up it — and `aSurface` is 0 for a wall and
// 1 for a roof, because a family is drawn as one mesh.
export const FACADE_VARYINGS = /* glsl */`
  varying vec2 vFacade;
  varying float vSurface;
  varying float vBay;
  varying float vWallTop;
`;

export const FACADE_VERTEX = /* glsl */`
  attribute vec2 aFacade;
  attribute float aSurface;
  attribute float aBay;
  attribute float aWallTop;
` + FACADE_VARYINGS;

export const FACADE_VERTEX_BODY = /* glsl */`
  vFacade = aFacade;
  vSurface = aSurface;
  vBay = aBay;
  vWallTop = aWallTop;
`;

// A cheap deterministic hash, so "some roofs have PV" and "the bands vary a
// little" are decisions the shader can make per building without a texture and
// without the answer changing between frames.
const NOISE = /* glsl */`
  float fHash(vec2 p) {
    return fract(sin(dot(floor(p), vec2(12.9898, 78.233))) * 43758.5453);
  }
  // A band edge that stays one pixel wide however far away it is: fwidth is
  // how fast the coordinate is changing on screen, so this is an antialiased
  // step rather than a hard one that would crawl and shimmer at distance.
  float fEdge(float x, float at) {
    float w = max(fwidth(x), 1e-5);
    return smoothstep(at - w, at + w, x);
  }
  float fBand(float x, float lo, float hi) {
    return fEdge(x, lo) * (1.0 - fEdge(x, hi));
  }
`;

/**
 * The campus block: five storeys of banded buff stone over a glazed ground
 * floor, a window every bay, a parapet, and a sedum roof with PV on some of
 * them.
 *
 * Everything is a function of `vFacade` in metres, so none of the numbers
 * below are proportions of anything — they are the sizes the architecture
 * actually is.
 */
export const CAMPUS_FRAGMENT = NOISE + /* glsl */`
  vec3 fCampus(vec2 m, float surf, float bayW, float wallTop,
               inout vec3 nrm, inout float rough, vec3 base) {
    // --- the roof ---------------------------------------------------------
    if (surf > 0.5) {
      vec3 sedum = vec3(0.40, 0.47, 0.29);
      // Sedum is a planted mat, not a lawn: mottle it, or a flat roof under a
      // low sun reads as a sheet of card.
      float mottle = fHash(m * 1.7) * 0.20 + fHash(m * 0.4) * 0.12;
      vec3 c = sedum * (0.84 + mottle);
      rough = 0.96;
      // PV on about a third of them, on a 1.6 m pitch and held 2.5 m off the
      // edge, so it reads as equipment standing on a roof rather than as the
      // roof itself.
      if (fHash(floor(m / 40.0) + 3.7) > 0.66) {
        float rows = fBand(fract(m.y / 1.6), 0.10, 0.84);
        float inset = fBand(m.x, 2.5, 34.0) * fBand(m.y, 2.5, 14.0);
        c = mix(c, vec3(0.10, 0.12, 0.16), rows * inset * 0.92);
        rough = mix(rough, 0.26, rows * inset);
      }
      return c;
    }

    // --- the walls --------------------------------------------------------
    // The palette, and the reason this is not the office block the first
    // version came out as: the brief's vocabulary is pale timber and buff
    // stone in strong horizontal bands, never curtain wall. A uniform grid of
    // punched windows is a curtain wall with the glass swapped for holes.
    vec3 stone  = base * vec3(1.02, 0.99, 0.93);
    vec3 course = base * vec3(0.80, 0.74, 0.63);   // the deep spandrel band
    vec3 timber = vec3(0.72, 0.58, 0.39);
    vec3 glass  = vec3(0.10, 0.13, 0.16);

    float along = m.x;
    float up = m.y;

    // The ground floor is fully glazed, set back under a pale timber soffit.
    // Opaque dark reflective glass with slim mullions and no transparency
    // anywhere — transparency is what made the Meshy models read as damaged.
    if (up < ${STOREY.toFixed(1)}) {
      float mullion = fBand(fract(along / 1.5), 0.035, 0.965);
      float head = 1.0 - fEdge(up, ${(STOREY - 0.5).toFixed(2)});
      float cill = fEdge(up, 0.4);
      vec3 c = mix(glass * 0.6, glass, mullion);
      c = mix(base * 0.62, c, cill);          // the plinth it stands on
      c = mix(timber * 1.06, c, head);        // the soffit over it
      rough = mix(0.88, 0.15, mullion * cill * head);
      // The whole storey is recessed, so the bands above read as carried
      // rather than as resting on the grass.
      nrm = normalize(nrm + vec3(0.0, 0.14 * cill * head, 0.0));
      return c;
    }

    // The parapet: the top 0.6 m is plain stone, a shade paler, with a coping
    // shadow under it. The scheme's blocks are 11.9 to 17 m and the storey is
    // 3.4, so the top floor is never a whole one — without this the banding
    // simply stops wherever the wall happens to end, and the building has no
    // top. Measured DOWN from this wall's own head, which is why the wall
    // height travels with the vertex.
    if (up > wallTop - 0.6) {
      float coping = 1.0 - fEdge(up, wallTop - 0.52);
      vec3 c = mix(base * 1.06, base * 0.74, coping);
      rough = 0.86;
      return c;
    }

    // Upper storeys. Each is one horizontal band: a deep stone course with a
    // continuous ribbon of window sitting in it. The course is 1.5 m of the
    // 3.4 — nearly half the storey — which is what makes the building read in
    // stripes from a distance instead of as a grid of holes.
    float inFloor = fract((up - ${STOREY.toFixed(1)}) / ${STOREY.toFixed(1)})
                    * ${STOREY.toFixed(1)};
    float bay = fract(along / bayW) * bayW;

    vec3 c = mix(stone, course, fBand(inFloor, 0.0, 1.45));
    c *= 0.97 + fHash(vec2(along, up) * 0.8) * 0.06;
    rough = 0.84;

    // A shadow line at each storey joint: 60 mm, and it does more for the
    // horizontal reading than any amount of colour.
    float joint = fBand(inFloor, 0.0, 0.06);
    c = mix(c, c * 0.55, joint);

    // The window: 1.9 m of the bay and 1.35 m tall, sitting on a 1.45 m cill,
    // recessed 300 mm. Deliberately wider than it is tall — a ribbon, not a
    // punched hole.
    float pad = (bayW - 1.9) * 0.5;
    float w = fBand(bay, pad, bayW - pad);
    float h = fBand(inFloor, 1.45, 2.80);
    float pane = w * h;
    c = mix(c, glass, pane);
    rough = mix(rough, 0.13, pane);

    // A timber fin at each bay edge, standing 120 mm proud. This is the piece
    // that turns a grid into the scheme's own language, and it is also what
    // stops a 38 m elevation reading as one flat plane.
    float fin = fBand(bay, pad - 0.30, pad - 0.06)
              + fBand(bay, bayW - pad + 0.06, bayW - pad + 0.30);
    fin *= fEdge(inFloor, 1.30) * (1.0 - fEdge(inFloor, 2.95));
    c = mix(c, timber, fin * 0.92);
    rough = mix(rough, 0.7, fin);

    // The reveals. Tilt the normal at each edge of the opening so the recess
    // catches the afternoon sun on one side and shades on the other — the
    // only reason a window reads as a hole rather than a dark rectangle
    // painted on the wall.
    float dx = fEdge(bay, pad) - fEdge(bay, bayW - pad);
    float dy = fEdge(inFloor, 1.45) - fEdge(inFloor, 2.80);
    nrm = normalize(nrm + vec3(dx, dy, 0.0) * 0.6 * (1.0 - pane)
                        + vec3(0.0, 0.0, 0.25) * fin);
    return c;
  }
`;

/**
 * The National Cyber Innovation Centre. A wedge, so three surfaces and no
 * repetition worth speaking of: the meadow you can walk up, the stone edge
 * that frames it, the flank, and the glazed head.
 *
 * `aSurface` is 0 for a flank, 1 for the roof, 2 for the high end.
 */
export const NCIC_FRAGMENT = NOISE + /* glsl */`
  vec3 fNcic(vec2 m, float surf, float head, inout vec3 nrm, inout float rough,
             vec3 base) {
    vec3 stone  = vec3(0.87, 0.83, 0.74);
    vec3 glass  = vec3(0.10, 0.13, 0.16);

    // --- the roof: one continuous wildflower meadow ------------------------
    if (surf > 0.5 && surf < 1.5) {
      // m.x runs up the slope in metres, m.y across the width. A 1.2 m stone
      // edge frames it on all four sides — the detail that stops a planted
      // roof reading as a green triangle stuck on the side of a building.
      float edge = 1.0
        - fBand(m.x, 1.2, ${(60 * 1.0353).toFixed(1)} - 1.2) * fBand(m.y, 1.2, 25.8);
      vec3 meadow = base * vec3(0.94, 1.02, 0.86);
      // Wildflower, not lawn: a coarse grain of grass with sparse warm and
      // pale flecks through it, which is what a species-rich roof looks like
      // from anywhere further than arm's length.
      float grain = fHash(m * 3.1) * 0.26 + fHash(m * 0.9) * 0.16;
      vec3 c = meadow * (0.80 + grain);
      float flower = fHash(m * 7.3 + 11.0);
      c = mix(c, vec3(0.86, 0.80, 0.44), step(0.965, flower) * 0.55);
      c = mix(c, vec3(0.80, 0.70, 0.74), step(0.986, flower) * 0.45);
      rough = 0.97;
      c = mix(c, stone, edge);
      rough = mix(rough, 0.8, edge);
      return c;
    }

    // --- the high end: fully glazed, and opaque ----------------------------
    if (surf > 1.5) {
      // Mullions every 1.5 m and a transom at each storey, so the head reads
      // as a glazed wall at a real size rather than as a dark panel. No
      // transparency: this is the surface Meshy turned into holes.
      float mull = fBand(fract(m.x / 1.5), 0.04, 0.96);
      float tran = fBand(fract(m.y / ${STOREY.toFixed(1)}), 0.05, 0.95);
      vec3 c = mix(glass * 0.45, glass, mull * tran);
      // Sky sits in the top of a glazed wall and ground in the bottom, which
      // is most of what makes glass look like glass at this distance.
      c = mix(c * 0.86, c * 1.5, clamp(m.y / max(head, 1.0), 0.0, 1.0));
      rough = mix(0.5, 0.09, mull * tran);
      nrm = normalize(nrm + vec3(0.0, 0.0, 0.06) * (1.0 - mull * tran));
      return c;
    }

    // --- the flanks: buff stone with long horizontal glazing ---------------
    // The wedge is a triangle on this face, so the glazing is banded by
    // height and runs the length of it: two ribbons, the way a section
    // through a stacked floorplate would read.
    float up = m.y;
    vec3 c = stone * (0.97 + fHash(m * 0.8) * 0.06);
    rough = 0.85;
    float band = fBand(fract(up / ${(STOREY * 1.6).toFixed(2)}), 0.30, 0.72);
    // Stop the ribbon short of the sloping edge, or it runs off into the sky
    // where the wall has already ended.
    float within = 1.0 - fEdge(up, ${(16 / 60).toFixed(4)} * m.x - 1.1);
    float pane = band * within * fEdge(m.x, 3.0);
    c = mix(c, glass, pane);
    rough = mix(rough, 0.12, pane);
    nrm = normalize(nrm + vec3(0.0, fEdge(fract(up / ${(STOREY * 1.6).toFixed(2)}), 0.30)
                                    - fEdge(fract(up / ${(STOREY * 1.6).toFixed(2)}), 0.72),
                               0.0) * 0.4 * within);
    return c;
  }
`;

/**
 * Patch a standard material so its fragment shader draws the facade.
 *
 * Written as a function of the material rather than a replacement for it,
 * because everything else this map does to these buildings — the wave that
 * grows them, the wind, the deterministic clock — is already layered on the
 * same material through `onBeforeCompile`, and a facade that replaced the
 * material would quietly undo all of it.
 */
export function facadeChunk(kind) {
  if (kind !== 'campus' && kind !== 'ncic') return null;
  if (kind === 'ncic') {
    return {
      vertex: FACADE_VERTEX,
      vertexBody: FACADE_VERTEX_BODY,
      fragment: FACADE_VARYINGS + NCIC_FRAGMENT,
      fragmentBody: /* glsl */`
        {
          float fRough = roughnessFactor;
          vec3 fNormal = normal;
          vec3 fCol = fNcic(vFacade, vSurface, vWallTop, fNormal, fRough,
                            diffuseColor.rgb);
          diffuseColor.rgb = fCol;
          normal = fNormal;
          roughnessFactor = fRough;
        }
      `,
    };
  }
  return {
    vertex: FACADE_VERTEX,
    vertexBody: FACADE_VERTEX_BODY,
    fragment: FACADE_VARYINGS + CAMPUS_FRAGMENT,
    // Runs after the standard material has established its own normal and
    // roughness, and before lighting uses them.
    fragmentBody: /* glsl */`
      {
        float fRough = roughnessFactor;
        vec3 fNormal = normal;
        vec3 fCol = fCampus(vFacade, vSurface, vBay, vWallTop, fNormal, fRough,
                            diffuseColor.rgb);
        diffuseColor.rgb = fCol;
        normal = fNormal;
        roughnessFactor = fRough;
      }
    `,
  };
}
