// chars.js — the cast of SICK NOTE: Dr. Nodd (deadpan, exhausted), Gus (nervous office worker in a hospital gown + tie)
// Local coordinates: origin at the feet, y down. face = 1 looks right, -1 looks left.
import { clamp, lerp, hash, TAU } from '/core/lib.js';
import { INK, push, pop, translate, rotate, scale, shape, fillOnly, stroke, ell, arc, spline, rr, rect, noodle, quad, dot, text } from './toon.js';

export const PAL = {
  white: '#ffffff', mouthIn: '#4a1a2a', tongue: '#e8637a',
  // Nodd
  nSkin: '#dcd3a6', nSkinS: '#b9ae80', bag: '#b49ccf', bagS: '#8f77ad', scrub: '#3aa59a', scrubS: '#2a7a72', under: '#f3efe2',
  cap: '#f08a3c', capS: '#c9641f', clog: '#ffd23f', clogS: '#d9a91f', dish: '#aab3c2', dishS: '#7d8798', badge: '#fdfaf0',
  // Gus
  gSkin: '#c98b5e', gSkinS: '#a46a42', gown: '#a9d3f0', gownS: '#7fb0d6', gownDot: '#6f9fc9', tie: '#e0443a', tieS: '#b32c24',
  hair: '#3a2a22', sock: '#3b3550', shoe: '#2c2430', case_: '#9a6431', caseS: '#764a20',
  // props
  chrome: '#c9ccd6', chromeS: '#959aa8', coffee: '#6b3e26', bagIV: '#e9f2ef',
};

// —— face parts ——
export function eye(cx, cy, rx, ry, { lid = 0, look = [0, 0], pupil = 4.5, skin = PAL.nSkin, closed = false, lw = 6, jitter = 0 } = {}) {
  if (closed) { stroke(arc(cx, cy + ry * .1, rx * .8, ry * .4, Math.PI * .12, Math.PI * .88, 14), lw); return; }
  shape(ell(cx, cy, rx, ry, 36), {
    fill: PAL.white, lw, shade: () => {
      dot(cx + look[0] * rx * .55 + jitter, cy + look[1] * ry * .5, pupil);
      if (lid > 0) {
        const yl = cy - ry + lid * 2 * ry;
        fillOnly([[cx - rx * 1.3, cy - ry * 1.4], [cx + rx * 1.3, cy - ry * 1.4], [cx + rx * 1.3, yl], [cx - rx * 1.3, yl + ry * .1]], skin, { boil: .5 });
        stroke([[cx - rx * 1.2, yl + ry * .1], [cx + rx * 1.2, yl]], lw);
      }
    }
  });
}
export function mouth(cx, cy, mw, { o = 0, w = 1, sm = 0, skew = 0, lw = 6, teeth = true } = {}) {
  const hw = mw * w / 2, k = mw * .22, lc = [cx - hw, cy - sm * k + skew * k], rc = [cx + hw, cy - sm * k - skew * k];
  if (o < .07) { stroke(quad(lc, [cx, cy + sm * k * 1.2], rc, 12), lw); return; }
  const h = o * mw * .62;
  const P = [...quad(lc, [cx, cy - h * .25 + sm * k * .4], rc, 12), ...quad(rc, [cx, cy + h + sm * k * .6], lc, 14)];
  shape(P, {
    fill: PAL.mouthIn, lw, shade: () => {
      if (teeth && o > .22) fillOnly(rect(cx - hw * 1.2, cy - h, hw * 2.4, h * .3 + 8), PAL.white, { boil: .3 });
      fillOnly(ell(cx + hw * .15, cy + h * .95, hw * .6, h * .45, 20), PAL.tongue, { boil: .3 });
    }
  });
}
export function hand(x, y, ang, r = 21, col = PAL.nSkin, { fist = false, lw = 6 } = {}) {
  push(); translate(x, y); rotate(ang);
  const pts = fist ? spline([[-r * .6, -r * .8], [r * .7, -r * .9], [r * 1.1, -r * .1], [r * .8, r * .8], [-r * .5, r * .9], [-r * .9, 0]])
    : spline([[-r * .5, -r * .85], [r * .5, -r * 1.05], [r * 1.35, -r * .75], [r * 1.05, -r * .3], [r * 1.5, -r * .1], [r * 1.1, r * .3], [r * 1.35, r * .7], [r * .6, r * .95], [-r * .6, r * .8], [-r * .95, 0]]);
  shape(pts, { fill: col, lw });
  pop();
}
export const sweat = (x, y, s = 1) => shape(spline([[x, y - 16 * s], [x + 9 * s, y + 4 * s], [x, y + 12 * s], [x - 9 * s, y + 4 * s]]), { fill: '#bfe9ff', lw: 5 });

