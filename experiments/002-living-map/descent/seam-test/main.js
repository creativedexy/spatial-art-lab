// Session C — the seam test.
//
// The one genuinely unproven idea in the living map is the hand-off: the map
// is live WebGL, the descent is a pre-rendered clip, and the viewer must not
// see either cut. This page runs the hand-off for real and measures both
// seams as a number, so "invisible" stops being a matter of opinion.
//
//   live canvas @ A ──fade──▶ clip plays ──fade──▶ live canvas @ B
//   ^ in-seam: clip frame 0 vs live A     ^ out-seam: clip frame N vs live B
//
// Modes (URL parameters):
//   ?capture=1  render every frame of the path, plus the destination as it
//               would look if the clip landed N metres off, and POST them to
//               the capture server — this is how the control clip is made
//   (none)      interactive: run it, flip between clip and live, judge by eye

import * as THREE from 'three';
import { buildScene, heightAtLocal } from '../../golden-valley/scene.js';
import { PATH, frameCount, cameraAt, makeCamera } from '../path.js';

const params = new URLSearchParams(location.search);
const capturing = params.has('capture');

const frameEl = document.getElementById('frame');
const video = document.getElementById('clip');
const scene = buildScene();
const camera = makeCamera();

// ?clip=name.webm swaps which encode is under test, so codec error can be
// measured separately from everything else.
if (params.has('clip')) video.src = `../clips/${params.get('clip')}`;

const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
frameEl.appendChild(renderer.domElement);
const render = () => renderer.render(scene, camera);
const wait = (ms) => new Promise((r) => setTimeout(r, ms));

// The clip has one aspect ratio for ever, so the stage is letterboxed to it
// rather than filling the window — a generated descent pins your frame shape.
function fit() {
  if (capturing) {
    renderer.setPixelRatio(1);
    renderer.setSize(PATH.size[0], PATH.size[1]);
    frameEl.style.width = `${PATH.size[0]}px`;
    frameEl.style.height = `${PATH.size[1]}px`;
    return;
  }
  const stage = document.getElementById('stage').getBoundingClientRect();
  const aspect = PATH.size[0] / PATH.size[1];
  const w = Math.min(stage.width, stage.height * aspect);
  frameEl.style.width = `${Math.floor(w)}px`;
  frameEl.style.height = `${Math.floor(w / aspect)}px`;
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
  renderer.setSize(Math.floor(w), Math.floor(w / aspect), false);
  render();
}
fit();
addEventListener('resize', fit);

// --- landing error ----------------------------------------------------------
// A generated clip will not land exactly where the maths says it should. This
// nudges the live camera off the clip's last frame by N metres so we can ask
// the useful question: how much drift can a fade of a given length hide?
function placeAt(t, errorMetres = 0) {
  cameraAt(t, camera, heightAtLocal);
  if (errorMetres) {
    camera.position.x += errorMetres * 0.7;
    camera.position.y += errorMetres * 0.5;
    camera.position.z += errorMetres * 0.5;
    camera.updateMatrixWorld();
  }
}

// --- capture mode -----------------------------------------------------------
// One browser launch renders the whole path and posts each frame to the
// capture server, which encodes them. Rendering the clip from the same scene
// as the live map gives a *control*: a descent whose seams are perfect by
// construction, so any error measured afterwards is the pipeline's, not the
// world's.
async function post(name) {
  const blob = await new Promise((r) => renderer.domElement.toBlob(r, 'image/png'));
  await fetch(`/__frame/${name}`, { method: 'POST', body: blob });
}

async function runCapture() {
  document.getElementById('panel').hidden = true;
  for (let i = 0; i < frameCount; i++) {
    placeAt(i / (frameCount - 1));
    render();
    await post(String(i).padStart(4, '0'));
  }
  // The destination as the live map would draw it if the clip landed N metres
  // off. Comparing these against the clip's last frame gives the drift budget.
  const errors = (params.get('errors') ?? '0').split(',').map(Number);
  for (const e of errors) {
    placeAt(1, e);
    render();
    await post(`land-${e}`);
  }
  await fetch('/__done', {
    method: 'POST',
    body: JSON.stringify({ frames: frameCount, landings: errors }),
  });
}

// --- seam measurement -------------------------------------------------------
// Both images are drawn into the same small canvas, so a clip at 1280x720 and
// a canvas at whatever the window happens to be are compared fairly.
const MW = 640, MH = 360;
const mk = () => Object.assign(document.createElement('canvas'), { width: MW, height: MH })
  .getContext('2d', { willReadFrequently: true });
const ctxClip = mk();
const ctxLive = mk();

// 'seeked' only promises the decoder moved; it does not promise a frame was
// painted, and drawImage takes the *painted* one. Headless Chromium happily
// hands back the previous frame — which is exactly how the first version of
// this test measured a 6.8% seam that did not exist. Wait for the frame
// callback where it exists, and never hang if it does not fire.
function seek(t) {
  return new Promise((resolve) => {
    let settled = false;
    const finish = () => { if (!settled) { settled = true; resolve(); } };
    video.addEventListener('seeked', () => {
      if (video.requestVideoFrameCallback) {
        video.requestVideoFrameCallback(finish);
        setTimeout(finish, 400);
      } else {
        requestAnimationFrame(() => requestAnimationFrame(finish));
      }
    }, { once: true });
    video.currentTime = t;
  });
}

