/* =================== ACCESS: team, roles, sign-in, permissions =================== */
/* Who may change what. Planning managers maintain the project's base data (BOQ, towers, floors &
   pours, monthly plan, workbook, periods, team). Site engineers enter the daily reports, optionally
   limited to their own towers. Anyone can open a read-only view. In this offline file the checks
   run in the browser, so they guide people rather than stop a determined one; the same roles map
   one-to-one onto SharePoint groups once the portal moves to a shared backend. */
const ROLE_LABEL = {pm:'Planning manager', engineer:'Site engineer', viewer:'View only'};
const PERMS = {
  base:['pm'], plan:['pm'], periods:['pm'], team:['pm'], import:['pm'],
  progress:['pm','engineer'], site:['pm','engineer'], cast:['pm','engineer'], send:['pm','engineer'],
  export:['pm','engineer','viewer'], view:['pm','engineer','viewer']
};
const PERM_ROWS = [
  ['Enter daily progress (whole tower and pours) and mark pours cast', 'progress', 'Only for the towers on their account, if any are set'],
  ['Enter labour, machinery, material & staff and site logs', 'site', 'Unless “site-wide reports” is switched off for them'],
  ['Send their entries to the planning manager as a file', 'send', ''],
  ['View every tab and export the DPR to Excel', 'export', ''],
  ['Change BOQ items, towers, lists, floors & pours and the project workbook', 'base', ''],
  ['Set and change the monthly plan', 'plan', ''],
  ['Close, reopen and roll over periods', 'periods', ''],
  ['Manage the team, import engineers’ entries and data backups', 'team', '']
];
let ME = null;   // the signed-in person: a team member, or the anonymous view-only visitor

function genId(prefix){ return (prefix||'')+Date.now().toString(36)+Math.random().toString(36).slice(2,8); }
function randomCode(n, alphabet){
  const a = alphabet || 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789', buf = new Uint32Array(n);
  crypto.getRandomValues(buf); return [...buf].map(x=> a[x % a.length]).join('');
}
function randomPin(){ return randomCode(4, '0123456789'); }
async function hashSecret(secret, salt){ return sha256Hex((salt? salt+':' : '')+secret); }
async function makeSecret(secret){ const s = randomCode(12); return {h: await hashSecret(secret, s), s}; }
async function checkSecret(rec, secret){ return !!rec && rec.h === await hashSecret(secret, rec.s||''); }

function teamUsers(){ return ((CFG.team && CFG.team.users) || []).filter(u=> u.active!==false); }
function userById(id){ return ((CFG.team && CFG.team.users) || []).find(u=> u.id===id) || null; }
function userName(id){ if(!id) return 'Someone'; if(id==='viewer') return 'Guest'; const u=userById(id); return u? u.name : 'A former team member'; }
function initials(name){ const p=String(name||'?').trim().split(/\s+/); return ((p[0]||'?')[0] + (p.length>1? p[p.length-1][0] : (p[0]||'?')[1]||'')).toUpperCase(); }
function activePMs(){ return teamUsers().filter(u=> u.role==='pm'); }
function avatarHtml(u, extra){ return `<span class="avatar ${u? u.role : 'viewer'}${extra? ' '+extra : ''}" aria-hidden="true">${escH(u? initials(u.name) : '—')}</span>`; }

function ensureProjectId(){ if(!CFG.projectId){ CFG.projectId = genId('prj-'); store.config = CFG; persist(); } }
/* Portals set up before v2.1 had one settings password: it becomes the planning manager's. */
function migrateLegacyPassword(){
  if(CFG.team || !(store.settingsAuth && store.settingsAuth.hash)) return false;
  CFG.team = { users:[{ id:genId('u-'), name:'Planning manager', role:'pm', towers:[], siteWide:true, pin:false,
    secret:{h:store.settingsAuth.hash, s:''}, active:true, created:new Date().toISOString(), migrated:true }], recovery:null };
  store.config = CFG; persist();
  return true;
}

