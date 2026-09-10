// The heightmap, unpacked.
//
// Phase 7. The survey arrives as one number per square metre over a 2 km box:
// four million samples, and at uint16 across a 34.96 m elevation span each one
// carried 0.53 mm of precision. The Environment Agency's own composite DTM is
// good to about 15 cm, so fifteen of those sixteen bits were describing noise,
// and 7.63 MB of a phone's first thirty seconds went on transmitting it.
//
// What is stored instead is twelve bits — a 0.85 cm step, still 2.6x finer
// than the measured median difference between neighbouring cells in this very
// file, which is the number that decides whether quantisation can terrace a
// gentle field. It cannot; the LiDAR's own roughness is larger.
//
// The rest is arithmetic. Each sample is predicted from the average of its
// left and upper neighbours, which for ground is nearly right nearly always,
// so the residual is small; zigzag makes small negatives small unsigned; the
// low and high bytes go in separate planes so gzip sees one run of nearly
// zeroes rather than four million alternating ones. 7.63 MB becomes 1.98.
//
// Deliberately not an image. A PNG or a WebP would have to come back through
// a canvas, and a canvas is where colour management lives — a browser is
// entitled to transform what it decodes, and a terrain that shifts by a
// colour profile is the exact class of silent drift this experiment spends
// its time hunting. Bytes in, bytes out, the same on every machine.
//
// `scripts/compress_assets.py` writes it; this reads it; nothing else knows.

/** Uint16 heights, whatever the file on disk turned out to be. */
export async function loadHeights(href, meta) {
  const res = await fetch(href);
  if (!res.ok) throw new Error(`heightmap ${res.status} at ${href}`);
  if (!/^delta\d+$/.test(meta.binFormat ?? '')) {
    return new Uint16Array(await res.arrayBuffer());
  }
  const bits = Number(meta.binFormat.slice(5));
  if (typeof DecompressionStream !== 'function') {
    throw new Error('this browser cannot ungzip a stream; serve the raw .bin');
  }
  const packed = new Uint8Array(await new Response(
    res.body.pipeThrough(new DecompressionStream('gzip'))).arrayBuffer());
  return unpack(packed, meta.binPixels[0], meta.binPixels[1], bits);
}

/** Exported for the tests, which check it against the encoder's own output. */
export function unpack(packed, W, H, bits) {
  const n = W * H;
  if (packed.length !== 2 * n) {
    throw new Error(`heightmap is ${packed.length} bytes, expected ${2 * n}`);
  }
  const lo = packed.subarray(0, n);
  const hi = packed.subarray(n, 2 * n);
  const q = new Int32Array(n);
  const out = new Uint16Array(n);
  const up = 16 - bits;
  const down = 2 * bits - 16;      // bit replication, so 4095 reaches 65535
  for (let y = 0, i = 0; y < H; y++) {
    for (let x = 0; x < W; x++, i++) {
      const z = lo[i] | (hi[i] << 8);
      const d = (z >>> 1) ^ -(z & 1);
      // On the first row and the first column there is only one neighbour, so
      // both terms are it and the average is it. The encoder does the same.
      const l = x > 0 ? q[i - 1] : (y > 0 ? q[i - W] : 0);
      const u = y > 0 ? q[i - W] : (x > 0 ? q[i - 1] : 0);
      const v = d + ((l + u) >> 1);
      q[i] = v;
      out[i] = (v << up) | (v >>> down);
    }
  }
  return out;
}
