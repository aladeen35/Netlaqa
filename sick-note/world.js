// world.js — the space clinic, the exam bed, the wall terminal, the magenta portal and the sleep dimension behind it
// Stage: 1080 wide, floor at y = FLOOR. Backgrounds are drawn wider than the stage for camera moves.
import { clamp, lerp, hash, vnoise, TAU } from '/core/lib.js';
import { INK, g, push, pop, translate, rotate, scale, shape, fillOnly, stroke, ell, arc, spline, rr, rect, quad, dot, text, bands } from './toon.js';
import { eye, mouth } from './chars.js';

export const FLOOR = 1450, BED = { x0: 540, x1: 1010, top: 1170 };
export const MON = { x: 800, y: 560, w: 330, h: 250 };
export const PORTAL = { x: 330, y: 780, r: 390 };
const X0 = -900, X1 = 2000;

export const CL = { wall: '#9fd8b8', wall2: '#8ccaa8', wallS: '#79b896', trim: '#2e8c86', floor: '#d8c7a0', floorS: '#c4b088', paper: '#f7f3e6' };

export function clinic(t, { flicker = 0 } = {}) {
  bands([CL.wall, CL.wall, CL.wall2], -400, FLOOR - 120, X0, X1);
  fillOnly(rect(X0, FLOOR - 120, X1 - X0, 120), CL.wallS, { boil: .2 });
  shape(rect(X0, FLOOR - 140, X1 - X0, 26), { fill: CL.trim, lw: 6 });                    // dado rail
  shape(rect(X0, FLOOR, X1 - X0, 900), { fill: CL.floor, lw: 7 });                         // floor
  for (let i = -6; i < 14; i++) stroke([[i * 160, FLOOR], [i * 160 - 260 + 540 * .3, FLOOR + 500]], 4, { line: CL.floorS });
  stroke([[X0, FLOOR + 140], [X1, FLOOR + 140]], 4, { line: CL.floorS });
  // porthole to space
  push(); translate(170, 330);
  shape(ell(0, 0, 130, 130, 48), { fill: '#16123a', lw: 9, shade: () => {
    for (let i = 0; i < 26; i++) dot(-120 + hash(i * 2.7) * 240, -120 + hash(i * 6.1) * 240, 2 + hash(i) * 3, '#fff8d6');
    shape(ell(46 + Math.sin(t * .2) * 4, 40, 44, 44, 30), { fill: '#f0a35a', lw: 6, shade: () => fillOnly(ell(64, 54, 30, 34, 20), '#c9773a', { boil: .3 }) });
    stroke(arc(46, 40, 76, 16, Math.PI * .05, Math.PI * .95, 18), 5, { line: '#ffd9a8' });
  } });
  shape(ell(0, 0, 150, 150, 48), { line: '#7d8798', lw: 22, stroke: true });
  shape(ell(0, 0, 150, 150, 48), { lw: 6 });
  for (let k = 0; k < 8; k++) dot(Math.cos(k / 8 * TAU) * 150, Math.sin(k / 8 * TAU) * 150, 6, INK);
  pop();
  // wall clock (it's 3:47, nobody has slept)
  push(); translate(500, 300);
  shape(ell(0, 0, 62, 62, 36), { fill: '#fdfaf0', lw: 7 });
  stroke([[0, 0], [Math.sin(TAU * 3.78 / 12) * 32, -Math.cos(TAU * 3.78 / 12) * 32]], 7);
  stroke([[0, 0], [Math.sin(TAU * (47 + t / 60) / 60) * 48, -Math.cos(TAU * (47 + t / 60) / 60) * 48]], 5);
  dot(0, 0, 6, INK);
  pop();
  // poster (background gag)
  push(); translate(360, 640); rotate(-.04);
  shape(rr(-90, -110, 180, 220, 6), { fill: '#fff3c4', lw: 6 });
  text('SLEEP', 0, -60, { font: '800 40px "Baloo 2"', fill: '#c9641f' });
  text('IS FOR', 0, -18, { font: '800 30px "Baloo 2"', fill: INK });
  text('THE WEAK', 0, 20, { font: '800 30px "Baloo 2"', fill: INK });
  stroke(spline([[-40, 66], [-20, 52], [0, 66], [20, 52], [40, 66]], false), 5, { line: '#c9641f' });
  pop();
  // fluorescent tube
  shape(rr(170, -10, 740, 40, 10), { fill: '#d6dbe4', lw: 6 });
  shape(rr(190, 30, 700, 22, 10), { fill: flicker ? '#f6fff8' : '#e6f5ec', lw: 5 });
  // door (right)
  shape(rr(1080 - 30, 760, 300, FLOOR - 760, 6), { fill: '#e7dcc0', lw: 7, shade: () => fillOnly(rect(1080 - 30, 760, 40, 700), '#cbbd99', { boil: .3 }) });
}

