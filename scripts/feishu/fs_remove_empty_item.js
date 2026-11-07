// Remove one empty list item that sits right AFTER the unique top-level block containing argv[3] (Feishu: Backspace
// on an empty list item turns it into a paragraph; a second Backspace removes the empty paragraph). Verifies the
// anchor block's text is unchanged. usage: node fs_remove_empty_item.js <url-substring> <anchor-text> [dry]
const { chromium } = require('/home/zeyu/.npm/_npx/86170c4cd1c5da32/node_modules/playwright-core');
(async () => {
  const [sub, anchorText, dry] = process.argv.slice(2);
  const browser = await chromium.connectOverCDP('http://127.0.0.1:9333');
  const page = browser.contexts()[0].pages().find(p => p.url().includes(sub));
  if (!page) throw new Error('doc tab not found');
  await page.bringToFront();
  const blocks = async () => page.evaluate(() => Array.from(document.querySelectorAll('[data-block-id]'))
    .filter(b => b.parentElement && b.parentElement.closest('[data-block-type="page"]') && !b.parentElement.closest('[data-block-type]:not([data-block-type="page"])'))
    .map(b => ({ id: b.getAttribute('data-block-id'), type: b.getAttribute('data-block-type'), text: (b.innerText || '').replace(/​/g, '').trim() })));
  // the stray item sits near the bottom and Feishu renders only nearby blocks: scroll to the end first
  await page.evaluate(() => { const els = Array.from(document.querySelectorAll('*')).filter(e => e.scrollHeight > e.clientHeight + 200 && ['auto', 'scroll'].includes(getComputedStyle(e).overflowY)); const s = els.sort((a, b) => b.scrollHeight - a.scrollHeight)[0]; s.scrollTop = s.scrollHeight; });
  await page.waitForTimeout(2500);
  let bl = await blocks();
  let hits = bl.filter(b => b.text.includes(anchorText));
  if (hits.length !== 1) throw new Error('anchor not unique: ' + hits.length);
  await page.locator(`[data-block-id="${hits[0].id}"]`).scrollIntoViewIfNeeded(); await page.waitForTimeout(600);
  bl = await blocks(); hits = bl.filter(b => b.text.includes(anchorText));
  const k = bl.indexOf(hits[0]); const prev = bl[k]; const victim = bl[k + 1];
  if (!victim) throw new Error('no block after the anchor is rendered');
  console.log('victim', victim.type, JSON.stringify(victim.text.slice(0, 40)), '| anchor', prev.type, prev.text.slice(0, 40));
  if (!['ordered', 'bullet'].includes(victim.type) || !/^(\d+\.)?$/.test(victim.text)) throw new Error('block after the anchor is not an empty list item');
  if (dry) process.exit(0);
  const el = page.locator(`[data-block-id="${victim.id}"]`); await el.scrollIntoViewIfNeeded(); await el.click(); await page.waitForTimeout(300);
  const caretType = async () => page.evaluate(() => { const s = window.getSelection(); if (!s || !s.anchorNode) return null; const n = s.anchorNode.nodeType === 1 ? s.anchorNode : s.anchorNode.parentElement; const b = n.closest('[data-block-type]'); return b ? b.getAttribute('data-block-type') : null; });
  if (!['ordered', 'bullet'].includes(await caretType())) throw new Error('caret not in the list item: ' + await caretType());
  await page.keyboard.press('Backspace'); await page.waitForTimeout(400);
  let t = await caretType(); console.log('after 1st Backspace caret in', t);
  bl = await blocks(); let cur = bl.find(b => b.id === victim.id);
  if (t === 'text' && cur && /^(\d+\.)?$/.test(cur.text)) { await page.keyboard.press('Backspace'); await page.waitForTimeout(400); }
  bl = await blocks(); const p2 = bl.find(b => b.id === prev.id); const gone = !bl.find(b => b.id === victim.id);
  console.log('victim gone:', gone, '| anchor unchanged:', !!(p2 && p2.text === prev.text));
  const k2 = bl.findIndex(b => b.id === prev.id);
  console.log('TAIL:'); for (const b of bl.slice(Math.max(0, k2 - 1), k2 + 3)) console.log(`[${b.type}] ${b.text.slice(0, 80)}`);
  await page.screenshot({ path: '/tmp/claude-1000/-home-zeyu-a5labs/48689c83-7841-4a15-9b22-728803e7db48/scratchpad/remove_empty_item-after.png' });
  process.exit(0);
})().catch(e => { console.error('ERROR', e.message); process.exit(1); });
