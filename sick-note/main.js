// SICK NOTE — Sci-Fi Sitcom Toon, 1080×1920, 24 fps
import { clamp, lerp, seg, ss, eo, ei, eio, back, hash, TAU } from '/core/lib.js';
import { W, H, INK, init, frame, g, push, pop, translate, rotate, scale, reset, shape, fillOnly, stroke, ell, arc, rr, rect, spline, dot, text } from './toon.js';
import { nodd, gus, ivPole, PAL } from './chars.js';
import { clinic, bed, monitor, portal, sleepWorld, wash, FLOOR, BED, MON, PORTAL } from './world.js';

init(document.getElementById('c'));
const J = async f => { try { const r = await fetch(f); if (r.ok) return await r.json(); } catch (e) { } return null; };
const LINES = await J('voice/lines.json'), DURS = (await J('voice/out/dur.json')) || {}, LIPS = (await J('voice/out/lips.json')) || {};
const LINE = Object.fromEntries(LINES.map(l => [l.id, l]));
const vdur = id => DURS[id] ?? LINE[id].text.length * .06;

export const DUR = 35.0;
export const VO = { p1: 2.7, d0: 9.0, p2: 13.5, d1: 24.1 };
// shots: [start, id]
const SHOTS = [[0, 'enter'], [2.5, 'two'], [8.9, 'cuN'], [10.8, 'scanG'], [13.3, 'cuG'], [15.0, 'self'], [16.25, 'scanN'], [18.75, 'boom'], [21.25, 'pause'], [24.0, 'punch'], [27.6, 'fall'], [30.6, 'end']];
const shotAt = t => { let s = SHOTS[0]; for (const x of SHOTS) if (t >= x[0]) s = x; return s; };
const q = t => Math.floor(t * 12 + 1e-6) / 12;    // 12 fps acting time

function talk(who, t) {
  const tq = q(t);
  for (const [id, t0] of Object.entries(VO)) {
    const L = LINE[id]; if (L.who !== who) continue;
    if (tq >= t0 && tq < t0 + vdur(id)) {
      const k = Math.floor((tq - t0) * 24), lp = LIPS[id];
      const o = lp ? (lp.o[k] ?? 0) : .5, b = lp ? (lp.b[k] ?? .5) : .5;
      return { o, w: .8 + .45 * b - .2 * o, talking: true };
    }
  }
  return { o: 0, w: 1, talking: false };
}
const blinkAt = (t, list, d = .14) => list.some(b => t >= b && t < b + d);
const popOpen = x => x <= 0 ? 0 : back(clamp(x / .3), 1.6);
const landSq = (t, tl) => { const u = t - tl; if (u < 0 || u > .6) return 1; return 1 - .22 * Math.exp(-u * 9) * Math.cos(u * 30); };

function cam(cx, cy, z, shake = 0, t = 0, rot = 0) {
  reset(); translate(W / 2, H / 2);
  if (shake) { const f = Math.floor(t * 24); translate((hash(f) - .5) * shake * 2, (hash(f + 77) - .5) * shake * 2); }
  scale(z); if (rot) rotate(rot); translate(-cx, -cy);
}

// —— default poses ——
const NX = 300, NS = .92, GX = 770, GY = BED.top + 140;
function N(t, o = {}) {
  const m = talk('NODD', t), tq = q(t);
  return { x: NX, y: FLOOR, s: NS, face: 1, t, lid: .58, look: [.4, .1], mouth: { o: m.o, w: m.w, sm: -.3 }, sq: 1 + .008 * Math.sin(tq * 2.1), headTilt: .16 + (m.talking ? (m.o - .3) * .06 : 0), lean: .14,
    blink: blinkAt(t, [6.2, 12.0, 20.0, 22.9, 26.4]), ...o };
}
function G(t, o = {}) {
  const m = talk('GUS', t), tq = q(t);
  return { x: GX, y: GY, s: 1, face: -1, t, sit: true, nerv: .35, lid: .12, look: [.5, -.1], brow: 1, mouth: { o: m.o * 1.2, w: m.w, sm: -.5 }, case: 'lap', sq: 1 + .012 * Math.sin(tq * 3.1),
    headTilt: m.talking ? (m.o - .3) * .1 : Math.sin(tq * 1.7) * .03, blink: blinkAt(t, [4.6, 8.0, 21.9, 29.9]), ...o };
}

