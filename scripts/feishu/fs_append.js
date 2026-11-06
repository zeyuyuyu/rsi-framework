// Append a section (heading2 + intro + ordered list) at the END of a Feishu doc: the last rendered block must be an
// empty text block. Checks the doc title, every markdown conversion, and stops at the first surprise.
// usage: node fs_append.js <url-substring> <expected-title-substring> <content.json> [dry]
const { chromium } = require('/home/zeyu/.npm/_npx/86170c4cd1c5da32/node_modules/playwright-core');
(async () => {
  const [sub, titleSub, file, dry] = process.argv.slice(2);
  const c = JSON.parse(require('fs').readFileSync(file, 'utf8'));
  const browser = await chromium.connectOverCDP('http://127.0.0.1:9333');
  const page = browser.contexts()[0].pages().find(p => p.url().includes(sub));
  if (!page) throw new Error('doc tab not found');
  await page.bringToFront();
  const title = await page.evaluate(() => (document.querySelector('[data-block-type="page"]') || {}).innerText || '');
  if (!title.includes(titleSub)) throw new Error('unexpected doc: ' + title.slice(0, 80));
  const blocks = async () => page.evaluate(() => Array.from(document.querySelectorAll('[data-block-id]'))
    .filter(b => b.parentElement && b.parentElement.closest('[data-block-type="page"]') && !b.parentElement.closest('[data-block-type]:not([data-block-type="page"])'))
    .map(b => ({ id: b.getAttribute('data-block-id'), type: b.getAttribute('data-block-type'), text: b.innerText.replace(/​/g, '').trim() })));
  await page.evaluate(() => { const els = Array.from(document.querySelectorAll('*')).filter(e => e.scrollHeight > e.clientHeight + 200 && ['auto', 'scroll'].includes(getComputedStyle(e).overflowY)); const s = els.sort((a, b) => b.scrollHeight - a.scrollHeight)[0]; s.scrollTop = s.scrollHeight; });
  await page.waitForTimeout(2500);
  let bl = await blocks();
  console.log('tail blocks:', bl.slice(-6).map(b => `${b.type}${b.text ? ':' + b.text.slice(0, 16) : ''}`).join(' | '));
  if (bl.some(b => b.type === 'heading2' && b.text.includes(c.heading))) throw new Error('section already exists');
  let target;
  if (c.after) {   // insert into the first empty text block after the unique block containing c.after
    const hits = bl.filter(b => b.text.includes(c.after));
    if (hits.length !== 1) throw new Error('anchor not unique: ' + hits.length);
    target = bl.slice(bl.indexOf(hits[0]) + 1).find(b => b.type === 'text' && b.text === '');
    if (!target) throw new Error('no empty text block after the anchor');
    const nxt = bl[bl.indexOf(target) + 1];
    console.log('anchor', hits[0].id, '| target', target.id, '| block after target:', nxt ? nxt.type + ':' + nxt.text.slice(0, 20) : 'none');
  } else {
    target = bl[bl.length - 1];
    if (!target || target.type !== 'text' || target.text !== '') throw new Error('last block is not an empty text block: ' + (target ? target.type + ':' + target.text.slice(0, 30) : 'none'));
  }
  console.log('editable blocks:', await page.evaluate(() => document.querySelectorAll('[contenteditable="true"]').length), '| target block', target.id);
  if (dry) process.exit(0);
  const el = page.locator(`[data-block-id="${target.id}"]`);
  await el.scrollIntoViewIfNeeded(); await el.click(); await page.waitForTimeout(500);
  const typeOf = async () => page.evaluate(() => { const s = window.getSelection(); if (!s || !s.anchorNode) return null; const n = s.anchorNode.nodeType === 1 ? s.anchorNode : s.anchorNode.parentElement; const b = n.closest('[data-block-type]'); return b ? b.getAttribute('data-block-type') : null; });
  if ((await typeOf()) !== 'text') throw new Error('caret not in a text block: ' + await typeOf());
  await page.keyboard.type('## ', { delay: 80 }); await page.waitForTimeout(400);
  if ((await typeOf()) !== 'heading2') throw new Error('heading shortcut did not convert: ' + await typeOf());
  await page.keyboard.insertText(c.heading); await page.keyboard.press('Enter'); await page.waitForTimeout(400);
  if (c.intro) { await page.keyboard.insertText(c.intro); await page.keyboard.press('Enter'); await page.waitForTimeout(400); }
  await page.keyboard.type('1. ', { delay: 80 }); await page.waitForTimeout(400);
  if ((await typeOf()) !== 'ordered') throw new Error('list shortcut did not convert: ' + await typeOf());
  for (let i = 0; i < c.items.length; i++) { await page.keyboard.insertText(c.items[i]); if (i < c.items.length - 1) { await page.keyboard.press('Enter'); await page.waitForTimeout(400); } }
  await page.waitForTimeout(2500);
  bl = await blocks();
  const h = bl.findIndex(b => b.type === 'heading2' && b.text.includes(c.heading));
  console.log('AFTER:'); for (const b of bl.slice(Math.max(0, h), h + 2 + c.items.length + 1)) console.log(`[${b.type}] ${b.text.slice(0, 90)}`);
  await page.screenshot({ path: file.replace('.json', '-after.png') });
  process.exit(0);
})().catch(e => { console.error('ERR', e.message); process.exit(1); });
