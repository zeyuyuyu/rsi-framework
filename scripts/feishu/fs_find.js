// Print the block containing <text> and its previous/next top-level siblings (DOM order). usage: node fs_find.js <url-sub> <text>
const { chromium } = require('/home/zeyu/.npm/_npx/86170c4cd1c5da32/node_modules/playwright-core');
(async () => {
  const [sub, text] = process.argv.slice(2);
  const browser = await chromium.connectOverCDP('http://127.0.0.1:9333');
  const page = browser.contexts()[0].pages().find(p => p.url().includes(sub));
  await page.bringToFront();
  const scroller = async (to) => page.evaluate((to) => { const els = Array.from(document.querySelectorAll('*')).filter(e => e.scrollHeight > e.clientHeight + 200 && ['auto','scroll'].includes(getComputedStyle(e).overflowY)); const s = els.sort((a,b)=>b.scrollHeight-a.scrollHeight)[0]; if (to === 'top') s.scrollTop = 0; else s.scrollTop += s.clientHeight * 0.6; return [s.scrollTop, s.scrollHeight - s.clientHeight]; }, to);
  await scroller('top'); await page.waitForTimeout(1000);
  for (let g = 0; g < 60; g++) {
    const r = await page.evaluate((text) => {
      const tops = Array.from(document.querySelectorAll('[data-block-id]')).filter(b => b.parentElement && b.parentElement.closest('[data-block-type="page"]') && !b.parentElement.closest('[data-block-type]:not([data-block-type="page"])'));
      const i = tops.findIndex(b => b.innerText.includes(text));
      if (i < 0) return null;
      const f = b => b ? `[${b.getAttribute('data-block-type')}#${b.getAttribute('data-block-id')}] ${b.innerText.replace(/​/g,'').replace(/\n+/g,' | ').trim().slice(0, 70)}` : 'none';
      return { prev: f(tops[i-1]), hit: f(tops[i]), next: f(tops[i+1]), next2: f(tops[i+2]) };
    }, text);
    if (r) { console.log(JSON.stringify(r, null, 1)); process.exit(0); }
    const [pos, max] = await scroller('down'); await page.waitForTimeout(600); if (pos >= max) break;
  }
  console.log('NOT FOUND'); process.exit(2);
})().catch(e => { console.error('ERR', e.message); process.exit(1); });
