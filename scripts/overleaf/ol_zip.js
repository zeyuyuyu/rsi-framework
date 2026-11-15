// Download an Overleaf project's source zip through the logged-in browser tab. usage: node ol_zip.js <projectId> <out.zip>
const { chromium } = require('/home/zeyu/.npm/_npx/86170c4cd1c5da32/node_modules/playwright-core');
(async () => {
  const [pid, out] = process.argv.slice(2);
  const browser = await chromium.connectOverCDP('http://127.0.0.1:9333');
  const page = browser.contexts()[0].pages().find(p => p.url().includes(pid));
  if (!page) throw new Error('tab not found ' + pid);
  const r = await page.evaluate(async (pid) => {
    const res = await fetch(`/project/${pid}/download/zip`, { credentials: 'include' });
    const buf = new Uint8Array(await res.arrayBuffer()); let s = ''; for (let i = 0; i < buf.length; i += 0x8000) s += String.fromCharCode.apply(null, buf.subarray(i, i + 0x8000));
    return { status: res.status, b64: btoa(s) }; }, pid);
  require('fs').writeFileSync(out, Buffer.from(r.b64, 'base64'));
  console.log('status', r.status, 'bytes', Buffer.from(r.b64, 'base64').length, 'title', await page.title());
  process.exit(0);
})().catch(e => { console.error('ERR', e.message); process.exit(1); });