// —— props ——
// The fatigue scanner: a chrome toaster with an antenna and an emitter dish. Origin = handle grip.
export function scanner(x, y, a = 0, { on = 0, crack = 0, smoke = 0, t = 0 } = {}) {
  push(); translate(x, y); rotate(a);
  stroke(spline([[-20, -60], [-26, -96], [-14, -120], [-24, -150]], false), 5);
  dot(-24, -150, 8, on ? '#ffde59' : '#e8392b');
  shape(rr(-70, -66, 120, 84, 18), {
    fill: PAL.chrome, lw: 7, shade: () => {
      fillOnly(rect(10, -70, 50, 100), PAL.chromeS, { boil: .3 });
      fillOnly(rect(-60, -58, 16, 20), '#ffffff', { boil: .2 });
    }
  });
  stroke([[-52, -66], [-8, -66]], 9); stroke([[-46, -66], [-14, -66]], 4, { line: '#5a5f6b' });   // bread slot
  shape(rr(-54, -30, 50, 32, 6), { fill: '#20302a', lw: 5, shade: () => { if (on) fillOnly(rect(-50, -16, 42 * clamp(on), 8), '#ffb020', { boil: 0 }); } });
  shape(rr(52, -44, 22, 40, 6), { fill: PAL.chromeS, lw: 5 });                       // emitter neck
  shape(ell(82, -24, 16, 34, 20), { fill: '#e6e9f0', lw: 6, shade: () => fillOnly(ell(86, -24, 8, 20, 14), '#9aa2b2', { boil: .3 }) });
  if (crack) { stroke([[-40, -60], [-24, -40], [-34, -22], [-16, 0]], 4); stroke([[20, -66], [6, -36], [22, -12]], 4); }
  if (smoke) for (let k = 0; k < 3; k++) { const u = (t * .9 + k / 3) % 1; shape(ell(-30 + k * 30 + u * 20, -80 - u * 120, 18 + u * 22, 14 + u * 18, 16), { fill: `rgba(120,120,130,${.55 * (1 - u) * smoke})`, line: `rgba(34,23,42,${.6 * (1 - u) * smoke})`, lw: 4 }); }
  pop();
}
// The coffee IV pole: wheels at (x, y), bag on top. level 0..1. Returns the bag's outlet point (world).
export function ivPole(x, y, t, { level = .7, h = 930, lean = 0 } = {}) {
  push(); translate(x, y); rotate(lean);
  for (const k of [-1, 0, 1]) { stroke([[0, -30], [k * 70, 0]], 7); shape(ell(k * 70, 4, 14, 14, 14), { fill: '#5a5f6b', lw: 5 }); }
  shape(rr(-9, -h, 18, h - 20, 6), { fill: PAL.chrome, lw: 6 });
  stroke(spline([[0, -h], [-40, -h - 20], [-70, -h + 10]], false), 6);
  stroke(spline([[0, -h], [40, -h - 20], [70, -h + 10]], false), 6);
  // bag of coffee
  push(); translate(-70, -h + 12);
  const bag = spline([[-60, 10], [60, 10], [70, 120], [40, 190], [-40, 190], [-70, 120]]);
  shape(bag, {
    fill: PAL.bagIV, lw: 7, shade: () => {
      const ly = lerp(186, 30, level) + Math.sin(t * 2) * 3;
      fillOnly([[-90, ly], [90, ly - 4], [90, 220], [-90, 220]], PAL.coffee, { boil: .4 });
      fillOnly(ell(-34, 70, 9, 34, 10), 'rgba(255,255,255,.7)', { boil: .2 });
    }
  });
  shape(rr(-34, 92, 68, 40, 6), { fill: '#fff3c4', lw: 5 });
  text('JAVA', 0, 113, { font: '800 26px "Baloo 2"', fill: INK });
  shape(rr(-10, 186, 20, 28, 5), { fill: PAL.chromeS, lw: 5 });
  pop();
  pop();
  return [x - 70 + Math.sin(lean) * 0, y - h + 12 + 214];
}
export function briefcase(x, y, a = 0, s = 1) {
  push(); translate(x, y); rotate(a); scale(s);
  stroke(spline([[-26, -6], [-24, -30], [24, -30], [26, -6]], false), 7);
  shape(rr(-70, 0, 140, 96, 10), { fill: PAL.case_, lw: 7, shade: () => fillOnly(rect(20, -4, 60, 110), PAL.caseS, { boil: .3 }) });
  shape(rr(-10, 26, 20, 16, 3), { fill: PAL.clog, lw: 4 });
  stroke([[-70, 40], [70, 40]], 4);
  pop();
}