// —— terminal readouts ——
function readout(t) {
  if (t < 16.25) {
    const u = clamp(seg(t, 11.0, 12.5));
    const lines = [{ s: 'FATIGUE-O-SCAN 9' }, { s: 'PATIENT: GUS' }];
    const v = Math.round(87 * eio(u));
    lines.push({ s: t >= 12.5 ? `${v}%  SEVERE` : `${v}%`, col: t >= 12.5 ? '#ff5a4a' : '#ffb020', size: 46 });
    return { lines, bar: .87 * eio(u), barCol: t >= 12.5 ? '#ff5a4a' : '#ffb020' };
  }
  const steps = [[16.25, '100%'], [17.1, '250%'], [17.6, '480%'], [17.9, '999%'], [18.1, '9999%'], [18.25, '99999%']];
  let v = '0%'; for (const [tt, s] of steps) if (t >= tt) v = s;
  if (t >= 18.4) return { lines: [{ s: 'PATIENT: DR. NODD' }, { s: 'ERROR', col: '#ff5a4a', size: 90 }, { s: '' }], bar: 1, barCol: '#ff5a4a', err: 1, crack: 1 };
  return { lines: [{ s: 'PATIENT: DR. NODD' }, { s: '' }, { s: v, col: '#ff5a4a', size: 70 }], bar: 1, barCol: '#ff5a4a', err: t >= 17.9 ? 1 : 0 };
}

// —— the room, drawn in world space ——
function room(t, { portalOpen = 0, noddP = null, gusP = null, gusFirst = false, iv = {}, tube = null, wash_ = 0, mon = null } = {}) {
  clinic(t, { flicker: Math.floor(t * 12) % 37 === 0 });
  monitor(t, mon || (t >= 18.4 ? readout(t) : null) || { lines: [{ s: 'FATIGUE-O-SCAN 9' }, { s: 'READY_', col: '#5ae07a' }] });
  if (portalOpen > 0) portal(PORTAL.x, PORTAL.y, PORTAL.r, t, { open: portalOpen, sx: .86, inside: (rx, ry) => sleepWorld(rx, ry, t, { snore: Math.max(0, Math.sin(t * 2.2)) }) });
  const out = ivPole(150, FLOOR, t, { level: iv.level ?? .62, lean: iv.lean ?? 0 });
  bed(t);
  if (noddP) nodd(noddP);
  if (gusP) gus(gusP);
  if (tube) { // coffee tube from the IV bag to Dr. Nodd's mouth
    stroke(spline([out, [out[0] + 20, out[1] + 200], [tube[0] - 60, tube[1] + 120], tube], false), 9);
    stroke(spline([out, [out[0] + 20, out[1] + 200], [tube[0] - 60, tube[1] + 120], tube], false), 4, { line: PAL.coffee });
  }
  if (wash_ > 0) wash('#ff3fd2', wash_);
}
// Nodd's mouth in world space (for the tube): head pivot (70,-960) rotated by lean around hip.
function noddMouth(P) {
  const s = P.s, lean = P.lean, ht = P.headTilt;
  const hx = 70, hy = -960 + 450, c = Math.cos(lean), sn = Math.sin(lean);
  const px = hx * c - hy * sn, py = hx * sn + hy * c - 450;
  const mx = 40 * Math.cos(ht) - 108 * Math.sin(ht), my = 40 * Math.sin(ht) + 108 * Math.cos(ht);
  const mx2 = mx * c - my * sn, my2 = mx * sn + my * c;
  return [P.x + (px + mx2) * s, P.y + (py + my2) * s];
}

