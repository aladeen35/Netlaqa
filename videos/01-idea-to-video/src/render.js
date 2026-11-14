// Deterministic frame renderer. Usage:
// node src/render.js --from 0 --to 45 --fps 30 --scale 1 --out cache/frames [--jpg]
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const a = process.argv.slice(2);
const opt = (k, d) => { const i = a.indexOf('--' + k); return i >= 0 ? a[i + 1] : d; };
const from = +opt('from', 0), to = +opt('to', 45), fps = +opt('fps', 30), scale = +opt('scale', 1);
const out = opt('out', 'cache/frames');
const W = Math.round(1080 * scale), H = Math.round(1920 * scale);

(async () => {
  fs.mkdirSync(out, { recursive: true });
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: 1 });
  page.on('pageerror', (e) => { console.error('page error:', e.message); process.exit(1); });
  await page.goto('file://' + path.resolve(__dirname, 'index.html') + '?scale=' + scale);
  await page.waitForFunction(() => window.READY === true, null, { timeout: 30000 });
  fs.mkdirSync('cache', { recursive: true });
  fs.writeFileSync('cache/cues.json', await page.evaluate(() => JSON.stringify(window.CUES)));
  const n = Math.max(1, Math.round((to - from) * fps));
  const t0 = Date.now();
  for (let i = 0; i < n; i++) {
    const t = from + i / fps;
    await page.evaluate((t) => window.drawFrame(t), t);
    await page.screenshot({ path: path.join(out, String(i).padStart(5, '0') + '.jpg'), type: 'jpeg', quality: 92 });
    if (i % 150 === 0) process.stderr.write(`frame ${i}/${n} t=${t.toFixed(2)}\n`);
  }
  console.error(`rendered ${n} frames in ${((Date.now() - t0) / 1000).toFixed(1)}s`);
  await browser.close();
})();