/* ---------- session ---------- */
function sessionKey(){ return 'dpr_session_'+CFG.projectId; }
function rememberKey(){ return 'dpr_remember_'+CFG.projectId; }
const VIEWER = {id:'viewer', role:'viewer', name:'Guest'};
function readSession(){
  let id = null;
  try{ id = sessionStorage.getItem(sessionKey()); }catch(e){}
  if(!id){ try{ id = localStorage.getItem(rememberKey()); }catch(e){} }
  if(id==='viewer') return VIEWER;
  const u = id && userById(id);
  return (u && u.active!==false)? u : null;
}
function writeSession(id, remember, projectId){
  const pid = projectId || CFG.projectId;
  try{ sessionStorage.setItem('dpr_session_'+pid, id); }catch(e){}
  try{ if(remember) localStorage.setItem('dpr_remember_'+pid, id); else localStorage.removeItem('dpr_remember_'+pid); }catch(e){}
}
function isRemembered(){ try{ return !!localStorage.getItem(rememberKey()); }catch(e){ return false; } }
function clearSession(){
  try{ sessionStorage.removeItem(sessionKey()); }catch(e){}
  try{ localStorage.removeItem(rememberKey()); }catch(e){}
}
/* Starting a new project changes its id; keep the person signed in across that reload. */
function carrySession(newProjectId){ if(ME) writeSession(ME.id, isRemembered(), newProjectId); }

/* ---------- permissions ---------- */
function can(perm, tower){
  if(!ME) return false;
  if(!(PERMS[perm]||[]).includes(ME.role)) return false;
  if(ME.role==='engineer'){
    if(perm==='site' && ME.siteWide===false) return false;
    if((perm==='progress'||perm==='cast') && tower && (ME.towers||[]).length && !ME.towers.includes(tower)) return false;
  }
  return true;
}
function denyText(perm, tower){
  if(!ME) return 'Sign in first.';
  if(ME.role==='viewer') return 'You’re in view-only mode. Sign in from the menu at the top right to make entries.';
  if(perm==='progress' || perm==='cast') return tower? `${tower} isn’t one of your towers. Ask the planning manager to add it to your account.` : 'Your account can’t enter progress.';
  if(perm==='site') return 'Your account enters progress only. The planning manager can allow site-wide reports (labour, machinery, material & staff, site logs) for you.';
  return 'Only a planning manager can change this.';
}
function need(perm, tower){
  if(can(perm, tower)) return true;
  uiAlert(denyText(perm, tower), 'Not available for your account');
  return false;
}

/* ---------- who saved what, and when ---------- */
if(!store.stamps) store.stamps = {};
if(!store.activity) store.activity = [];
if(!store.tomb) store.tomb = {};
if(!store.sent) store.sent = {};
function nowIso(){ return new Date().toISOString(); }
function stamp(key){ const s = {by: ME? ME.id : '', at: nowIso()}; store.stamps[key] = s; return s; }
function stampOf(key){ return store.stamps[key] || null; }
function logAct(act, what){
  store.activity.push({at: nowIso(), by: ME? ME.id : '', act, what: what||''});
  if(store.activity.length > 3000) store.activity.splice(0, store.activity.length-3000);
}
/* Any change to base data: lets the planning manager see that engineers need a fresh setup file. */
function touchBase(){ CFG.updatedAt = nowIso(); store.config = CFG; }
function whenText(iso){
  if(!iso) return '';
  const d = new Date(iso);
  return d.toLocaleDateString('en-IN', {day:'numeric', month:'short'})+', '+d.toLocaleTimeString('en-IN', {hour:'numeric', minute:'2-digit'});
}
function savedByText(s){ return s? `Saved by ${userName(s.by)} · ${whenText(s.at)}` : ''; }
function byChip(s){ return s && s.by? `<span class="by-chip" title="${escH(savedByText(s))}">${escH(initials(userName(s.by)))}</span>` : ''; }
function setSavedBy(id, s, emptyText){
  const el = document.getElementById(id); if(!el) return;
  el.textContent = s? savedByText(s) : (emptyText||'');
  el.classList.toggle('empty', !s);
}