export function bed(t, { paperCrumple = 0 } = {}) {
  const { x0, x1, top } = BED;
  for (const lx of [x0 + 40, x1 - 40]) shape(rr(lx - 14, top + 60, 28, FLOOR - top - 60, 6), { fill: '#7d8798', lw: 6 });
  shape(rr(x0 + 10, FLOOR - 40, x1 - x0 - 20, 22, 8), { fill: '#7d8798', lw: 6 });
  shape(rr(x0, top + 20, x1 - x0, 60, 14), { fill: CL.trim, lw: 7, shade: () => fillOnly(rect(x0, top + 60, x1 - x0, 30), '#22706b', { boil: .3 }) });
  // paper sheet roll
  shape(rr(x0 + 6, top, x1 - x0 - 12, 30, 10), { fill: CL.paper, lw: 6 });
  shape(ell(x0 - 6, top + 34, 26, 34, 18), { fill: CL.paper, lw: 6, shade: () => fillOnly(ell(x0 - 6, top + 34, 9, 12, 10), '#d8d0b8', { boil: .2 }) });
  // pillow
  shape(spline([[x1 - 150, top + 4], [x1 - 140, top - 34], [x1 - 20, top - 40], [x1 - 6, top + 2]]), { fill: '#ffffff', lw: 6 });
}

// The wall terminal on an arm. readout(lines, bar) draws its text.
export function monitor(t, { lines = [], bar = -1, barCol = '#ffb020', err = 0, crack = 0, shake = 0 } = {}) {
  const { x, y, w, h } = MON;
  const sx = shake ? (hash(Math.floor(t * 24) * 3.1) - .5) * shake : 0;
  stroke(spline([[x + w / 2 + 40, y - h / 2 - 220], [x + w / 2 + 10, y - h / 2 - 120], [x + 20, y - h / 2 - 40]], false), 14);
  push(); translate(x + sx, y);
  shape(rr(-w / 2 - 26, -h / 2 - 26, w + 52, h + 64, 26), { fill: '#d6d1c2', lw: 7, shade: () => fillOnly(rect(w / 2 - 20, -h, 80, h * 2), '#b6b0a0', { boil: .3 }) });
  shape(rr(-w / 2, -h / 2, w, h, 20), {
    fill: err ? (Math.floor(t * 12) % 2 ? '#3a0f18' : '#22101a') : '#14231c', lw: 7, shade: () => {
      for (let i = 0; i < 14; i++) fillOnly(rect(-w / 2, -h / 2 + i * (h / 14), w, 3), 'rgba(0,0,0,.25)', { boil: 0 });
      lines.forEach((L, i) => text(L.s, -w / 2 + 22, -h / 2 + 34 + i * 40, { font: `400 ${L.size || 38}px VT323`, fill: L.col || '#ffb020', align: 'left' }));
      if (bar >= 0) {
        const bw = w - 44, by = h / 2 - 66;
        shape(rect(-w / 2 + 22, by, bw, 30), { fill: '#0c1410', lw: 4, line: barCol });
        fillOnly(rect(-w / 2 + 26, by + 4, (bw - 8) * clamp(bar), 22), barCol, { boil: .2 });
      }
      if (crack) { stroke([[-40, -h / 2], [-10, -30], [-60, 20], [-30, h / 2]], 4, { line: '#e6e6e6' }); stroke([[-10, -30], [60, -10], [120, -60]], 4, { line: '#e6e6e6' }); }
    }
  });
  dot(w / 2 - 6, h / 2 + 20, 8, err ? '#ff3a3a' : '#5ae07a');
  pop();
}

