// Replace exact substrings in a Feishu doc. Each `find` must sit in exactly one rendered block and inside one text
// node (scrolls through the virtualized doc to find it); otherwise it is SKIPPED and reported.
// usage: node fs_replace.js <url-sub> <title-sub> <edits.json> [dry]   edits: [{find, replace}, ...]
const { chromium } = require('/home/zeyu/.npm/_npx/86170c4cd1c5da32/node_modules/playwright-core');
(async () => {
  const [sub, titleSub, file, dry] = process.argv.slice(2);
  const edits = JSON.parse(require('fs').readFileSync(file, 'utf8'));
  const browser = await chromium.connectOverCDP('http://127.0.0.1:9333');
  const page = browser.contexts()[0].pages().find(p => p.url().includes(sub));
  if (!page) throw new Error('doc tab not found');
  await page.bringToFront();
  const title = await page.evaluate(() => (document.querySelector('[data-block-type="page"]') || {}).innerText || '');
  if (!title.includes(titleSub)) throw new Error('unexpected doc');
  const scroller = async (to) => page.evaluate((to) => { const els = Array.from(document.querySelectorAll('*')).filter(e => e.scrollHeight > e.clientHeight + 200 && ['auto', 'scroll'].includes(getComputedStyle(e).overflowY)); const s = els.sort((a, b) => b.scrollHeight - a.scrollHeight)[0]; if (to === 'top') s.scrollTop = 0; else s.scrollTop += s.clientHeight * 0.6; return [s.scrollTop, s.scrollHeight - s.clientHeight]; }, to);
  // a `find` may span several text nodes of one block (Feishu splits long pasted text): match on the concatenated text
  const locate = async (find) => page.evaluate((find) => {
    const blocks = Array.from(document.querySelectorAll('[data-block-id]')).filter(b => !b.querySelector('[data-block-id]'));
    const hits = blocks.filter(b => b.innerText.replace(/\u200b/g, '').includes(find));
    if (hits.length !== 1) return { n: hits.length };
    const w = document.createTreeWalker(hits[0], NodeFilter.SHOW_TEXT); let cat = ''; while (w.nextNode()) cat += w.currentNode.textContent;
    return { n: 1, id: hits[0].getAttribute('data-block-id'), node: cat.replace(/\u200b/g, '').includes(find) }; }, find);
  const report = [];
  for (const e of edits) {
    await scroller('top'); await page.waitForTimeout(1000);
    let loc = await locate(e.find), guard = 0;
    while (loc.n === 0 && guard++ < 50) { const [pos, max] = await scroller('down'); await page.waitForTimeout(700); loc = await locate(e.find); if (pos >= max) break; }
    if (loc.n !== 1 || !loc.node) { report.push(`SKIP (${loc.n} blocks, one node: ${loc.node}): ${e.find.slice(0, 40)}`); continue; }
    if (dry) { report.push(`ok: ${e.find.slice(0, 40)}`); continue; }
    const blk = page.locator(`[data-block-id="${loc.id}"]`);
    await blk.scrollIntoViewIfNeeded(); await page.keyboard.press('Escape'); await page.waitForTimeout(300);
    const sel = await page.evaluate(({ id, find }) => {
      const b = document.querySelector(`[data-block-id="${id}"]`);
      const w = document.createTreeWalker(b, NodeFilter.SHOW_TEXT); const nodes = []; while (w.nextNode()) nodes.push(w.currentNode);
      // map the match on the zero-width-stripped concatenation back to (node, offset) pairs
      let cat = '', map = [];   // map[i] = [nodeIndex, offsetInNode] for each kept character
      nodes.forEach((n, ni) => { for (let k = 0; k < n.textContent.length; k++) { const ch = n.textContent[k]; if (ch !== '\u200b') { cat += ch; map.push([ni, k]); } } });
      const i = cat.indexOf(find); if (i < 0) return null;
      const [sn, so] = map[i], [en, eo] = map[i + find.length - 1];
      const r = document.createRange(); r.setStart(nodes[sn], so); r.setEnd(nodes[en], eo + 1);
      const s = window.getSelection(); s.removeAllRanges(); s.addRange(r);
      const ce = b.closest('[contenteditable="true"]'); if (ce) ce.focus();
      return s.toString().replace(/\u200b/g, ''); }, { id: loc.id, find: e.find });
    await page.waitForTimeout(400);
    if (sel !== e.find) throw new Error('selection mismatch on: ' + e.find.slice(0, 40));
    await page.keyboard.insertText(e.replace); await page.waitForTimeout(1200);
    const now = await page.evaluate(id => (document.querySelector(`[data-block-id="${id}"]`) || {}).innerText || '', loc.id);
    if (!now.replace(/​/g, '').includes(e.replace)) throw new Error('block did not update for: ' + e.find.slice(0, 40));
    report.push(`done: ${e.find.slice(0, 40)}`);
  }
  console.log(report.join('\n')); process.exit(0);
})().catch(e => { console.error('ERR', e.message); process.exit(1); });