/* ---------- site-log rows: ids, who/when, deletions ---------- */
function canonRow(r){ return JSON.stringify(Object.keys(r).filter(k=> k!=='by' && k!=='at' && k!=='via').sort().map(k=> [k, r[k]])); }
function ensureLogIds(){
  let n = 0;
  ['concrete','rain','hindrance','bbs'].forEach(t=> (store[t]||[]).forEach(r=>{ if(!r.id){ r.id = genId('r-'); n++; } }));
  if(n) persist();
}
/* Gives new rows an id, stamps new or changed rows with the person and time, keeps the stamp of
   rows that didn't change, and notes rows that were removed so the removal can travel in files. */
function stampLogRows(prev, rows){
  const old = new Map((prev||[]).filter(r=> r.id).map(r=> [r.id, r]));
  const now = nowIso(), me = ME? ME.id : '';
  const out = rows.map(r=>{
    const base = Object.assign({}, r, {id: r.id || genId('r-')});
    const was = r.id && old.get(r.id);
    if(was && canonRow(was)===canonRow(base)) return Object.assign(base, {by: was.by||'', at: was.at||''}, was.via? {via: was.via} : {});
    return Object.assign(base, {by: me, at: now});
  });
  const keep = new Set(out.map(r=> r.id));
  const removed = (prev||[]).filter(r=> r.id && !keep.has(r.id)).map(r=> r.id);
  return {rows: out, commit(){ removed.forEach(id=>{ store.tomb[id] = {at: now, by: me}; }); }};
}
function decorateLogRow(tr, prefill){
  tr.dataset.id = (prefill && prefill.id) || '';
  const chip = prefill && prefill.by? byChip(prefill) : '';
  if(chip){ const td = tr.querySelector('td'); if(td) td.insertAdjacentHTML('beforeend', chip); }
}

/* ---------- files out: works in the claude.ai viewer (downloads capability) and as a local file ---------- */
async function saveFile(filename, data, mime){
  const blob = (data instanceof Blob)? data : new Blob([data], {type: mime || 'application/octet-stream'});
  let dl = null;
  try{ dl = await claude.use('downloads'); }catch(e){ dl = null; }
  if(dl){
    try{ await dl.save({filename, data: blob}); return 'saved'; }
    catch(e){
      if(e && e.code==='declined') return 'declined';
      if(e && (e.code==='rejected_extension' || e.code==='too_large' || e.code==='rate_limited')){ uiAlert((e.message||'The file wasn’t saved.'), 'File not saved'); return 'failed'; }
      console.error('downloads.save failed, trying a browser download instead:', e);
    }
  }
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a'); a.href = url; a.download = filename;
  document.body.appendChild(a); a.click(); a.remove();
  setTimeout(()=> URL.revokeObjectURL(url), 4000);
  return 'saved';
}
function fileStem(){ return (CFG.project.name||'DPR').replace(/[^a-zA-Z0-9]+/g,'_').replace(/^_+|_+$/g,'').slice(0,40) || 'DPR'; }
function pickFile(accept, multiple){
  return new Promise(resolve=>{
    const inp = document.createElement('input'); inp.type = 'file'; inp.accept = accept||''; inp.multiple = !!multiple; inp.style.display = 'none';
    inp.addEventListener('change', ()=>{ const f = [...inp.files]; inp.remove(); resolve(f); });
    document.body.appendChild(inp); inp.click();
  });
}
function readText(file){ return new Promise((res, rej)=>{ const r = new FileReader(); r.onload = ()=> res(r.result); r.onerror = ()=> rej(r.error); r.readAsText(file); }); }

