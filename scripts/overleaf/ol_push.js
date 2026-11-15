// usage: node ol_push.js <projectId> <out.pdf> <file1> [file2 ...]   (tex/bib files first; pdf figures are sent in their own batch)
const { chromium } = require('/home/zeyu/.npm/_npx/86170c4cd1c5da32/node_modules/playwright-core');
const fs = require('fs'); const path = require('path');
const log = (...a) => console.log(new Date().toISOString().slice(11, 19), ...a);
(async () => {
  const [pid, outPdf, ...files] = process.argv.slice(2);
  const browser = await chromium.connectOverCDP('http://127.0.0.1:9333');
  const page = browser.contexts()[0].pages().find(p => p.url().includes(pid));
  if (!page) throw new Error('tab not found ' + pid);
  await page.bringToFront(); await page.waitForTimeout(1500);
  if ((await page.evaluate(() => document.body.innerText)).includes("You're offline")) { log('offline -> reload'); await page.reload({ waitUntil: 'load' }); await page.waitForTimeout(8000); }
  log('TITLE', await page.title());
  const batches = [files.filter(f => !f.endsWith('.pdf')), files.filter(f => f.endsWith('.pdf'))].filter(b => b.length);
  for (const batch of batches) {
    log('batch', batch.map(f => path.basename(f)).join(' '));
    await page.getByRole('button', { name: /Upload/ }).first().click();
    const input = page.locator('input[type=file]').first();
    await input.waitFor({ state: 'attached', timeout: 15000 });
    await input.setInputFiles(batch);
    // overwrite dialogs, one per existing file
    const t0 = Date.now(); let ow = 0;
    while (Date.now() - t0 < 60000) {
      const btn = page.getByRole('button', { name: /^Overwrite$/ });
      if (await btn.count()) { await btn.first().click(); ow++; await page.waitForTimeout(800); continue; }
      const txt = await page.evaluate(() => document.body.innerText);
      if (/Uploading|uploading/.test(txt)) { await page.waitForTimeout(800); continue; }
      await page.waitForTimeout(1500);
      if (!(await page.getByRole('button', { name: /^Overwrite$/ }).count())) break;
    }
    log('overwrites', ow);
    // close the upload modal if still open
    const close = page.getByRole('button', { name: /^Close$/ });
    for (let i = 0; i < 3 && await close.count(); i++) { try { await close.first().click({ timeout: 3000 }); } catch (e) {} await page.waitForTimeout(600); }
    await page.waitForTimeout(1500);
  }
  // verify the tree holds the files
  const tree = await page.evaluate(() => Array.from(document.querySelectorAll('[role="treeitem"]')).map(e => (e.getAttribute('aria-label') || e.innerText || '').trim().split('\n')[0]));
  for (const f of files) log('in tree:', path.basename(f), tree.includes(path.basename(f)));
  // recompile
  await page.getByRole('button', { name: /^Recompile$/ }).first().click();
  log('recompile clicked');
  await page.waitForTimeout(4000);
  for (let i = 0; i < 90; i++) { const txt = await page.evaluate(() => document.body.innerText); if (!/Compiling/.test(txt)) break; await page.waitForTimeout(2000); }
  const after = await page.evaluate(() => { const t = document.body.innerText; const m = t.match(/Errors\s*(\d+)/); const w = t.match(/Warnings\s*(\d+)/); return { errors: m && m[1], warnings: w && w[1], timeout: /timed out|Timed out/.test(t) }; });
  log('compile', JSON.stringify(after));
  // download pdf
  const href = await page.evaluate(() => { const a = Array.from(document.querySelectorAll('a[href*="output.pdf"]'))[0]; return a ? a.href : null; });
  log('pdf href', href && href.slice(0, 90));
  if (href && outPdf) {
    const b64 = await page.evaluate(async (u) => { const r = await fetch(u); const b = await r.blob(); return await new Promise(res => { const fr = new FileReader(); fr.onload = () => res(fr.result.split(',')[1]); fr.readAsDataURL(b); }); }, href);
    fs.writeFileSync(outPdf, Buffer.from(b64, 'base64')); log('saved', outPdf, fs.statSync(outPdf).size);
  }
  process.exit(0);
})().catch(e => { console.error('ERR', e.message); process.exit(1); });