// —— subtitles: Arabic on top, English below, speaker pill ——
const SUBS = Object.entries(VO).map(([id, t0]) => ({ id, t0, t1: t0 + Math.max(1.8, vdur(id) + .6), ar: LINE[id].ar, en: LINE[id].sub || LINE[id].text, who: LINE[id].who }));
function wrap(str, font, maxW, rtl = false) {
  g.font = font; const words = str.split(' '), out = []; let cur = '';
  for (const w of words) { const tr = cur ? cur + ' ' + w : w; if (g.measureText(tr).width > maxW && cur) { out.push(cur); cur = w; } else cur = tr; }
  if (cur) out.push(cur); return out;
}
function subs(t) {
  const s = SUBS.filter(x => t >= x.t0 && t < x.t1).slice(-1)[0]; if (!s) return;
  g.setTransform(1, 0, 0, 1, 0, 0);
  const fa = '800 56px "Baloo Bhaijaan 2"', fe = '800 40px "Baloo 2"';
  const ar = wrap(s.ar, fa, 920, true), en = wrap(s.en, fe, 920);
  const lhA = 70, lhE = 48, total = ar.length * lhA + en.length * lhE + 10;
  let y = H - 90 - total;
  // speaker pill
  const col = s.who === 'NODD' ? '#2e8c86' : '#e07a2a', name = s.who === 'NODD' ? 'DR. NODD' : 'GUS';
  g.font = '800 28px "Baloo 2"'; const pw = g.measureText(name).width + 40;
  g.beginPath(); g.roundRect(W / 2 - pw / 2, y - 52, pw, 42, 21); g.fillStyle = col; g.fill(); g.lineWidth = 6; g.strokeStyle = INK; g.stroke();
  g.fillStyle = '#fff'; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText(name, W / 2, y - 30);
  const draw = (str, font, yy, rtl) => {
    g.font = font; g.direction = rtl ? 'rtl' : 'ltr'; g.textAlign = 'center'; g.textBaseline = 'middle';
    g.lineJoin = 'round'; g.lineWidth = 12; g.strokeStyle = '#000'; g.strokeText(str, W / 2, yy); g.fillStyle = '#fff'; g.fillText(str, W / 2, yy);
    g.direction = 'ltr';
  };
  for (const L of ar) { draw(L, fa, y + lhA / 2, true); y += lhA; }
  y += 10;
  for (const L of en) { draw(L, fe, y + lhE / 2, false); y += lhE; }
}

// —— title (on the end card) ——
function title(t) {
  const u = t - 30.6; if (u < 0) return;
  const k = Math.floor(u * 12), sc = k === 0 ? .4 : k === 1 ? 1.18 : k === 2 ? .95 : 1;
  g.setTransform(1, 0, 0, 1, 0, 0);
  push(); reset(); translate(W / 2, 330); rotate(-.05); scale(sc);
  shape(rr(-430, -120, 860, 240, 30), { fill: '#2a2370', lw: 9 });
  text('SICK NOTE', 10, 14, { font: '400 150px "Lilita One"', fill: '#f08a3c', outlineW: 0 });
  text('SICK NOTE', 0, 4, { font: '400 150px "Lilita One"', fill: '#fff3c4', outlineW: 0 });
  pop();
}

