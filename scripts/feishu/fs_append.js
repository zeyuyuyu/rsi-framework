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
  if (bl.some(b => b.type.startsWith('heading') && b.text.includes(c.heading))) throw new Error('section already exists');
  let target;
  if (c.insert_after) {   // new paragraph right after the unique block containing c.insert_after (a text block)
    // Feishu renders only nearby blocks: scroll from the top until the anchor is in the DOM
    const scroller = async (to) => page.evaluate((to) => { const els = Array.from(document.querySelectorAll('*')).filter(e => e.scrollHeight > e.clientHeight + 200 && ['auto','scroll'].includes(getComputedStyle(e).overflowY)); const s = els.sort((a,b)=>b.scrollHeight-a.scrollHeight)[0]; if (to === 'top') s.scrollTop = 0; else s.scrollTop += s.clientHeight * 0.6; return [s.scrollTop, s.scrollHeight - s.clientHeight]; }, to);
    await scroller('top'); await page.waitForTimeout(1000);
    let hits = [];
    for (let g = 0; g < 60; g++) {
      bl = await blocks(); hits = bl.filter(b => b.text.includes(c.insert_after));
      if (hits.length) break;
      const [pos, max] = await scroller('down'); await page.waitForTimeout(600); if (pos >= max) break;
    }
    if (hits.length !== 1) throw new Error('insert_after anchor not unique: ' + hits.length);
    const anchor = hits[0];
    const nxt = bl[bl.indexOf(anchor) + 1];
    console.log('insert after', anchor.type + '#' + anchor.id, '| next block:', nxt ? nxt.type + ':' + nxt.text.slice(0, 20) : 'none');
    if (dry) { console.log('editable blocks:', await page.evaluate(() => document.querySelectorAll('[contenteditable="true"]').length)); process.exit(0); }
    const caretType = async () => page.evaluate(() => { const s = window.getSelection(); if (!s || !s.anchorNode) return null; const n = s.anchorNode.nodeType === 1 ? s.anchorNode : s.anchorNode.parentElement; const b = n.closest('[data-block-type]'); return b ? b.getAttribute('data-block-type') : null; });
    let t;
    if (nxt && ['ordered', 'bullet'].includes(nxt.type) && nxt.text === '') {
      // an empty list item already follows the anchor (left by an earlier attempt): Enter on it leaves the list
      const el2 = page.locator(`[data-block-id="${nxt.id}"]`);
      await el2.scrollIntoViewIfNeeded(); await el2.click(); await page.waitForTimeout(300);
      await page.keyboard.press('Enter'); await page.waitForTimeout(500);
      t = await caretType();
    } else {
      const el = page.locator(`[data-block-id="${anchor.id}"]`);
      await el.scrollIntoViewIfNeeded(); await el.click(); await page.waitForTimeout(300);
      const placed = await page.evaluate((id) => { const b = document.querySelector(`[data-block-id="${id}"]`); const w = document.createTreeWalker(b, NodeFilter.SHOW_TEXT, { acceptNode: n => n.textContent.replace(/\u200b/g, '').length ? 1 : 3 }); let last = null; while (w.nextNode()) last = w.currentNode; if (!last) return false; const r = document.createRange(); r.setStart(last, last.textContent.length); r.collapse(true); const s = window.getSelection(); s.removeAllRanges(); s.addRange(r); return true; }, anchor.id);
      if (!placed) throw new Error('could not place the caret at the end of the anchor');
      await page.keyboard.press('End'); await page.keyboard.press('Enter'); await page.waitForTimeout(500);
      t = await caretType();
      if (['ordered', 'bullet'].includes(t)) { await page.keyboard.press('Enter'); await page.waitForTimeout(500); t = await caretType(); }   // anchor was a list item: a second Enter leaves the list
    }
    if (t !== 'text') throw new Error('Enter after the anchor did not give a text block: ' + t);
    target = null;
  } else if (c.after) {   // insert into the first empty text block after the unique block containing c.after
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
  console.log('editable blocks:', await page.evaluate(() => document.querySelectorAll('[contenteditable="true"]').length), '| target block', target ? target.id : '(new paragraph after anchor)');
  if (dry) process.exit(0);
  if (target) { const el = page.locator(`[data-block-id="${target.id}"]`); await el.scrollIntoViewIfNeeded(); await el.click(); await page.waitForTimeout(500); }
  const typeOf = async () => page.evaluate(() => { const s = window.getSelection(); if (!s || !s.anchorNode) return null; const n = s.anchorNode.nodeType === 1 ? s.anchorNode : s.anchorNode.parentElement; const b = n.closest('[data-block-type]'); return b ? b.getAttribute('data-block-type') : null; });
  if ((await typeOf()) !== 'text') throw new Error('caret not in a text block: ' + await typeOf());
  const level = c.level || 2;
  await page.keyboard.type('#'.repeat(level) + ' ', { delay: 80 }); await page.waitForTimeout(400);
  if ((await typeOf()) !== 'heading' + level) throw new Error('heading shortcut did not convert: ' + await typeOf());
  await page.keyboard.insertText(c.heading); await page.keyboard.press('Enter'); await page.waitForTimeout(400);
  if (c.intro) { await page.keyboard.insertText(c.intro); await page.keyboard.press('Enter'); await page.waitForTimeout(400); }
  await page.keyboard.type('1. ', { delay: 80 }); await page.waitForTimeout(400);
  if ((await typeOf()) !== 'ordered') throw new Error('list shortcut did not convert: ' + await typeOf());
  for (let i = 0; i < c.items.length; i++) { await page.keyboard.insertText(c.items[i]); if (i < c.items.length - 1) { await page.keyboard.press('Enter'); await page.waitForTimeout(400); } }
  await page.waitForTimeout(2500);
  bl = await blocks();
  const h = bl.findIndex(b => b.type.startsWith('heading') && b.text.includes(c.heading));
  console.log('AFTER:'); for (const b of bl.slice(Math.max(0, h), h + 2 + c.items.length + 1)) console.log(`[${b.type}] ${b.text.slice(0, 90)}`);
  await page.screenshot({ path: file.replace('.json', '-after.png') });
  process.exit(0);
})().catch(e => { console.error('ERR', e.message); process.exit(1); });