// —————————————————— Dr. Nodd ——————————————————
// P: {x,y,s,face,lean,sq, lid,look,brow,mouth:{o,w,sm},blink,closed,headTilt, armF:{h,bend}, armB, holdF:'scanner'|null, scanA, scanOn, sweat}
export function nodd(P) {
  const f = P.face ?? 1;
  push(); translate(P.x, P.y); rotate(P.rot ?? 0); scale((P.s ?? 1) * f, (P.s ?? 1) * (P.sq ?? 1));
  // legs + clogs
  for (const sx of [-1, 1]) {
    const hip = [sx * 30, -450], ank = [sx * 36, -36];
    shape(noodle(hip, ank, sx * -8, 48, 40), { fill: PAL.scrub, lw: 7, shade: () => fillOnly(rect(sx > 0 ? 6 : -200, -460, 200, 440), PAL.scrubS, { boil: .3 }) });
    shape(spline([[ank[0] - 30, 0], [ank[0] - 30, -30], [ank[0] + 10, -42], [ank[0] + 54, -26], [ank[0] + 56, 0]]), { fill: PAL.clog, lw: 7, shade: () => { fillOnly(rect(ank[0] - 40, -10, 120, 20), PAL.clogS, { boil: .3 }); for (const hx of [10, 30]) dot(ank[0] + hx, -24, 4, INK); } });
  }
  push(); translate(0, -450); rotate(P.lean ?? .1); translate(0, 450);
  const shB = [-64, -770], shF = [58, -768];
  const drawArm = (sh, arm, front) => {
    const hp = [sh[0] + arm.h[0], sh[1] + arm.h[1]];
    const el = [sh[0] + arm.h[0] * .32, sh[1] + arm.h[1] * .32];
    shape(noodle(sh, hp, arm.bend ?? 0, 30, 26), { fill: PAL.nSkin, lw: 7 });
    shape(noodle(sh, el, 0, 52, 46), { fill: PAL.scrub, lw: 7 });
    const ang = Math.atan2(hp[1] - sh[1], hp[0] - sh[0]);
    if (front && P.holdF === 'scanner') { scanner(hp[0], hp[1] - 6, P.scanA ?? 0, { on: P.scanOn || 0, crack: P.crack, smoke: P.smoke, t: P.t || 0 }); hand(hp[0], hp[1], ang, 22, PAL.nSkin, { fist: true }); return; }
    if (front && P.holdF === 'tube') { hand(hp[0], hp[1], ang, 22, PAL.nSkin, { fist: true }); return; }
    hand(hp[0], hp[1], ang, 22, PAL.nSkin, { fist: !!arm.fist });
  };
  drawArm(shB, P.armB || { h: [-14, 300], bend: -16 }, false);
  // scrub top
  const top = spline([[-40, -800], [-88, -770], [-98, -620], [-92, -470], [0, -440], [92, -468], [96, -620], [86, -770], [40, -800]]);
  shape(top, {
    fill: PAL.scrub, lw: 7, shade: () => {
      fillOnly(spline([[30, -820], [110, -780], [120, -440], [40, -430], [60, -620]]), PAL.scrubS, { boil: .4 });
      fillOnly([[-26, -800], [30, -800], [4, -720]], PAL.under, { boil: .3 });
    }
  });
  stroke([[-28, -800], [4, -716], [32, -800]], 6);
  stroke(rr(-70, -640, 50, 44, 6), 5);                                   // chest pocket
  shape(rr(-64, -660, 14, 40, 4), { fill: '#e8392b', lw: 4 }); shape(rr(-46, -664, 14, 44, 4), { fill: '#3b6fd6', lw: 4 });
  shape(rr(26, -680, 60, 38, 5), { fill: PAL.badge, lw: 5 });             // badge
  text('NODD', 56, -660, { font: '800 20px "Baloo 2"', fill: INK });
  // neck (long, stooped forward)
  shape(noodle([6, -790], [44, -870], -10, 40, 38), { fill: PAL.nSkin, lw: 6 });
  push(); translate(70, -960); rotate(P.headTilt ?? .16);
  noddHead(P);
  pop();
  drawArm(shF, P.armF || { h: [16, 300], bend: 16 }, true);
  pop();
  if (P.sweat != null) sweat(180, -1080 + (P.sweat % 1) * 30, 1.2);
  pop();
}
function noddHead(P) {
  shape(ell(-82, 6, 18, 28, 18), { fill: PAL.nSkin, lw: 6, shade: () => fillOnly(ell(-78, 8, 8, 14, 12), PAL.nSkinS, { boil: .3 }) });
  const HD = spline([[-20, -112], [50, -110], [88, -70], [96, 0], [90, 80], [60, 130], [10, 140], [-40, 120], [-80, 60], [-90, -20], [-66, -86]]);
  shape(HD, {
    fill: PAL.nSkin, lw: 7, shade: () => {
      fillOnly(spline([[-100, -40], [-70, -120], [-110, -130]]), PAL.nSkinS, { boil: .3 });
      fillOnly(spline([[-50, 80], [30, 96], [100, 70], [100, 160], [-60, 160]]), PAL.nSkinS, { boil: .3 });
      for (let i = 0; i < 24; i++) dot(-34 + hash(i * 3.1) * 120, 92 + hash(i * 7.7) * 40, 1.8, '#8f8660');
    }
  });
  // eye bags: three layers of purple
  for (const [ex, rx, k] of [[4, 34, 1], [60, 27, .85]]) {
    shape(spline([[ex - rx, 22], [ex, 52 * k + 6], [ex + rx, 22], [ex, 34]]), { fill: PAL.bag, lw: 5 });
    stroke(arc(ex, 52, rx * .8, 10, Math.PI * .15, Math.PI * .85, 10), 4, { line: PAL.bagS });
    stroke(arc(ex + 2, 64, rx * .6, 8, Math.PI * .2, Math.PI * .8, 8), 3.5, { line: PAL.bagS });
  }
  const lid = P.blink ? 1 : clamp(P.lid ?? .55, 0, 1), look = P.look || [0, 0];
  eye(4, -6, 34, 36, { lid: P.closed ? 0 : lid, look, closed: P.closed, pupil: 4.5, jitter: P.jit || 0 });
  eye(60, -8, 27, 31, { lid: P.closed ? 0 : lid, look, closed: P.closed, pupil: 4, jitter: P.jit || 0 });
  // brows: two droopy slabs
  const br = P.brow ?? 0;
  shape(spline([[-30, -54 - br * 10], [6, -64 - br * 14], [34, -54 - br * 6], [30, -44 - br * 6], [-28, -44 - br * 10]]), { fill: '#6a5a3a', lw: 5 });
  shape(spline([[44, -56 - br * 6], [74, -64 - br * 12], [96, -54 - br * 10], [94, -46 - br * 10], [44, -46 - br * 6]]), { fill: '#6a5a3a', lw: 5 });
  // long droopy nose
  shape(spline([[30, -14], [44, 30], [76, 58], [70, 80], [40, 74], [28, 50]]), { fill: PAL.nSkin, lw: 6, shade: () => fillOnly(ell(66, 72, 14, 8, 12), PAL.nSkinS, { boil: .3 }) });
  const m = P.mouth || {};
  mouth(40, 108, 70, { o: m.o || 0, w: m.w ?? 1, sm: m.sm ?? -.3, skew: m.skew ?? .15, lw: 6 });
  // head mirror (a cracked mini satellite dish) on a strap
  fillOnly([[-92, -66], [96, -70], [96, -56], [-92, -52]], '#4a4f5a', { boil: .3 });
  push(); translate(30, -86); rotate(-.3);
  shape(ell(0, 0, 34, 28, 24), { fill: PAL.dish, lw: 6, shade: () => fillOnly(ell(6, 4, 20, 16, 16), PAL.dishS, { boil: .3 }) });
  stroke([[-16, -14], [-2, 2], [-12, 16]], 3.5);
  dot(0, 0, 5, INK);
  pop();
  // the floppy surgical cap
  shape(spline([[-96, -70], [-104, -140], [-50, -196], [40, -200], [110, -150], [128, -80], [150, -40], [120, -30], [96, -70], [0, -84]]), {
    fill: PAL.cap, lw: 7, shade: () => {
      fillOnly(spline([[40, -220], [140, -150], [160, -30], [110, -40], [90, -120]]), PAL.capS, { boil: .3 });
      for (let i = 0; i < 9; i++) dot(-70 + hash(i * 5.3) * 160, -170 + hash(i * 2.1) * 80, 5, '#ffd9a8');
    }
  });
  stroke(spline([[-96, -74], [0, -88], [96, -74]], false), 6);
}

