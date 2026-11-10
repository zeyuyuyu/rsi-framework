// Delete one list item or paragraph of a Feishu doc, identified by its block id AND the exact text it must hold
// (so a block someone else has edited since it was read is never touched). The text is selected and removed, then
// the empty item is removed with Backspace (list item -> paragraph -> gone). Neighbours are checked afterwards.
// usage: node fs_delete_block.js <url-sub> <title-sub> <block-id> <exact text> [dry]
const { chromium } = require('/home/zeyu/.npm/_npx/86170c4cd1c5da32/node_modules/playwright-core');
(async () => {
  const [sub, titleSub, id, expect, dry] = process.argv.slice(2);
  const browser = await chromium.connectOverCDP('http://127.0.0.1:9333');
  const page = browser.contexts()[0].pages().find(p => p.url().includes(sub));
  if (!page) throw new Error('doc tab not found');
  await page.bringToFront();
  const title = await page.evaluate(() => (document.querySelector('[data-block-type="page"]') || {}).innerText || '');
  if (!title.includes(titleSub)) throw new Error('unexpected doc');
  const blocks = async () => page.evaluate(() => Array.from(document.querySelectorAll('[data-block-id]'))
    .filter(b => b.parentElement && b.parentElement.closest('[data-block-type="page"]') && !b.parentElement.closest('[data-block-type]:not([data-block-type="page"])'))
    .map(b => ({ id: b.getAttribute('data-block-id'), type: b.getAttribute('data-block-type'), text: (b.innerText || '').replace(/​/g, '').trim() })));
  const scroller = async (to) => page.evaluate((to) => { const els = Array.from(document.querySelectorAll('*')).filter(e => e.scrollHeight > e.clientHeight + 200 && ['auto', 'scroll'].includes(getComputedStyle(e).overflowY)); const s = els.sort((a, b) => b.scrollHeight - a.scrollHeight)[0]; if (to === 'top') s.scrollTop = 0; else s.scrollTop += s.clientHeight * 0.6; return [s.scrollTop, s.scrollHeight - s.clientHeight]; }, to);
  const body = t => t.replace(/^\d+\.\s*/, '').trim();          // a list item's innerText starts with its number
  await scroller('top'); await page.waitForTimeout(1000);
  let bl = await blocks();
  for (let g = 0; g < 80 && !bl.find(b => b.id === id); g++) { const [pos, max] = await scroller('down'); await page.waitForTimeout(700); bl = await blocks(); if (pos >= max) break; }
  if (!bl.find(b => b.id === id)) throw new Error('block not found: ' + id);
  await page.locator(`[data-block-id="${id}"]`).scrollIntoViewIfNeeded(); await page.waitForTimeout(600);
  bl = await blocks();
  const k = bl.findIndex(b => b.id === id), victim = bl[k], prev = bl[k - 1], next = bl[k + 1];
  if (!['ordered', 'bullet', 'text'].includes(victim.type)) throw new Error('not a list item or paragraph: ' + victim.type);
  if (body(victim.text) !== expect) throw new Error('block text differs from the expected text (edited by someone?): ' + body(victim.text).slice(0, 60));
  if (!prev) throw new Error('previous block not rendered');
  console.log('delete', victim.type + '#' + id, body(victim.text).slice(0, 40), '| prev', prev.type, prev.text.slice(0, 30), '| next', next ? next.type + ' ' + next.text.slice(0, 30) : 'none');
  if (dry) process.exit(0);
  await page.keyboard.press('Escape'); await page.waitForTimeout(300);
  const sel = await page.evaluate(({ id, find }) => {
    const b = document.querySelector(`[data-block-id="${id}"]`);
    const w = document.createTreeWalker(b, NodeFilter.SHOW_TEXT); const nodes = []; while (w.nextNode()) nodes.push(w.currentNode);
    let cat = '', map = [];
    nodes.forEach((n, ni) => { for (let j = 0; j < n.textContent.length; j++) { const ch = n.textContent[j]; if (ch !== '​') { cat += ch; map.push([ni, j]); } } });
    const i = cat.indexOf(find); if (i < 0) return null;
    const [sn, so] = map[i], [en, eo] = map[i + find.length - 1];
    const r = document.createRange(); r.setStart(nodes[sn], so); r.setEnd(nodes[en], eo + 1);
    const s = window.getSelection(); s.removeAllRanges(); s.addRange(r);
    const ce = b.closest('[contenteditable="true"]'); if (ce) ce.focus();
    return s.toString().replace(/​/g, ''); }, { id, find: expect });
  await page.waitForTimeout(400);
  if (sel !== expect) throw new Error('selection mismatch');
  const caretType = async () => page.evaluate(() => { const s = window.getSelection(); if (!s || !s.anchorNode) return null; const n = s.anchorNode.nodeType === 1 ? s.anchorNode : s.anchorNode.parentElement; const b = n.closest('[data-block-id]'); return b ? b.getAttribute('data-block-type') + '#' + b.getAttribute('data-block-id') : null; });
  await page.keyboard.press('Backspace'); await page.waitForTimeout(700);
  bl = await blocks(); let cur = bl.find(b => b.id === id);
  if (!cur || body(cur.text) !== '') throw new Error('text was not removed: ' + (cur ? cur.text.slice(0, 40) : 'block gone'));
  if (!(await caretType() || '').endsWith('#' + id)) throw new Error('caret left the block: ' + await caretType());
  for (let n = 0; n < 2; n++) {                        // list item -> paragraph -> gone
    bl = await blocks(); cur = bl.find(b => b.id === id);
    if (!cur) break;
    if (body(cur.text) !== '' || !(await caretType() || '').endsWith('#' + id)) throw new Error('unexpected state before Backspace: ' + cur.text.slice(0, 30) + ' caret ' + await caretType());
    await page.keyboard.press('Backspace'); await page.waitForTimeout(600);
  }
  bl = await blocks();
  const gone = !bl.find(b => b.id === id), p2 = bl.find(b => b.id === prev.id), n2 = next ? bl.find(b => b.id === next.id) : null;
  console.log('gone:', gone, '| prev unchanged:', !!(p2 && p2.text.replace(/^\d+\.\s*/, '') === prev.text.replace(/^\d+\.\s*/, '')), '| next unchanged:', !next || !!(n2 && n2.text.replace(/^\d+\.\s*/, '') === next.text.replace(/^\d+\.\s*/, '')));
  if (!gone) throw new Error('block still there');
  process.exit(0);
})().catch(e => { console.error('ERR', e.message); process.exit(1); });
