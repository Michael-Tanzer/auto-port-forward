HTML_PAGE = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Auto Port Forward</title>
<link rel="icon" type="image/svg+xml" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'><rect width='64' height='64' rx='12' fill='%231a1a1a'/><rect x='14' y='16' width='8' height='32' rx='2' fill='%234caf50'/><rect x='42' y='16' width='8' height='32' rx='2' fill='%234caf50'/><polygon points='26,26 38,32 26,38' fill='%234caf50'/></svg>">
<style>
  :root {
    --bg: #0c0c0c; --card: #141414; --card-border: #222; --item: #1c1c1c; --item-border: #2a2a2a;
    --text: #fff; --muted: #8e8e8e; --dim: #555;
    --green: #3ab159; --green-bg: rgba(58,177,89,0.1); --green-border: #245a33;
    --red: #e5484d; --red-bg: rgba(229,72,77,0.1);
    --accent: #3ab159; --radius: 12px;
    --mono: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, Courier, monospace;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background: var(--bg); color: var(--text); padding: 48px 24px; max-width: 760px; margin: 0 auto; }

  /* Header */
  header { display: flex; align-items: center; gap: 12px; margin-bottom: 32px; }
  .logo { display: flex; gap: 4px; background: var(--card); padding: 6px 8px; border-radius: 6px; border: 1px solid var(--card-border); }
  .logo-bar { width: 4px; height: 16px; background: var(--green); border-radius: 2px; }
  .logo-bar:last-child { height: 12px; margin-top: 4px; }
  header h1 { font-size: 18px; font-weight: 600; letter-spacing: -0.3px; }

  /* Sections */
  section { background: var(--card); border: 1px solid var(--card-border); border-radius: var(--radius); padding: 24px; margin-bottom: 24px; }
  .section-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
  .section-head h2 { font-size: 12px; font-weight: 500; color: var(--muted); text-transform: uppercase; letter-spacing: 0.5px; }

  /* Add button */
  .btn-add { display: inline-flex; align-items: center; gap: 6px; padding: 4px 12px; background: transparent; border: 1px solid var(--green-border); color: var(--green); border-radius: 4px; font-size: 13px; font-weight: 500; cursor: pointer; font-family: inherit; transition: background 0.15s; }
  .btn-add:hover { background: var(--green-bg); }
  .btn-add svg { width: 14px; height: 14px; }

  /* Text action links */
  .actions { display: flex; gap: 16px; font-size: 13px; font-weight: 500; flex-shrink: 0; }
  .act { cursor: pointer; color: var(--muted); transition: color 0.15s; background: none; border: none; padding: 0; font: inherit; font-size: 13px; font-weight: 500; }
  .act:hover { color: var(--text); }
  .act-del { color: var(--red); }
  .act-del:hover { color: #ff6b6b; }

  /* Connected list — fused items with rounded ends */
  .item-list { display: flex; flex-direction: column; gap: 0; }
  .item-list > * { border-radius: 0; border-bottom: 1px solid var(--item-border); }
  .item-list > *:first-child { border-radius: 6px 6px 0 0; }
  .item-list > *:last-child { border-radius: 0 0 6px 6px; border-bottom: none; }
  .item-list > *:only-child { border-radius: 6px; }

  /* SSH rows */
  .ssh-row { display: flex; justify-content: space-between; align-items: center; background: var(--item); border: 1px solid var(--item-border); border-bottom: none; padding: 12px 16px; }
  .item-list > .ssh-row:last-child { border-bottom: 1px solid var(--item-border); }
  .ssh-info { display: flex; flex-direction: column; gap: 4px; min-width: 0; flex: 1; }
  .item-name { font-size: 14px; font-weight: 600; }
  .mono { font-family: var(--mono); color: var(--muted); font-size: 13px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

  /* Tunnel rows — 3-column grid: info | badge (100px) | actions */
  .tunnel-row { display: grid; grid-template-columns: minmax(0, 1fr) 100px auto; align-items: center; gap: 16px; background: var(--item); border: 1px solid var(--item-border); border-bottom: none; border-left: 3px solid var(--green); padding: 12px 16px; }
  .item-list > .tunnel-row:last-child { border-bottom: 1px solid var(--item-border); }
  .tunnel-row.offline { border-left-color: var(--muted); }
  .tunnel-row.error { border-left-color: var(--red); }
  .tunnel-info { display: flex; flex-direction: column; gap: 4px; min-width: 0; }

  /* Status badge */
  .badge { display: inline-flex; align-items: center; gap: 6px; padding: 2px 8px; border-radius: 12px; font-size: 12px; font-weight: 500; white-space: nowrap; justify-self: start; }
  .badge-green { background: var(--green-bg); color: var(--green); }
  .badge-red { background: var(--red-bg); color: var(--red); }
  .badge-gray { background: rgba(142,142,142,0.1); color: var(--muted); }
  .dot { width: 6px; height: 6px; border-radius: 50%; flex-shrink: 0; }
  .dot-green { background: var(--green); animation: pulse 2s infinite; }
  .dot-red { background: var(--red); }
  .dot-gray { background: var(--muted); }
  @keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.4; } }

  /* Forms */
  .form-panel { background: var(--item); border: 1px solid var(--item-border); border-radius: 6px; padding: 16px; margin-top: 12px; animation: slideDown 0.15s ease-out; }
  @keyframes slideDown { from { opacity: 0; transform: translateY(-6px); } to { opacity: 1; transform: translateY(0); } }
  .form-grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px; }
  .form-group { display: flex; flex-direction: column; gap: 4px; }
  .form-group label { font-size: 11px; font-weight: 500; color: var(--muted); text-transform: uppercase; letter-spacing: 0.3px; }
  .form-group input, .form-group select { width: 100%; background: var(--bg); border: 1px solid var(--card-border); border-radius: 6px; padding: 8px 10px; color: var(--text); font-family: inherit; font-size: 13px; transition: border-color 0.15s; outline: none; }
  .form-group input:focus, .form-group select:focus { border-color: var(--accent); }
  .form-group input:disabled { opacity: 0.4; }
  .form-group select { appearance: none; background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' fill='%23888' viewBox='0 0 16 16'%3E%3Cpath d='M8 11L3 6h10z'/%3E%3C/svg%3E"); background-repeat: no-repeat; background-position: right 8px center; padding-right: 28px; }
  .form-actions { display: flex; gap: 8px; margin-top: 14px; }
  .form-actions button { font-family: inherit; border-radius: 4px; padding: 6px 16px; font-size: 13px; font-weight: 500; cursor: pointer; border: 1px solid; transition: all 0.15s; }
  .btn-save { background: var(--green-bg); color: var(--green); border-color: var(--green-border); }
  .btn-save:hover { background: rgba(58,177,89,0.2); }
  .btn-cancel { background: transparent; color: var(--muted); border-color: transparent; }
  .btn-cancel:hover { color: var(--text); }
  .cb-group { display: flex; align-items: center; gap: 6px; font-size: 13px; color: var(--muted); align-self: end; padding-bottom: 5px; }
  .cb-group input[type="checkbox"] { accent-color: var(--accent); }

  .empty { color: var(--dim); font-size: 13px; padding: 4px 0; }
  #error-banner { display: none; background: var(--red-bg); color: var(--red); border: 1px solid rgba(229,72,77,0.25); padding: 10px 14px; border-radius: 8px; margin-bottom: 16px; font-size: 13px; }
  .hidden { display: none !important; }
</style>
</head>
<body>

<header>
  <div class="logo"><div class="logo-bar"></div><div class="logo-bar"></div></div>
  <h1>Auto Port Forward</h1>
</header>

<div id="error-banner"></div>

<section>
  <div class="section-head">
    <h2>SSH Connections</h2>
    <button class="btn-add" onclick="toggleSshForm()">
      <svg viewBox="0 0 16 16" fill="currentColor"><path d="M8 2a1 1 0 011 1v4h4a1 1 0 110 2H9v4a1 1 0 11-2 0V9H3a1 1 0 110-2h4V3a1 1 0 011-1z"/></svg>
      Add
    </button>
  </div>
  <div id="ssh-list" class="item-list item-list"></div>
  <div id="ssh-form" class="hidden">
    <div class="form-panel">
      <div class="form-grid">
        <div class="form-group"><label>Name</label><input id="sf-name" placeholder="my-server"></div>
        <div class="form-group"><label>Host</label><input id="sf-host" placeholder="192.168.1.100"></div>
        <div class="form-group"><label>Port</label><input id="sf-port" type="number" value="22"></div>
        <div class="form-group"><label>Username</label><input id="sf-user" placeholder="root"></div>
        <div class="form-group"><label>Key file</label><input id="sf-key" placeholder="~/.ssh/id_rsa"></div>
        <div class="form-group"><label>Password</label><input id="sf-pass" type="password" placeholder="optional"></div>
      </div>
      <div class="form-actions">
        <button class="btn-save" onclick="saveSsh()">Save</button>
        <button class="btn-cancel" onclick="toggleSshForm()">Cancel</button>
      </div>
    </div>
  </div>
</section>

<section>
  <div class="section-head">
    <h2>Tunnels</h2>
    <button class="btn-add" onclick="toggleTunnelForm()">
      <svg viewBox="0 0 16 16" fill="currentColor"><path d="M8 2a1 1 0 011 1v4h4a1 1 0 110 2H9v4a1 1 0 11-2 0V9H3a1 1 0 110-2h4V3a1 1 0 011-1z"/></svg>
      Add
    </button>
  </div>
  <div id="tunnel-list" class="item-list item-list"></div>
  <div id="tunnel-form" class="hidden">
    <div class="form-panel">
      <div class="form-grid">
        <div class="form-group"><label>Name</label><input id="tf-name" placeholder="my-db"></div>
        <div class="form-group"><label>SSH Connection</label><select id="tf-ssh"></select></div>
        <div class="form-group"><label>Remote host</label><input id="tf-rhost" value="localhost"></div>
        <div class="form-group"><label>Remote port</label><input id="tf-rport" type="number" placeholder="5432"></div>
        <div class="form-group"><label>Local port</label><input id="tf-lport" type="number" placeholder="5432"></div>
        <div class="cb-group"><input type="checkbox" id="tf-enabled" checked> Auto-start</div>
      </div>
      <div class="form-actions">
        <button class="btn-save" onclick="saveTunnel()">Save</button>
        <button class="btn-cancel" onclick="toggleTunnelForm()">Cancel</button>
      </div>
    </div>
  </div>
</section>

<script>
const $ = s => document.querySelector(s);
let editingSsh = null, editingTunnel = null;

function showError(msg) {
  const b = $('#error-banner');
  b.textContent = msg; b.style.display = 'block';
  setTimeout(() => b.style.display = 'none', 5000);
}

async function api(path, opts = {}) {
  try {
    const res = await fetch(path, {
      headers: { 'Content-Type': 'application/json' }, ...opts,
      body: opts.body ? JSON.stringify(opts.body) : undefined,
    });
    const data = await res.json();
    if (!res.ok) { showError(data.error || 'Request failed'); return null; }
    return data;
  } catch (e) { showError(e.message); return null; }
}

// --- SSH ---
async function loadSsh() {
  const data = await api('/api/ssh');
  if (!data) return;
  const el = $('#ssh-list');
  const names = Object.keys(data);
  if (names.length === 0) { el.innerHTML = '<div class="empty">No connections yet.</div>'; return; }
  el.innerHTML = names.map(name => {
    const c = data[name];
    return `<div class="ssh-row">
      <div class="ssh-info">
        <span class="item-name">${esc(name)}</span>
        <span class="mono">${esc(c.username || '')}@${esc(c.host)}:${c.port || 22}</span>
      </div>
      <div class="actions">
        <button class="act" onclick="editSsh('${esc(name)}')">Edit</button>
        <button class="act act-del" onclick="deleteSsh('${esc(name)}')">Del</button>
      </div>
    </div>`;
  }).join('');
  populateSshDropdown(names);
}

function populateSshDropdown(names) {
  const sel = $('#tf-ssh'); const cur = sel.value;
  sel.innerHTML = names.map(n => `<option value="${esc(n)}">${esc(n)}</option>`).join('');
  if (cur && names.includes(cur)) sel.value = cur;
}

function toggleSshForm(show) {
  const f = $('#ssh-form');
  const visible = show !== undefined ? show : f.classList.contains('hidden');
  f.classList.toggle('hidden', !visible);
  if (!visible) { editingSsh = null; clearSshForm(); }
}

function clearSshForm() {
  $('#sf-name').value = ''; $('#sf-host').value = ''; $('#sf-port').value = '22';
  $('#sf-user').value = ''; $('#sf-key').value = ''; $('#sf-pass').value = '';
  $('#sf-name').disabled = false;
}

async function editSsh(name) {
  const data = await api('/api/ssh');
  if (!data || !data[name]) return;
  const c = data[name]; editingSsh = name;
  $('#sf-name').value = name; $('#sf-name').disabled = true;
  $('#sf-host').value = c.host || ''; $('#sf-port').value = c.port || 22;
  $('#sf-user').value = c.username || ''; $('#sf-key').value = c.key_file || '';
  $('#sf-pass').value = c.password || '';
  toggleSshForm(true);
}

async function saveSsh() {
  const name = editingSsh || $('#sf-name').value.trim();
  if (!name) { showError('Name is required'); return; }
  const body = {
    host: $('#sf-host').value.trim(), port: parseInt($('#sf-port').value) || 22,
    username: $('#sf-user').value.trim(), key_file: $('#sf-key').value.trim(),
    password: $('#sf-pass').value,
  };
  if (!body.password) delete body.password;
  if (!body.key_file) delete body.key_file;
  await api(`/api/ssh/${encodeURIComponent(name)}`, { method: 'PUT', body });
  toggleSshForm(false); loadSsh();
}

async function deleteSsh(name) {
  if (!confirm(`Delete SSH connection "${name}"?`)) return;
  await api(`/api/ssh/${encodeURIComponent(name)}`, { method: 'DELETE' }); loadSsh();
}

// --- Tunnels ---
async function loadTunnels() {
  const data = await api('/api/tunnels');
  if (!data) return;
  const el = $('#tunnel-list');
  if (data.length === 0) { el.innerHTML = '<div class="empty">No tunnels yet.</div>'; return; }
  el.innerHTML = data.map(t => {
    const st = t.status || 'disconnected';
    const isConn = st === 'connected';
    const isErr = st.startsWith('error');
    const rowCls = isConn ? '' : isErr ? 'error' : 'offline';
    const badgeCls = isConn ? 'badge-green' : isErr ? 'badge-red' : 'badge-gray';
    const dotCls = isConn ? 'dot-green' : isErr ? 'dot-red' : 'dot-gray';
    const label = isConn ? 'Connected' : isErr ? 'Error' : 'Offline';
    const errDetail = isErr ? st.replace('error: ', '') : '';
    return `<div class="tunnel-row ${rowCls}">
      <div class="tunnel-info">
        <span class="item-name">${esc(t.name)}</span>
        <span class="mono">:${t.local_port} \\u2192 ${esc(t.remote_host || 'localhost')}:${t.remote_port} via ${esc(t.ssh)}</span>
      </div>
      <div class="badge ${badgeCls}" ${errDetail ? `title="${esc(errDetail)}"` : ''}>
        <span class="dot ${dotCls}"></span>${label}
      </div>
      <div class="actions">
        ${isConn
          ? `<button class="act" onclick="stopTunnel('${esc(t.name)}')">Stop</button>`
          : `<button class="act" onclick="startTunnel('${esc(t.name)}')">Start</button>`}
        <button class="act" onclick="editTunnel('${esc(t.name)}')">Edit</button>
        <button class="act act-del" onclick="deleteTunnel('${esc(t.name)}')">Del</button>
      </div>
    </div>`;
  }).join('');
}

function toggleTunnelForm(show) {
  const f = $('#tunnel-form');
  const visible = show !== undefined ? show : f.classList.contains('hidden');
  f.classList.toggle('hidden', !visible);
  if (!visible) { editingTunnel = null; clearTunnelForm(); }
}

function clearTunnelForm() {
  $('#tf-name').value = ''; $('#tf-rhost').value = 'localhost';
  $('#tf-rport').value = ''; $('#tf-lport').value = ''; $('#tf-enabled').checked = true;
  $('#tf-name').disabled = false;
}

async function editTunnel(name) {
  const data = await api('/api/tunnels');
  if (!data) return;
  const t = data.find(x => x.name === name);
  if (!t) return; editingTunnel = name;
  $('#tf-name').value = t.name; $('#tf-name').disabled = true;
  $('#tf-ssh').value = t.ssh; $('#tf-rhost').value = t.remote_host || 'localhost';
  $('#tf-rport').value = t.remote_port; $('#tf-lport').value = t.local_port;
  $('#tf-enabled').checked = t.enabled !== false;
  toggleTunnelForm(true);
}

async function saveTunnel() {
  const name = editingTunnel || $('#tf-name').value.trim();
  if (!name) { showError('Name is required'); return; }
  const body = {
    name, ssh: $('#tf-ssh').value, remote_host: $('#tf-rhost').value.trim(),
    remote_port: parseInt($('#tf-rport').value), local_port: parseInt($('#tf-lport').value),
    enabled: $('#tf-enabled').checked,
  };
  if (editingTunnel) {
    await api(`/api/tunnels/${encodeURIComponent(name)}`, { method: 'PUT', body });
  } else {
    await api('/api/tunnels', { method: 'POST', body });
  }
  toggleTunnelForm(false); loadTunnels();
}

async function deleteTunnel(name) {
  if (!confirm(`Delete tunnel "${name}"?`)) return;
  await api(`/api/tunnels/${encodeURIComponent(name)}`, { method: 'DELETE' }); loadTunnels();
}

async function startTunnel(name) {
  await api(`/api/tunnels/${encodeURIComponent(name)}/start`, { method: 'POST' }); loadTunnels();
}

async function stopTunnel(name) {
  await api(`/api/tunnels/${encodeURIComponent(name)}/stop`, { method: 'POST' }); loadTunnels();
}

function esc(s) { const d = document.createElement('div'); d.textContent = String(s); return d.innerHTML; }

loadSsh(); loadTunnels();
setInterval(loadTunnels, 5000);
</script>
</body>
</html>
"""