/* ---------- applying access to the page ---------- */
function applyAccess(){
  const b = document.body;
  b.classList.toggle('no-base', !can('base'));
  b.classList.toggle('no-site', !can('site'));
  b.classList.toggle('no-entry', !can('progress'));
  b.classList.toggle('is-viewer', !ME || ME.role==='viewer');
  document.querySelectorAll('fieldset.pfs').forEach(fs=>{ fs.disabled = !can('site'); });
  document.querySelectorAll('.ro-banner').forEach(el=>{
    el.textContent = (!ME || ME.role==='viewer')? 'View only. Sign in from the menu at the top right to make entries.'
      : 'View only: your account enters progress, not site-wide reports. The planning manager can change that.';
  });
  renderUserChip();
  fillTowerSelect();
}
function fillTowerSelect(){
  const cur = towerSelect.value;
  const mine = (ME && ME.role==='engineer' && (ME.towers||[]).length)? ME.towers.filter(t=> CFG.towers.includes(t)) : null;
  const opt = t=> `<option value="${escH(t)}">${escH(t)}</option>`;
  if(mine && mine.length){
    const others = CFG.towers.filter(t=> !mine.includes(t));
    towerSelect.innerHTML = `<optgroup label="Your ${escH(T('zones').toLowerCase())}">${mine.map(opt).join('')}</optgroup>`
      + (others.length? `<optgroup label="Others (view only)">${others.map(opt).join('')}</optgroup>` : '');
    towerSelect.value = mine.includes(cur)? cur : mine[0];
  } else {
    towerSelect.innerHTML = CFG.towers.map(opt).join('');
    towerSelect.value = CFG.towers.includes(cur)? cur : (CFG.towers[0]||'');
  }
}
/* Terms used in labels. v2.1 keeps the building vocabulary; later versions make it configurable. */
function T(k){ const t = (CFG.terms||{}); const d = {zone:'Tower', zones:'Towers', level:'Level', pour:'Pour'}; return t[k] || d[k] || k; }

/* ---------- header: who's signed in ---------- */
function renderUserChip(){
  const chip = document.getElementById('userChip'); if(!chip) return;
  if(!ME){ chip.hidden = true; return; }
  chip.hidden = false;
  chip.innerHTML = avatarHtml(ME.role==='viewer'? null : ME) + `<span class="who"><b>${escH(ME.name)}</b><small>${escH(ROLE_LABEL[ME.role]||'')}</small></span>`;
  chip.title = ME.role==='viewer'? 'View only — open the menu to sign in' : 'Signed in as '+ME.name;
}
function closeUserMenu(){ const m = document.getElementById('userMenu'); if(m) m.remove(); document.removeEventListener('mousedown', userMenuOutside, true); }
function userMenuOutside(e){ const m = document.getElementById('userMenu'); if(m && !m.contains(e.target) && !e.target.closest('#userChip')) closeUserMenu(); }
function openUserMenu(){
  if(document.getElementById('userMenu')){ closeUserMenu(); return; }
  const chip = document.getElementById('userChip'), r = chip.getBoundingClientRect();
  const m = document.createElement('div'); m.id = 'userMenu'; m.className = 'menu-pop'; m.setAttribute('role','menu');
  const items = [];
  if(ME && ME.role!=='viewer'){
    items.push(['My account', ()=>{ openSettingsOverlay(); renderMyAccount(); }]);
    if(can('send')) items.push(['Send my entries…', sendEntriesDialog]);
    if(can('team')) items.push(['Team & access', ()=>{ settingsPane = 'team'; openSettings(); }]);
    items.push(['Switch user', ()=> signOut(true)]);
    items.push(['Sign out', ()=> signOut(false)]);
  } else {
    items.push(['Sign in', ()=> signOut(true)]);
  }
  m.innerHTML = items.map((it,i)=> `<button type="button" role="menuitem" data-i="${i}">${escH(it[0])}</button>`).join('');
  m.style.top = (r.bottom + 10)+'px';
  m.style.right = Math.max(12, window.innerWidth - r.right)+'px';
  document.body.appendChild(m);
  m.querySelectorAll('button').forEach(b=> b.addEventListener('click', ()=>{ closeUserMenu(); items[+b.dataset.i][1](); }));
  m.addEventListener('keydown', e=>{ if(e.key==='Escape'){ closeUserMenu(); chip.focus(); } });
  setTimeout(()=> document.addEventListener('mousedown', userMenuOutside, true), 0);
  const first = m.querySelector('button'); if(first) first.focus();
}

