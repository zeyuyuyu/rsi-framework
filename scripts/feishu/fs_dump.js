// Dump every top-level block of a Feishu doc tab (url substring in argv[2]) in document order; screenshot to argv[3].
const { chromium } = require('/home/zeyu/.npm/_npx/86170c4cd1c5da32/node_modules/playwright-core');
(async () => {
  const [sub, shot] = process.argv.slice(2);
  const browser = await chromium.connectOverCDP('http://127.0.0.1:9333');
  const page = browser.contexts()[0].pages().find(p => p.url().includes(sub));
  if (!page) throw new Error('tab not found');
  await page.bringToFront();
  console.log('URL', page.url()); console.log('TITLE', await page.title());
  console.log('editable blocks', await page.evaluate(() => document.querySelectorAll('[contenteditable="true"]').length));
  const step = async (to) => page.evaluate((to) => {
    const els = Array.from(document.querySelectorAll('*')).filter(e => e.scrollHeight > e.clientHeight + 200 && ['auto','scroll'].includes(getComputedStyle(e).overflowY));
    const s = els.sort((a,b)=>b.scrollHeight-a.scrollHeight)[0]; if (!s) return true;
    if (to === 'top') s.scrollTop = 0; else s.scrollTop += s.clientHeight * 0.5;
    return s.scrollTop + s.clientHeight >= s.scrollHeight - 5; }, to);
  const grab = async () => page.evaluate(() => Array.from(document.querySelectorAll('[data-block-id]'))
    .filter(b => b.parentElement && b.parentElement.closest('[data-block-type="page"]') && !b.parentElement.closest('[data-block-type]:not([data-block-type="page"])'))
    .map(b => ({ id: b.getAttribute('data-block-id'), type: b.getAttribute('data-block-type'), text: b.innerText.replace(/​/g, '').replace(/\n+/g, ' | ').trim() })));
  await step('top'); await page.waitForTimeout(1500);
  const seen = new Map(); const order = [];
  for (let i = 0; i < 80; i++) {
    for (const b of await grab()) { if (!seen.has(b.id)) { seen.set(b.id, b); order.push(b.id); } else if (b.text.length > seen.get(b.id).text.length) seen.set(b.id, b); }
    const end = await step('down'); await page.waitForTimeout(700);
    if (end) { for (const b of await grab()) if (!seen.has(b.id)) { seen.set(b.id, b); order.push(b.id); } break; }
  }
  const ids = process.env.FS_DOM_ORDER ? order : (order.map(Number).every(n => !isNaN(n)) ? order.slice().sort((a,b)=>a-b) : order);
  console.log('BLOCKS', ids.length);
  for (const id of ids) { const b = seen.get(id); console.log(`[${b.type}] ${b.text}`); }
  if (shot) await page.screenshot({ path: shot });
  process.exit(0);
})().catch(e => { console.error('ERR', e.message); process.exit(1); });