const SHEET = location.search.includes('sheet');
function clipBox(x, y, w, h, fn) { g.save(); g.setTransform(1, 0, 0, 1, 0, 0); g.beginPath(); g.rect(x, y, w, h); g.clip(); g.fillStyle = '#f4ecd8'; g.fillRect(x, y, w, h); fn(); g.restore(); g.save(); g.setTransform(1, 0, 0, 1, 0, 0); g.lineWidth = 5; g.strokeStyle = INK; g.strokeRect(x, y, w, h); g.restore(); }
function label(s, x, y, size = 30) { g.setTransform(1, 0, 0, 1, 0, 0); g.font = `800 ${size}px "Baloo 2"`; g.fillStyle = INK; g.textAlign = 'center'; g.textBaseline = 'middle'; g.direction = 'ltr'; g.fillText(s, x, y); }
function modelSheet(t) {
  frame(t);
  g.setTransform(1, 0, 0, 1, 0, 0); g.fillStyle = '#efe4c8'; g.fillRect(0, 0, W, H);
  label('SICK NOTE — model sheet', W / 2, 50, 44);
  // full figures
  clipBox(20, 90, 1040, 760, () => {
    reset(); translate(0, 0);
    nodd({ x: 440, y: 820, s: .62, face: 1, t, lid: .58, look: [.4, .1], lean: .14, headTilt: .16, mouth: { o: 0, sm: -.3 } });
    nodd({ x: 250, y: 820, s: .62, face: -1, t, lid: .58, look: [.4, .1], lean: .14, headTilt: .16, holdF: 'scanner', armF: { h: [150, 120], bend: 20 } });
    gus({ x: 680, y: 820, s: .9, face: 1, t, lid: .12, brow: 1, look: [.4, 0], case: 'hand', mouth: { sm: -.5 } });
    gus({ x: 920, y: 820, s: .9, face: -1, t, lid: .12, brow: 1, look: [.4, 0], case: null, armF: { h: [70, -140], bend: 30 }, armB: { h: [-60, -120], bend: -20 }, mouth: { o: .6, sm: -.5 } });
  });
  label('Dr. Nodd', 300, 880); label('Gus', 800, 880);
  // expressions
  const NE = [['deadpan', {}], ['asleep', { closed: true, mouth: { o: .2, sm: 0 } }], ['talking', { mouth: { o: .6, w: 1, sm: -.2 } }], ['ERROR', { lid: .1, brow: .8, jit: 2, mouth: { o: .3, sm: -.8 } }]];
  NE.forEach(([n, o], i) => { const x = 20 + i * 262, y = 910; clipBox(x, y, 250, 300, () => { reset(); nodd({ x: x - 50, y: y + 1370, s: 1.05, face: 1, t, lid: .58, look: [.4, .1], lean: .14, headTilt: .16, mouth: { o: 0, sm: -.3 }, ...o }); }); label(n, x + 125, y + 325, 26); });
  const GE = [['nervous', {}], ['panic', { eyeS: 1.2, pupil: 3, brow: 1.6, lid: 0, mouth: { o: .7, sm: -.8 } }], ['talking', { mouth: { o: .55, sm: -.4 } }], ['asleep', { closed: true, brow: .2, mouth: { o: .15, sm: 0 } }]];
  GE.forEach(([n, o], i) => { const x = 20 + i * 262, y = 1270; clipBox(x, y, 250, 300, () => { reset(); gus({ x: x + 125, y: y + 640, s: 1.0, face: 1, t, lid: .12, brow: 1, look: [.3, 0], case: null, mouth: { sm: -.5 }, ...o }); }); label(n, x + 125, y + 325, 26); });
  // palette
  const pal = [['#9fd8b8', 'clinic'], ['#d8c7a0', 'floor'], ['#2e8c86', 'trim'], ['#3aa59a', 'Nodd'], ['#f08a3c', 'cap'], ['#a9d3f0', 'Gus'], ['#e0443a', 'tie'], ['#2a2370', 'sleep'], ['#f5c84a', 'stars'], ['#ff3fd2', 'portal only']];
  pal.forEach(([c, n], i) => { const x = 30 + i * 104, y = 1650; g.setTransform(1, 0, 0, 1, 0, 0); g.fillStyle = c; g.fillRect(x, y, 90, 90); g.lineWidth = 5; g.strokeStyle = INK; g.strokeRect(x, y, 90, 90); g.font = '800 20px "Baloo 2"'; g.fillStyle = INK; g.textAlign = 'center'; g.fillText(n, x + 45, y + 112); });
}
function render(t) {
  if (SHEET) return modelSheet(t);
  frame(t);
  g.setTransform(1, 0, 0, 1, 0, 0); g.fillStyle = '#9fd8b8'; g.fillRect(0, 0, W, H);
  const [t0, id] = shotAt(t), u = t - t0, tq = q(t);
  if (id === 'enter') {
    cam(540, 1000, 1.08, 0, t);
    const walkU = ss(seg(t, 0, 1.4)), fall = eo(clamp(seg(t, 1.45, 2.0)));
    const gx = lerp(1110, 1030, walkU);
    const step = t < 1.4 ? Math.sin(tq * 14) : 0;
    room(t, {
      noddP: N(t, { closed: true, lean: .22, headTilt: .3, mouth: { o: .15 + .1 * Math.sin(t * 3), sm: 0 } }),
      gusP: G(t, { x: gx, y: FLOOR - Math.max(0, step) * 8, sit: false, case: 'hand', rot: -.9 * fall, sq: landSq(t, 2.0), nerv: .1, lid: .5, brow: .3, look: [-.6, .2], mouth: { o: fall > .9 ? .2 : 0, sm: -.6 }, leg: [step * 18, -step * 18], closed: t > 2.0 }),
    });
  } else if (id === 'two') {
    cam(560, 920, lerp(1.1, 1.2, ss(seg(t, 2.5, 8.9))), 0, t);
    const wake = t >= 4.0;
    room(t, {
      noddP: N(t, { closed: !wake, lid: wake ? (t < 4.3 ? .8 : .62) : .6, lean: wake ? .14 : .22, headTilt: wake ? .16 : .3, look: [.6, .1] }),
      gusP: G(t, { armF: { h: [70 + Math.sin(tq * 5) * 40, -140 + Math.cos(tq * 4) * 40], bend: 30 }, armB: { h: [-60, -120 + Math.sin(tq * 6) * 30], bend: -20 }, case: 'lap', nerv: .5, kick: true }),
    });
  } else if (id === 'cuN') {
    cam(400, 640, 2.0, 0, t);
    const pull = ss(seg(t, 10.0, 10.5));
    room(t, { noddP: N(t, { look: [.7, .2], holdF: pull > 0 ? 'scanner' : null, armF: { h: [lerp(16, 150, pull), lerp(300, 120, pull)], bend: 20 }, scanA: 0 }) });
  } else if (id === 'scanG') {
    cam(800, 570, lerp(2.5, 2.8, ss(u / 2.5)), 0, t);
    room(t, { mon: readout(t) });
  } else if (id === 'cuG') {
    cam(770, 990, 2.1, 0, t);
    room(t, { gusP: G(t, { nerv: 1.2, eyeS: 1.18, pupil: 3, brow: 1.5, sweat: t * 1.5, look: [0, 0], lid: 0 }) });
  } else if (id === 'self') {
    const wp = ss(clamp(u / .25));
    cam(lerp(770, 380, wp), lerp(900, 720, wp), lerp(2.2, 1.5, wp), 0, t);
    const turn = eio(seg(t, 15.4, 15.9));
    room(t, {
      noddP: N(t, { holdF: 'scanner', armF: { h: [lerp(150, 70, turn), lerp(120, -60, turn)], bend: 30 }, scanA: lerp(0, Math.PI * .85, turn), scanOn: t > 15.9 ? 1 : 0, look: [lerp(.7, -.2, turn), lerp(.2, -.5, turn)], lid: .55 }),
      gusP: G(t, { nerv: .8 }),
    });
    if (wp < 1) { g.setTransform(1, 0, 0, 1, 0, 0); g.globalAlpha = .5 * (1 - wp); g.fillStyle = '#fff'; for (let i = 0; i < 18; i++) g.fillRect(0, hash(i) * H, W, 6); g.globalAlpha = 1; }
  } else if (id === 'scanN') {
    const sh = t >= 18.4 ? 26 : 0;
    cam(800, 570, lerp(2.5, 2.9, ss(u / 2.5)), sh, t);
    room(t, { mon: readout(t) });
  } else if (id === 'boom') {
    const op = popOpen(t - 18.75);
    cam(540, 980, lerp(1.4, 1.04, eo(clamp(u / .6))), 30 * Math.exp(-u * 3), t);
    room(t, {
      portalOpen: op, wash_: .1 * clamp(op),
      noddP: N(t, { holdF: 'scanner', crack: 1, smoke: 1, armF: { h: [80, 60], bend: 20 }, scanA: .4, lid: .55, look: [.6, 0], jit: 0 }),
      gusP: G(t, { nerv: 1.4, eyeS: 1.2, pupil: 3, brow: 1.6, sweat: t * 1.5, mouth: { o: .7, sm: -.8 }, look: [-.8, -.2], lid: 0 }),
    });
  } else if (id === 'pause') {
    cam(540, 980, lerp(1.04, 1.1, ss(u / 2.75)), 0, t);
    const sip = seg(t, 22.0, 22.9) > 0 && t < 23.2;
    const P = N(t, { holdF: 'tube', armF: { h: [60, -150], bend: 30 }, look: [.7, 0], lid: .6, mouth: { o: sip ? .12 : 0, sm: -.2 } });
    room(t, { portalOpen: 1, wash_: .1, noddP: P, tube: noddMouth(P), iv: { level: .62 - .05 * clamp(seg(t, 22.0, 23.0)) },
      gusP: G(t, { nerv: .9, eyeS: 1.15, pupil: 3, brow: 1.4, look: [-.8, 0], lid: 0, mouth: { o: 0, sm: -.9 } }) });
  } else if (id === 'punch') {
    cam(400, 780, 1.6, 0, t);
    room(t, { portalOpen: 1, wash_: .1, noddP: N(t, { look: [.6, .1], lid: t > 26.6 ? .7 : .55, brow: t > 25.0 ? .4 : 0, armF: { h: [40, 280], bend: 16 } }) });
  } else if (id === 'fall') {
    cam(540, 1000, lerp(1.06, 1.12, ss(u / 3)), 0, t);
    const ant = ss(seg(t, 27.6, 27.8)), fallU = ei(clamp(seg(t, 27.8, 28.7)));
    const close = 1 - ei(clamp(seg(t, 29.2, 29.5)));
    const P = N(t, { closed: t > 27.7, lean: .14 - .06 * ant, rot: -1.3 * fallU, s: NS * (1 - .85 * fallU), x: lerp(NX, PORTAL.x, fallU), y: lerp(FLOOR, PORTAL.y + 250, fallU), mouth: { o: .2, sm: 0 } });
    room(t, { portalOpen: close, wash_: .1 * close, noddP: fallU < .98 ? P : null,
      gusP: G(t, { nerv: t < 29.5 ? .7 : .1, eyeS: 1.15, pupil: 3, brow: t < 29.5 ? 1.3 : .2, look: t > 29.7 ? [0, 0] : [-.8, -.1], lid: t > 29.7 ? .45 : 0, mouth: { o: 0, sm: -.4 } }) });
  } else if (id === 'end') {
    cam(560, 1000, 1.08, 0, t);
    const lie = eio(clamp(seg(t, 30.4, 30.9)));
    room(t, { gusP: G(t, { x: lerp(GX, 650, lie), rot: 1.4 * lie, closed: t > 30.7, nerv: 0, brow: .2, sq: landSq(t, 30.9), case: 'lap', mouth: { o: .15 + .1 * Math.sin(t * 2.4), sm: 0 } }) });
    const zt = (t * .5) % 1;
    text('z', 940 + zt * 60, 1000 - zt * 160, { font: `800 ${44 + zt * 30}px "Baloo 2"`, fill: '#2a2370', outlineW: 0 });
  }
  title(t);
  subs(t);
}