// —————————————————— Gus ——————————————————
// P: {x,y,s,face,rot,sit, nerv,t, lid,look,brow,mouth,blink,closed, armF, armB, case:'hand'|'lap'|null, sweat, eyeS}
export function gus(P) {
  const f = P.face ?? 1, ner = P.nerv ?? 0;
  const jit = ner ? (hash(Math.floor((P.t || 0) * 12) * 3.3) - .5) * 8 * ner : 0;
  push(); translate(P.x + jit, P.y); if (P.sit) { translate(0, -150); rotate(P.rot ?? 0); translate(0, 150); } else rotate(P.rot ?? 0); scale((P.s ?? 1) * f, (P.s ?? 1) * (P.sq ?? 1));
  // legs
  for (const sx of [-1, 1]) {
    const hip = [sx * 30, -150];
    let knee, ank;
    if (P.sit) { knee = [sx * 22 + 74, -150]; ank = [sx * 22 + 80 + (P.kick ? Math.sin((P.t || 0) * 8 + sx) * 10 : 0), -40]; }
    else { knee = [sx * 32, -90]; ank = [sx * 32 + (P.leg?.[sx > 0 ? 1 : 0] || 0), -30]; }
    shape(noodle(hip, knee, 0, 30, 28), { fill: PAL.gSkin, lw: 6 });
    shape(noodle(knee, ank, 0, 28, 26), { fill: PAL.gSkin, lw: 6, shade: () => fillOnly(rect(-300, ank[1] - 34, 600, 60), PAL.sock, { boil: .3 }) });
    shape(spline([[ank[0] - 22, ank[1] + 26], [ank[0] - 20, ank[1] + 2], [ank[0] + 14, ank[1] - 2], [ank[0] + 46, ank[1] + 14], [ank[0] + 44, ank[1] + 28]]), { fill: PAL.shoe, lw: 6, shade: () => fillOnly(ell(ank[0] + 30, ank[1] + 8, 8, 4, 8), '#ffffff', { boil: 0 }) });
  }
  push(); rotate(P.lean ?? 0);
  const shB = [-62, -310], shF = [58, -310];
  const drawArm = (sh, arm, front) => {
    const hp = [sh[0] + arm.h[0], sh[1] + arm.h[1]];
    shape(noodle(sh, hp, arm.bend ?? 0, 26, 22), { fill: PAL.gSkin, lw: 6 });
    shape(noodle(sh, [sh[0] + arm.h[0] * .3, sh[1] + arm.h[1] * .3], 0, 40, 36), { fill: PAL.gown, lw: 6 });
    const ang = Math.atan2(hp[1] - sh[1], hp[0] - sh[0]);
    if (front && P.case === 'hand') briefcase(hp[0], hp[1] + 20, 0, .8);
    hand(hp[0], hp[1], ang, 17, PAL.gSkin, { fist: !!arm.fist || (front && P.case === 'hand') });
  };
  drawArm(shB, P.armB || { h: [-20, 120], bend: -14 }, false);
  // gown: a pear
  const body = spline([[0, -340], [62, -320], [100, -220], [120, -130], [60, -112], [0, -118], [-60, -112], [-120, -130], [-100, -220], [-62, -320]]);
  shape(body, {
    fill: PAL.gown, lw: 7, shade: () => {
      fillOnly(spline([[30, -350], [110, -300], [140, -120], [70, -100], [80, -220]]), PAL.gownS, { boil: .4 });
      for (let i = 0; i < 18; i++) dot(-90 + hash(i * 1.9) * 180, -300 + hash(i * 4.3) * 180, 5, PAL.gownDot);
    }
  });
  if (P.case === 'lap') briefcase(10, -170, 0, .9);
  // collar + necktie (still at work)
  shape([[-36, -338], [0, -326], [36, -338], [20, -310], [0, -318], [-20, -310]], { fill: '#ffffff', lw: 5 });
  shape(spline([[-12, -322], [12, -322], [8, -306], [-8, -306]]), { fill: PAL.tie, lw: 5 });
  shape([[-9, -306], [9, -306], [20, -200], [0, -180], [-20, -200]], { fill: PAL.tie, lw: 6, shade: () => { for (let k = 0; k < 4; k++) fillOnly([[-30, -300 + k * 28], [30, -310 + k * 28], [30, -300 + k * 28], [-30, -290 + k * 28]], PAL.tieS, { boil: .2 }); } });
  push(); translate(0, -430); rotate(P.headTilt ?? 0);
  gusHead(P, ner);
  pop();
  drawArm(shF, P.armF || { h: [20, 120], bend: 14 }, true);
  pop();
  if (P.sweat != null) { const u = P.sweat % 1; sweat(-100, -560 + u * 40, 1.1); sweat(100, -540 + ((u + .5) % 1) * 40, .9); }
  pop();
}
function gusHead(P, ner) {
  for (const sx of [-1, 1]) shape(ell(sx * 96, 10, 20, 28, 16), { fill: PAL.gSkin, lw: 6, shade: () => fillOnly(ell(sx * 96, 12, 8, 14, 10), PAL.gSkinS, { boil: .3 }) });
  shape(ell(0, 0, 98, 96, 60), { fill: PAL.gSkin, lw: 7, shade: () => fillOnly(ell(52, 34, 62, 70, 30), PAL.gSkinS, { boil: .3 }) });
  // comb-over: three sad hairs
  for (const k of [-1, 0, 1]) stroke(spline([[-40 + k * 18, -92], [0 + k * 16, -112 - k * 4], [50 + k * 10, -96]], false), 5);
  // eyes (touching, big) + bags
  const look = P.look || [0, 0], shake = ner ? (hash(Math.floor((P.t || 0) * 24) * 1.7) - .5) * 4 * ner : 0, es = P.eyeS ?? 1;
  for (const ex of [-34, 34]) {
    stroke(arc(ex, 30, 24, 8, Math.PI * .15, Math.PI * .85, 10), 4, { line: PAL.gSkinS });
    eye(ex, -6, 34 * es, 36 * es, { lid: P.blink ? 1 : (P.lid ?? .1), look, closed: P.closed, pupil: P.pupil ?? 4.2, skin: PAL.gSkin, jitter: shake, lw: 6 });
  }
  // worried brows
  const br = P.brow ?? 1;
  stroke([[-70, -48 + br * 2], [-28, -58 - br * 10]], 8); stroke([[70, -48 + br * 2], [28, -58 - br * 10]], 8);
  // nose + big moustache
  shape(ell(0, 30, 16, 13, 14), { fill: PAL.gSkinS, lw: 5 });
  shape(spline([[-60, 54], [-30, 40], [0, 48], [30, 40], [60, 54], [36, 62], [0, 58], [-36, 62]]), { fill: PAL.hair, lw: 5 });
  const m = P.mouth || {};
  mouth(0, 74, 50, { o: m.o || 0, w: m.w ?? 1, sm: m.sm ?? -.5, skew: m.skew || 0, lw: 5 });
}
