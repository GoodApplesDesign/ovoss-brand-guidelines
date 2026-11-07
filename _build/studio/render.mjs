// Render studio scenes with headless Chrome over CDP. Usage: node render.mjs <outDir> scene[:WxH] ...
import { spawn } from 'node:child_process';
import { writeFileSync, mkdirSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
const HERE = dirname(fileURLToPath(import.meta.url));
const [outDir, ...jobs] = process.argv.slice(2);
mkdirSync(outDir, { recursive: true });
const PORT = 9347, CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const chrome = spawn(CHROME, ['--headless=new', `--remote-debugging-port=${PORT}`, `--user-data-dir=${resolve(HERE, '.prof')}`,
  '--allow-file-access-from-files', '--hide-scrollbars', '--no-first-run', '--no-default-browser-check', '--enable-gpu', '--use-angle=metal', '--ignore-gpu-blocklist', 'about:blank'], { stdio: 'ignore' });
const sleep = ms => new Promise(r => setTimeout(r, ms));
let ver; for (let i = 0; i < 60 && !ver; i++) { try { ver = await (await fetch(`http://127.0.0.1:${PORT}/json/version`)).json(); } catch { await sleep(250); } }
function cdp(wsUrl) { const ws = new WebSocket(wsUrl); let id = 0; const pend = new Map(), listeners = [];
  ws.onmessage = ev => { const m = JSON.parse(ev.data); if (m.id && pend.has(m.id)) { const { res, rej } = pend.get(m.id); pend.delete(m.id); m.error ? rej(new Error(JSON.stringify(m.error))) : res(m.result); } else listeners.forEach(f => f(m)); };
  const ready = new Promise(r => ws.onopen = r);
  return { ready, on: f => listeners.push(f), close: () => ws.close(),
    send: (method, params = {}) => new Promise((res, rej) => { const i = ++id; pend.set(i, { res, rej }); ws.send(JSON.stringify({ id: i, method, params })); }) }; }
for (const job of jobs) {
  const [scene, dims] = job.split(':'); const [W, H] = (dims || '1000x1250').split('x').map(Number);
  const t = await (await fetch(`http://127.0.0.1:${PORT}/json/new?about:blank`, { method: 'PUT' })).json();
  const c = cdp(t.webSocketDebuggerUrl); await c.ready;
  c.on(m => { if (m.method === 'Runtime.exceptionThrown') console.log(scene, 'EXC', JSON.stringify(m.params.exceptionDetails).slice(0, 400));
              if (m.method === 'Runtime.consoleAPICalled' && m.params.type !== 'debug') console.log(scene, 'console', m.params.args.map(a => a.value ?? a.description).join(' ').slice(0, 300)); });
  await c.send('Runtime.enable'); await c.send('Page.enable');
  await c.send('Emulation.setDeviceMetricsOverride', { width: W, height: H, deviceScaleFactor: 2, mobile: false });
  await c.send('Page.navigate', { url: 'file://' + resolve(HERE, 'studio.html') + '?scene=' + scene.replace(/~/g, '&') });
  let st = null; for (let i = 0; i < 240; i++) { await sleep(500);
    const r = await c.send('Runtime.evaluate', { expression: 'JSON.stringify(document.body ? document.body.dataset : {})', returnByValue: true });
    st = JSON.parse(r.result.value || '{}'); if (st.ready) break; }
  await sleep(300);
  const shot = await c.send('Page.captureScreenshot', { format: 'png' });
  writeFileSync(resolve(outDir, scene.replace(/[~=]/g, '_') + '.png'), Buffer.from(shot.data, 'base64'));
  console.log(scene, W + 'x' + H, JSON.stringify(st));
  c.close(); await fetch(`http://127.0.0.1:${PORT}/json/close/${t.id}`);
}
chrome.kill();