/* ---------- sign-in, first run, recovery ---------- */
const authFails = {};
const askedRecovery = new Set();
function authOverlay(){ return document.getElementById('authOverlay'); }
function hideAuth(){ const o = authOverlay(); o.hidden = true; o.innerHTML = ''; document.body.classList.remove('auth-open'); }
function authShell(inner){
  const o = authOverlay();
  const p = CFG.project||{};
  o.innerHTML = `<div class="auth-card">
    <div class="auth-head"><div class="brand-mark" aria-hidden="true"><i></i><i></i><i></i></div>
      <div><h1>Daily Progress Portal</h1><div class="sub">${escH(p.name||'Project')}${p.contractor? ' · '+escH(p.contractor) : ''}</div></div></div>
    ${inner}</div>`;
  o.hidden = false; document.body.classList.add('auth-open');
  return o;
}
function showWelcome(){
  const o = authShell(`
    <p class="auth-q">How will you use the portal on this device?</p>
    <div class="choice-cards">
      <div class="choice-card"><h3>I&rsquo;m the planning manager</h3><p>Set up the project and the team. You&rsquo;ll be able to change the BOQ, ${escH(T('zones').toLowerCase())}, floors &amp; pours, plan and periods.</p>
        <button class="btn blue" type="button" id="wcSetup">Set up as planning manager</button></div>
      <div class="choice-card"><h3>I&rsquo;m joining a project</h3><p>Open the setup file your planning manager sent, then sign in with the PIN they gave you.</p>
        <button class="btn secondary" type="button" id="wcJoin">Open setup file&hellip;</button></div>
    </div>
    <div class="auth-foot"><button class="linkbtn" type="button" id="wcView">Just look around (view only)</button></div>`);
  o.querySelector('#wcSetup').onclick = setupPlanningManager;
  o.querySelector('#wcJoin').onclick = joinFromSetupFile;
  o.querySelector('#wcView').onclick = ()=> signInAs(VIEWER, false);
}
async function setupPlanningManager(){
  const node = document.createElement('div');
  node.innerHTML = `<label class="dlg-field"><span>Your name</span><input id="pmName" type="text" autocomplete="name" placeholder="e.g. Anil Mehta"></label>
    <label class="dlg-field"><span>Choose a password (6+ characters)</span><input id="pmPw" type="password" autocomplete="new-password"></label>
    <label class="dlg-field"><span>Confirm password</span><input id="pmPw2" type="password" autocomplete="new-password"></label>`;
  const r = await uiDialog({title:'Set up the planning manager account', message:'You’ll sign in with this password. Engineers get their own PINs, which you set in Settings → Team & access.',
    node, focusEl: node.querySelector('#pmName'), cancelValue:false,
    buttons:[{label:'Cancel', value:false}, {label:'Create account', value:true, primary:true, validate:()=>{
      const n = node.querySelector('#pmName').value.trim(), a = node.querySelector('#pmPw').value, b = node.querySelector('#pmPw2').value;
      if(!n) return 'Enter your name.'; if(a.length<6) return 'Use at least 6 characters for the password.'; if(a!==b) return 'The passwords don’t match.'; return ''; }}]});
  if(r.value!==true) return;
  const u = {id:genId('u-'), name:node.querySelector('#pmName').value.trim(), role:'pm', towers:[], siteWide:true, pin:false,
    secret: await makeSecret(node.querySelector('#pmPw').value), active:true, created:nowIso()};
  CFG.team = {users:[u], recovery:null};
  ensureProjectId(); touchBase(); persist();
  askedRecovery.add(u.id);          // the first-run flow shows the code itself, right after sign-in
  await signInAs(u, false, true);
  await createRecoveryCode(true);
}
async function createRecoveryCode(first){
  const code = randomCode(4)+'-'+randomCode(4)+'-'+randomCode(4);
  CFG.team.recovery = await makeSecret(code.replace(/-/g,''));
  persist(); logAct('Team', 'New recovery code created');
  const node = document.createElement('div');
  node.innerHTML = `<div class="code-box" id="rcCode">${code}</div>
    <button class="btn secondary" type="button" id="rcCopy">Copy code</button>`;
  node.querySelector('#rcCopy').onclick = async ()=>{
    try{ await navigator.clipboard.writeText(code); flash('Recovery code copied'); }
    catch(e){ const rng = document.createRange(); rng.selectNodeContents(node.querySelector('#rcCode')); const sel = getSelection(); sel.removeAllRanges(); sel.addRange(rng); flash('Code selected — press Ctrl+C to copy'); }
  };
  await uiDialog({title: first? 'Save your recovery code' : 'New recovery code',
    message:'If a planning manager forgets their password, this code resets it. Keep it somewhere safe outside this portal; it isn’t shown again.'+(first? '' : ' The previous code no longer works.'),
    node, buttons:[{label:'I’ve saved it', value:true, primary:true}], cancelValue:true});
}
function showSignIn(){
  const users = teamUsers();
  const order = {pm:0, engineer:1};
  users.sort((a,b)=> (order[a.role]-order[b.role]) || a.name.localeCompare(b.name));
  const o = authShell(`
    <p class="auth-q">Who&rsquo;s signing in?</p>
    <div class="user-tiles">${users.map(u=> `<button type="button" class="user-tile" data-id="${escH(u.id)}">${avatarHtml(u)}<span class="nm">${escH(u.name)}</span><span class="rl">${escH(ROLE_LABEL[u.role])}</span></button>`).join('')}</div>
    <form class="auth-pin" id="authForm" hidden autocomplete="off">
      <div class="field"><label for="authSecret" id="authLabel">PIN</label><input type="password" id="authSecret" autocomplete="current-password"></div>
      <button class="btn blue" type="submit" id="authGo">Sign in</button>
      <label class="hint auth-remember"><input type="checkbox" id="authRemember"> Stay signed in on this device</label>
    </form>
    <div class="err-text" id="authErr" role="alert"></div>
    <div class="auth-foot">
      <button class="linkbtn" type="button" id="authView">View only (no sign-in)</button>
      <button class="linkbtn" type="button" id="authForgot">Forgot password?</button>
      <button class="linkbtn" type="button" id="authJoin">Open a setup file&hellip;</button>
    </div>`);
  let sel = null;
  const form = o.querySelector('#authForm'), inp = o.querySelector('#authSecret'), err = o.querySelector('#authErr');
  o.querySelectorAll('.user-tile').forEach(t=> t.addEventListener('click', ()=>{
    o.querySelectorAll('.user-tile').forEach(x=> x.classList.toggle('sel', x===t));
    sel = userById(t.dataset.id);
    form.hidden = false; err.textContent = '';
    o.querySelector('#authLabel').textContent = sel.pin? 'PIN' : 'Password';
    inp.value = ''; inp.inputMode = sel.pin? 'numeric' : 'text';
    inp.focus();
  }));
  form.addEventListener('submit', async e=>{
    e.preventDefault(); if(!sel) return;
    const f = authFails[sel.id] || {n:0, until:0};
    if(Date.now() < f.until){ err.textContent = `Too many attempts. Try again in ${Math.ceil((f.until-Date.now())/1000)} seconds.`; return; }
    if(await checkSecret(sel.secret, inp.value)){
      authFails[sel.id] = {n:0, until:0};
      await signInAs(sel, o.querySelector('#authRemember').checked, true);
    } else {
      f.n++; if(f.n>=5){ f.until = Date.now()+30000; f.n = 0; }
      authFails[sel.id] = f;
      err.textContent = (sel.pin? 'That PIN' : 'That password')+' isn’t right.'+(f.until>Date.now()? ' Wait 30 seconds before trying again.' : '');
      inp.select();
    }
  });
  o.querySelector('#authView').onclick = ()=> signInAs(VIEWER, false, true);
  o.querySelector('#authForgot').onclick = forgotPassword;
  o.querySelector('#authJoin').onclick = joinFromSetupFile;
  if(users.length===1) o.querySelector('.user-tile').click();
}
async function forgotPassword(){
  const pms = activePMs();
  const node = document.createElement('div');
  node.innerHTML = `${pms.length>1? `<label class="dlg-field"><span>Account</span><select id="fpUser">${pms.map(u=> `<option value="${escH(u.id)}">${escH(u.name)}</option>`).join('')}</select></label>` : ''}
    <label class="dlg-field"><span>Recovery code</span><input id="fpCode" type="text" autocomplete="off" placeholder="XXXX-XXXX-XXXX"></label>
    <label class="dlg-field"><span>New password (6+ characters)</span><input id="fpPw" type="password" autocomplete="new-password"></label>
    <label class="dlg-field"><span>Confirm new password</span><input id="fpPw2" type="password" autocomplete="new-password"></label>`;
  const noCode = !(CFG.team && CFG.team.recovery);
  const msg = noCode? 'No recovery code has been created on this device yet. Another planning manager can reset your password from Team & access, or you can open a setup file you exported earlier, which restores the team as it was then.'
    : 'Engineers who forget their PIN: ask the planning manager to set a new one. Planning managers: enter the recovery code you saved when the account was created.';
  if(noCode){ await uiAlert(msg, 'Reset a password'); return; }
  const r = await uiDialog({title:'Reset a planning manager password', message:msg, node, focusEl: node.querySelector('#fpCode'), cancelValue:false,
    buttons:[{label:'Cancel', value:false}, {label:'Reset password', value:true, primary:true, validate:()=>{
      const a = node.querySelector('#fpPw').value, b = node.querySelector('#fpPw2').value;
      if(!node.querySelector('#fpCode').value.trim()) return 'Enter the recovery code.';
      if(a.length<6) return 'Use at least 6 characters.'; if(a!==b) return 'The passwords don’t match.'; return ''; }}]});
  if(r.value!==true) return;
  const code = node.querySelector('#fpCode').value.toUpperCase().replace(/[^A-Z0-9]/g,'');
  if(!(await checkSecret(CFG.team.recovery, code))){ uiAlert('That recovery code isn’t right, so no password was changed.', 'Password not reset'); return; }
  const u = userById(node.querySelector('#fpUser')? node.querySelector('#fpUser').value : pms[0].id);
  u.secret = await makeSecret(node.querySelector('#fpPw').value); u.pin = false;
  store.activity.push({at: nowIso(), by: u.id, act:'Team', what:'Reset own password with the recovery code'});
  persist();
  await uiAlert(`Sign in as ${u.name} with the new password. For safety, create a new recovery code afterwards in Team & access.`, 'Password reset');
  showSignIn();
}
async function signInAs(u, remember, fresh){
  ME = u;
  writeSession(u.id, remember && u.id!=='viewer');
  hideAuth();
  if(fresh && u.id!=='viewer') logAct('Signed in', '');
  persist();
  applyAccess();
  renderAll();
  reloadLogs();
  if(fresh) flash(u.id==='viewer'? 'View only — nothing can be changed' : 'Signed in as '+u.name);
  if(u.role==='pm' && CFG.team && !CFG.team.recovery && !askedRecovery.has(u.id)){
    askedRecovery.add(u.id);
    if(await uiConfirm('Your account has no recovery code yet. Without one, a forgotten password can only be reset by another planning manager.', {title:'Create a recovery code?', ok:'Create code', cancel:'Later'})) await createRecoveryCode(false);
  }
}
async function signOut(toSignIn){
  if(typeof pgUnsaved==='function' && pgUnsaved()){
    if(!(await uiConfirm('You have unsaved pour entries. Signing out discards them.', {title:'Discard unsaved entries?', ok:'Discard and sign out', cancel:'Keep editing', danger:true}))) return;
    PG.key = '';
  }
  closeSettings(); closeUserMenu();
  if(ME && ME.id!=='viewer'){ logAct('Signed out', ''); persist(); }
  ME = null; clearSession();
  applyAccess(); renderAll();
  if(CFG.team) showSignIn(); else showWelcome();
}
function reloadLogs(){ loadConcrete(); loadRain(); loadHindrance(); loadBbs(); }