// —— the portal: the only thing that glows (magenta) ——
export function portal(cx, cy, r, t, { open = 1, sx = .78, inside = null } = {}) {
  if (open <= .001) return;
  const R = r * open;
  push(); translate(cx, cy); scale(sx, 1);
  fillOnly(ell(0, 0, R * 1.55, R * 1.42, 48), 'rgba(255,63,210,.14)', { boil: .6 });
  fillOnly(ell(0, 0, R * 1.26, R * 1.2, 48), 'rgba(255,63,210,.18)', { boil: .6 });
  const rim = []; const N = 22;
  for (let i = 0; i < N; i++) { const a = i / N * TAU, k = 1 + .08 * (vnoise(i * 1.7 + t * 3) - .5) * 2 + .05 * Math.sin(a * 5 + t * 6); rim.push([Math.cos(a) * R * k, Math.sin(a) * R * k]); }
  shape(spline(rim), {
    fill: '#ff3fd2', lw: 8, shade: () => {
      if (inside && open > .25) {
        // the sleep dimension seen through the hole: drawn in the portal's own frame
        fillOnly(ell(0, 0, R * .9, R * .9, 40), '#2a2370', { boil: .3 });
        push(); scale(1 / sx, 1); inside(R * .9 * sx, R * .9); pop();
        // a thin swirl over it, so it still reads as a portal
        for (let k = 0; k < 4; k++) {
          const pts = [], pts2 = [];
          for (let j = 0; j <= 18; j++) { const u = j / 18, rr_ = R * (1 - u * .35) * .9, a = k / 4 * TAU + u * 1.4 + t * 1.6; pts.push([Math.cos(a) * rr_, Math.sin(a) * rr_]); const a2 = a + .3; pts2.push([Math.cos(a2) * rr_, Math.sin(a2) * rr_]); }
          fillOnly([...pts, ...pts2.reverse()], 'rgba(255,140,232,.45)', { boil: .3 });
        }
      } else {
        fillOnly(ell(0, 0, R * .9, R * .9, 40), '#ff7ae0', { boil: .3 });
        for (let k = 0; k < 5; k++) {
          const pts = [], pts2 = [];
          for (let j = 0; j <= 22; j++) { const u = j / 22, rr_ = R * (1 - u) * .95, a = k / 5 * TAU + u * 3.6 + t * 2.6; pts.push([Math.cos(a) * rr_, Math.sin(a) * rr_]); const a2 = a + .55 * (1 - u * .7); pts2.push([Math.cos(a2) * rr_, Math.sin(a2) * rr_]); }
          fillOnly([...pts, ...pts2.reverse()], k % 2 ? '#ffb3ef' : '#d61fae', { boil: .4 });
        }
        fillOnly(ell(0, 0, R * .3, R * .3, 24), '#ffd6f4', { boil: .5 });
        fillOnly(ell(0, 0, R * .14, R * .14, 16), '#ffffff', { boil: .5 });
      }
    }
  });
  for (let i = 0; i < 12; i++) {
    const a = hash(i) * TAU + t * (1.5 + hash(i + 4) * 2), d = R * (1.05 + .25 * ((t * .8 + hash(i + 9)) % 1));
    dot(Math.cos(a) * d, Math.sin(a) * d, 5 + hash(i + 2) * 4, i % 3 ? '#ff9be8' : '#ffffff');
  }
  if (open > .6) for (let i = 0; i < 3; i++) {
    const u = (t * .9 + i / 3) % 1, x = (-.4 + i * .4) * R, y0 = R * .92;
    shape(spline([[x - 10, y0], [x + 10, y0], [x + 7, y0 + 20 + u * 40], [x, y0 + 32 + u * 50], [x - 7, y0 + 20 + u * 40]]), { fill: '#ff3fd2', lw: 6 });
  }
  pop();
}

// —— the sleep dimension (indigo, lavender, gold): floating pillows + a snoring pillow creature ——
export function sleepWorld(rx, ry, t, { snore = 0 } = {}) {
  bands(['#2a2370', '#352b86', '#43369c'], -ry, ry, -rx * 1.2, rx * 1.2);
  for (let i = 0; i < 22; i++) {
    const x = (-1 + hash(i * 3.3) * 2) * rx, y = (-1 + hash(i * 8.1) * 2) * ry, s = 4 + hash(i) * 6, tw = .6 + .4 * Math.sin(t * 3 + i);
    fillOnly([[x, y - s * 2 * tw], [x + s * .5, y - s * .5], [x + s * 2 * tw, y], [x + s * .5, y + s * .5], [x, y + s * 2 * tw], [x - s * .5, y + s * .5], [x - s * 2 * tw, y], [x - s * .5, y - s * .5]], '#f5c84a', { boil: .3 });
  }
  for (let i = 0; i < 5; i++) {
    const x = (-.75 + i * .38) * rx + Math.sin(t * .7 + i) * 10, y = (-.55 + hash(i * 4.4) * 1.0) * ry + Math.sin(t * 1.1 + i * 2) * 14;
    push(); translate(x, y); rotate(Math.sin(t * .5 + i) * .3);
    shape(spline([[-56, -30], [0, -40], [56, -30], [62, 30], [0, 40], [-62, 30]]), { fill: '#8a7ae0', lw: 6, shade: () => fillOnly(ell(20, 14, 40, 22, 16), '#6f5fc4', { boil: .3 }) });
    pop();
  }
  // pillow creature, asleep, snoring
  push(); translate(-rx * .32, -ry * .42); scale(.8); const br = 1 + .05 * Math.sin(t * 2.2) + snore * .06;
  scale(br, 1 / br);
  shape(spline([[-120, -60], [0, -80], [120, -60], [130, 50], [0, 70], [-130, 50]]), { fill: '#e9e2ff', lw: 7, shade: () => fillOnly(ell(50, 30, 80, 40, 20), '#c6bbef', { boil: .3 }) });
  for (const ex of [-40, 40]) stroke(arc(ex, -6, 18, 10, Math.PI * .1, Math.PI * .9, 10), 6);
  shape(ell(0, 30, 12 + snore * 6, 8 + snore * 10, 14), { fill: '#4a1a2a', lw: 5 });
  shape(spline([[-70, 0], [-56, -6], [-50, 6]]), { fill: '#ff9bcb', lw: 0, line: null });
  pop();
  const zt = (t * .6) % 1;
  text('z', -rx * .1 + zt * 40, -ry * .62 - zt * 80, { font: `800 ${30 + zt * 20}px "Baloo 2"`, fill: '#f5c84a', outlineW: 6 });
}

export function wash(col, a) { g.setTransform(1, 0, 0, 1, 0, 0); g.globalAlpha = a; g.fillStyle = col; g.fillRect(0, 0, 1080, 1920); g.globalAlpha = 1; }