function events() {
  return [
    { t: .4, type: 'door' }, { t: 2.0, type: 'boing' }, { t: 4.0, type: 'blip' }, { t: 10.4, type: 'clickbeep' }, { t: 11.0, type: 'beam' },
    { t: 12.5, type: 'sting' }, { t: 15.0, type: 'whoosh' }, { t: 15.9, type: 'beam' },
    ...[16.25, 17.1, 17.6, 17.9, 18.1, 18.25].map(t => ({ t, type: 'beep' })), { t: 18.4, type: 'error' },
    { t: 18.75, type: 'portalOpen' }, { t: 21.25, type: 'musicCut' }, { t: 22.4, type: 'slurp' },
    { t: 27.8, type: 'slide' }, { t: 28.2, type: 'snore' }, { t: 29.5, type: 'fwump' }, { t: 29.9, type: 'blip' }, { t: 30.9, type: 'boing' }, { t: 31.6, type: 'snore' }, { t: 33.4, type: 'snore' },
  ];
}

await document.fonts.load('800 40px "Baloo 2"'); await document.fonts.load('800 60px "Baloo Bhaijaan 2"', 'دكتور'); await document.fonts.load('400 40px VT323'); await document.fonts.load('400 40px "Lilita One"');
window.render = render; window.DUR = DUR; window.EV = events(); window.SUBS = SUBS;
window.TEXTS = t => {
  const out = [];
  if (t >= 30.6) out.push({ id: 'title', text: 'SICK NOTE', x0: 110, y0: 210, x1: 970, y1: 450 });
  return out;
};
render(0); window.READY = true;