/* ---------- my account (everyone) ---------- */
function openSettingsOverlay(){ settingsOverlay.style.display = 'flex'; }
function renderMyAccount(){
  const u = ME; if(!u) return;
  const towers = u.role==='engineer'? ((u.towers||[]).length? u.towers.join(', ') : 'All '+T('zones').toLowerCase()) : '—';
  settingsPanel.innerHTML = `
    <button class="close-x" id="closeSettingsX" aria-label="Close">&times;</button>
    <h2>My account</h2>
    <div class="acct-head">${avatarHtml(u.role==='viewer'? null : u, 'lg')}<div><b>${escH(u.name)}</b><div class="hint" style="margin:2px 0 0;">${escH(ROLE_LABEL[u.role])}${u.role==='engineer'? ' · '+escH(T('zones'))+': '+escH(towers)+(u.siteWide===false? ' · progress only' : ' · site-wide reports') : ''}</div></div></div>
    ${u.role==='viewer'? `<div class="settings-section"><p class="hint" style="margin:0;">You’re browsing without signing in, so nothing can be changed.</p><button class="btn blue" type="button" id="maSignIn">Sign in</button></div>` : `
    <div class="settings-section">
      <h4>Send my entries</h4>
      <p class="hint">Save your daily entries as a file and send it to the planning manager (email, WhatsApp or a shared folder). They import it into the master copy; sending the same days again is safe.</p>
      <button class="btn blue" type="button" id="maSend">Send my entries&hellip;</button>
      ${store.sent[u.id]? `<span class="hint" style="margin-left:10px;">Last sent ${escH(whenText(store.sent[u.id].at))} (up to ${escH(store.sent[u.id].to)})</span>` : ''}
    </div>
    <div class="settings-section">
      <h4>Project setup on this device</h4>
      <p class="hint">When the planning manager changes the BOQ, plan, pours or team, they send a new setup file. Open it here; your entries are kept.</p>
      <button class="btn secondary" type="button" id="maSetup">Open setup file&hellip;</button>
      <span class="hint" style="margin-left:10px;">Setup on this device: ${escH(CFG.updatedAt? whenText(CFG.updatedAt) : 'not dated')}</span>
    </div>
    <div class="settings-section">
      <h4>Sign-in</h4>
      <button class="btn secondary" type="button" id="maPw">Change my ${u.pin? 'PIN' : 'password'}</button>
      <button class="btn secondary" type="button" id="maOut">Sign out</button>
    </div>`}`;
  const b = id=> document.getElementById(id);
  b('closeSettingsX').onclick = closeSettings;
  if(b('maSignIn')) b('maSignIn').onclick = ()=> signOut(true);
  if(b('maSend')) b('maSend').onclick = sendEntriesDialog;
  if(b('maSetup')) b('maSetup').onclick = joinFromSetupFile;
  if(b('maPw')) b('maPw').onclick = changeMyPassword;
  if(b('maOut')) b('maOut').onclick = ()=> signOut(false);
}
async function changeMyPassword(){
  const u = ME, word = u.pin? 'PIN' : 'password', min = u.pin? 4 : 6;
  const r = await uiDialog({title:'Change my '+word, cancelValue:false,
    inputs:[{label:'Current '+word, type:'password'}, {label:'New '+word, type:'password'}, {label:'Confirm new '+word, type:'password'}],
    buttons:[{label:'Cancel', value:false}, {label:'Change '+word, value:true, primary:true, validate:v=>{
      if(!v[0]) return 'Enter your current '+word+'.';
      if(v[1].length<min) return `Use at least ${min} ${u.pin? 'digits' : 'characters'}.`;
      if(u.pin && !/^\d+$/.test(v[1])) return 'A PIN uses digits only.';
      if(v[1]!==v[2]) return 'The new '+word+'s don’t match.'; return ''; }}]});
  if(r.value!==true) return;
  if(!(await checkSecret(u.secret, r.inputs[0]))){ uiAlert('Your current '+word+' isn’t right, so nothing was changed.', word.charAt(0).toUpperCase()+word.slice(1)+' not changed'); return; }
  u.secret = await makeSecret(r.inputs[1]);
  logAct('Team', 'Changed own '+word); persist();
  flash(word.charAt(0).toUpperCase()+word.slice(1)+' changed');
}

/* ---------- start ---------- */
function bootAccess(){
  ensureProjectId();
  migrateLegacyPassword();
  ensureLogIds();
  ME = CFG.team? readSession() : null;
  applyAccess();
  if(!CFG.team) showWelcome();
  else if(!ME) showSignIn();
}