/** Mean absolute RGB difference as a percentage, plus a difference image. */
function compare(target) {
  const a = ctxClip.getImageData(0, 0, MW, MH).data;
  const b = ctxLive.getImageData(0, 0, MW, MH).data;
  const out = target ? target.getContext('2d').createImageData(target.width, target.height) : null;
  const sx = target ? MW / target.width : 1;
  const sy = target ? MH / target.height : 1;
  let sum = 0, peak = 0;
  for (let i = 0; i < a.length; i += 4) {
    const d = Math.abs(a[i] - b[i]) + Math.abs(a[i + 1] - b[i + 1]) + Math.abs(a[i + 2] - b[i + 2]);
    sum += d;
    if (d > peak) peak = d;
  }
  if (out) {
    for (let y = 0; y < target.height; y++) {
      for (let x = 0; x < target.width; x++) {
        const i = ((y * sy | 0) * MW + (x * sx | 0)) * 4;
        const o = (y * target.width + x) * 4;
        const d = Math.min(255, (Math.abs(a[i] - b[i]) + Math.abs(a[i + 1] - b[i + 1])
          + Math.abs(a[i + 2] - b[i + 2])) * 4);
        out.data[o] = d; out.data[o + 1] = d * 0.55; out.data[o + 2] = 40; out.data[o + 3] = 255;
      }
    }
    target.getContext('2d').putImageData(out, 0, 0);
  }
  const n = a.length / 4;
  return { meanPercent: +(sum / n / 765 * 100).toFixed(3), peakPercent: +(peak / 765 * 100).toFixed(1) };
}

async function measureSeam(videoTime, t, errorMetres, target) {
  await seek(videoTime);
  ctxClip.drawImage(video, 0, 0, MW, MH);
  placeAt(t, errorMetres);
  render();
  ctxLive.drawImage(renderer.domElement, 0, 0, MW, MH);
  return compare(target);
}

async function measureBoth(errorMetres) {
  const last = Math.max(0, video.duration - 0.5 / PATH.fps);
  const inSeam = await measureSeam(0, 0, 0, document.getElementById('dIn'));
  const outSeam = await measureSeam(last, 1, errorMetres, document.getElementById('dOut'));
  return { errorMetres, inSeam, outSeam };
}

// --- interactive ------------------------------------------------------------
const readout = document.getElementById('readout');
const fadeInput = document.getElementById('fade');
const errInput = document.getElementById('err');
const fadeMs = () => +fadeInput.value;
const errM = () => +errInput.value;
fadeInput.oninput = () => { document.getElementById('fadeval').textContent = `${fadeMs()} ms`; };
errInput.oninput = () => { document.getElementById('errval').textContent = `${errM()} m`; };

async function runDescent() {
  const run = document.getElementById('run');
  run.disabled = true;
  const fade = fadeMs();

  placeAt(0);            // 1. live map, sitting on the clip's first frame
  render();
  await seek(0);
  video.style.transition = `opacity ${fade}ms linear`;
  video.style.opacity = '1';   // 2. cross-fade in over an identical image
  await wait(fade + 20);

  await video.play();          // 3. the clip carries the descent
  // 4. while the clip is opaque, move the live camera to the destination and
  //    render once — the hand-back must never wait on a first frame.
  placeAt(1, errM());
  render();

  const endsAt = video.duration - fade / 1000;
  await new Promise((resolve) => {
    const check = () => {
      if (video.currentTime >= endsAt || video.ended) { resolve(); return; }
      requestAnimationFrame(check);
    };
    check();
  });
  video.style.opacity = '0';   // 5. cross-fade out onto the live map at B
  await wait(fade + 20);
  video.pause();
  run.disabled = false;
}

let flipping = null;
document.getElementById('flip').onclick = async () => {
  if (flipping) { clearInterval(flipping); flipping = null; video.style.opacity = '0'; return; }
  await seek(Math.max(0, video.duration - 0.5 / PATH.fps));
  placeAt(1, errM());
  render();
  video.style.transition = 'none';
  let on = false;
  flipping = setInterval(() => { on = !on; video.style.opacity = on ? '1' : '0'; }, 700);
};

document.getElementById('run').onclick = runDescent;
document.getElementById('measure').onclick = async () => {
  readout.textContent = 'measuring…';
  const r = await measureBoth(errM());
  readout.innerHTML = `in-seam <b>${r.inSeam.meanPercent}%</b> (peak ${r.inSeam.peakPercent}%) `
    + `&middot; out-seam <b>${r.outSeam.meanPercent}%</b> (peak ${r.outSeam.peakPercent}%) `
    + `at ${r.errorMetres} m landing error`;
};

// --- entry points -----------------------------------------------------------
if (capturing) {
  runCapture();
} else {
  placeAt(0);
  render();
}

window.__seamReady = true;
