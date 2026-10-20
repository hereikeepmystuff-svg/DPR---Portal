/* =================== SHAREPOINT SYNC (v3.0) =================== */
/* With sync on, one SharePoint folder holds the project, and every device keeps a full copy:
     dpr-project.json                    the setup (BOQ, areas, plan, periods, team); planning managers write it
     dpr-workbook.xlsx                   the project's DPR workbook, if one is imported
     entries/<month>__<device>.json      what was entered on each device, one file per month
   A device uploads only what was entered (or imported from files) on it, and merges everyone else's files
   with the same rules as entries files: the newest version of each record wins, removals travel, nothing is
   counted twice. Records that arrived by sync carry via:'sync' and are never sent back.
   People sign in with their Microsoft 365 work account: OAuth 2.0 authorization code with PKCE, straight
   against Microsoft's endpoints, so the portal stays one file with no extra library. SharePoint's own
   permissions decide who may read the folder and who may write to it. */

const SYNC_FORMAT = 1;
const SP_FILES = {project:'dpr-project.json', workbook:'dpr-workbook.xlsx', entries:'entries', readme:'About these files.txt'};
const MS_SCOPES = 'openid profile email offline_access https://graph.microsoft.com/Files.ReadWrite.All';
const XLSX_TYPE = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet';
const BUILD_SYNC = Object.assign({}, (FACTORY && FACTORY.sync) || {});   // tools/build.py --ms-client-id, --ms-tenant, --portal-url
const MS_AUTH_KEY = 'dpr_ms_auth', MS_PENDING_KEY = 'dpr_ms_pending';
let SYNC_OVERRIDE = null;      // connection details while connecting or joining, before they are in the setup
let SYNC_APPLYING = false;     // changes made by the sync itself don't trigger another upload
let SYNC_NEEDS_RENDER = false, SYNC_NEEDS_RELOAD = false;

function msEndpoints(){
  const t = window.__dprEndpoints || {};      // tests point the portal at a stand-in for Microsoft
  return {login: t.login || 'https://login.microsoftonline.com', graph: t.graph || 'https://graph.microsoft.com/v1.0'};
}
function syncConf(){
  const c = SYNC_OVERRIDE || CFG.sync || {};
  return {clientId: c.clientId || BUILD_SYNC.clientId || '', tenant: c.tenant || BUILD_SYNC.tenant || 'organizations',
    driveId: c.driveId || '', folderId: c.folderId || ''};
}
function syncOn(){ const c = syncConf(); return !!(CFG.sync && !CFG.sync.off && c.clientId && c.driveId && c.folderId); }
/* Microsoft sign-in needs a web address: a file opened from the computer, or the portal inside another page, can't. */
function syncWhyNot(){
  if(location.protocol==='file:') return 'file';
  if(IN_FRAME) return 'frame';
  if(!(window.crypto && crypto.subtle)) return 'crypto';
  return '';
}
function canSyncHere(){ return !syncWhyNot(); }
function syncWhereText(){
  return syncWhyNot()==='frame'? 'SharePoint sync works in the portal’s own web address or the Android app, not inside another page.'
    : 'SharePoint sync needs the portal’s web address or the Android app: Microsoft sign-in doesn’t work in a file opened from the computer. Everything else works here as before.';
}
function syncErr(kind, message, status, code){ const e = new Error(message); e.kind = kind; e.status = status || 0; e.code = code || ''; return e; }
function syncSleep(ms){ return new Promise(r=> setTimeout(r, ms)); }

/* ---------- Microsoft sign-in: authorization code with PKCE ---------- */
function b64url(bytes){ let s = ''; for(let i = 0; i < bytes.length; i++) s += String.fromCharCode(bytes[i]); return btoa(s).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,''); }
function b64urlBytes(s){ s = String(s).replace(/-/g,'+').replace(/_/g,'/'); while(s.length % 4) s += '='; const bin = atob(s), u = new Uint8Array(bin.length); for(let i = 0; i < bin.length; i++) u[i] = bin.charCodeAt(i); return u; }
function randomB64url(n){ const a = new Uint8Array(n); crypto.getRandomValues(a); return b64url(a); }
async function pkceChallenge(verifier){ return b64url(new Uint8Array(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(verifier)))); }
function jwtClaims(t){ try{ return JSON.parse(new TextDecoder().decode(b64urlBytes(String(t).split('.')[1]))); }catch(e){ return {}; } }
/* The address Microsoft sends the sign-in back to. It must be registered with the app exactly. */
function msRedirectUri(){
  let p = location.pathname;
  if(location.hostname!=='appassets.androidplatform.net') p = p.replace(/\/index\.html$/i, '/');
  return location.origin + p;
}
function msAuthRaw(){ try{ return JSON.parse(localStorage.getItem(MS_AUTH_KEY) || 'null'); }catch(e){ return null; } }
function msAuthSave(a){ try{ if(a) localStorage.setItem(MS_AUTH_KEY, JSON.stringify(a)); else localStorage.removeItem(MS_AUTH_KEY); }catch(e){} }
function msAccount(){ const a = msAuthRaw(), c = syncConf(); return (a && a.account && a.clientId===c.clientId && (a.access || a.refresh))? a.account : null; }
function msAuthorizeUrl(p, challenge, prompt, hint){
  const q = new URLSearchParams({client_id: p.clientId, response_type:'code', redirect_uri: p.redirect, response_mode:'fragment',
    scope: MS_SCOPES, state: p.state, code_challenge: challenge, code_challenge_method:'S256'});
  if(prompt) q.set('prompt', prompt);
  if(hint) q.set('login_hint', hint);
  return msEndpoints().login + '/' + encodeURIComponent(p.tenant) + '/oauth2/v2.0/authorize?' + q.toString();
}
/* Full-page sign-in. What to do afterwards (connect, join, resume) waits in the browser until the page comes back. */
async function msSignIn(next, opts){
  opts = opts || {};
  const c = Object.assign({}, syncConf(), opts.conf || {});
  if(!c.clientId) throw syncErr('config', 'The portal doesn’t know which app to sign in with yet: the app (client) ID is missing.');
  const p = {state: randomB64url(18), verifier: randomB64url(48), clientId: c.clientId, tenant: c.tenant || 'organizations',
    redirect: msRedirectUri(), next: next || 'resume', data: opts.data || null, at: Date.now()};
  const json = JSON.stringify(p);
  try{ sessionStorage.setItem(MS_PENDING_KEY, json); }catch(e){}
  try{ localStorage.setItem(MS_PENDING_KEY, json); }catch(e){}   // in case the app's page is rebuilt meanwhile
  const url = msAuthorizeUrl(p, await pkceChallenge(p.verifier), opts.prompt || 'select_account', opts.hint || '');
  if(window.DPRAndroid && typeof DPRAndroid.beginSignIn==='function'){ try{ DPRAndroid.beginSignIn(); }catch(e){} }
  location.assign(url);
}
async function msTokenRequest(tenant, params){
  let r;
  try{
    r = await fetch(msEndpoints().login + '/' + encodeURIComponent(tenant) + '/oauth2/v2.0/token',
      {method:'POST', headers:{'Content-Type':'application/x-www-form-urlencoded'}, body: new URLSearchParams(params).toString()});
  }catch(e){ throw syncErr('offline', 'No connection to Microsoft.'); }
  let j = {}; try{ j = await r.json(); }catch(e){}
  if(!r.ok){
    const again = /invalid_grant|interaction_required|login_required|consent_required/.test(j.error || '');
    throw syncErr(again? 'signin' : 'auth', msErrorText(j.error, j.error_description), r.status, j.error || '');
  }
  return j;
}
// every address the account goes by: a sign-in name (UPN) can differ from the work email the planning manager typed
function msNames(c){ return [...new Set([c.preferred_username, c.email, c.upn, c.unique_name].filter(Boolean).map(x=> String(x).trim().toLowerCase()))]; }
function msKeep(j, ctx){
  const prev = msAuthRaw() || {}, same = prev.clientId===ctx.clientId;
  const c = j.id_token? jwtClaims(j.id_token) : null;
  const a = {clientId: ctx.clientId, tenant: ctx.tenant,
    account: c? {name: c.name || '', username: String(c.preferred_username || c.email || c.upn || '').toLowerCase(), names: msNames(c), oid: c.oid || '', tid: c.tid || ''} : (same? prev.account : null),
    access: j.access_token || '', accessExp: Date.now() + Math.max(60, (+j.expires_in || 3600) - 120) * 1000,
    refresh: j.refresh_token || (same? prev.refresh : '') || ''};
  msAuthSave(a);
  return a;
}
async function msRedeem(code, p){
  return msKeep(await msTokenRequest(p.tenant, {client_id: p.clientId, grant_type:'authorization_code', code,
    redirect_uri: p.redirect, code_verifier: p.verifier, scope: MS_SCOPES}), p);
}
/* The page came back from Microsoft: finish the sign-in, then clear the reply from the address bar. */
async function msHandleRedirect(){
  const h = location.hash.replace(/^#/, '');
  if(!/(^|&)(code|error)=/.test(h) || !/(^|&)state=/.test(h)) return null;
  const q = new URLSearchParams(h);
  let p = null;
  try{ p = JSON.parse(sessionStorage.getItem(MS_PENDING_KEY) || 'null'); }catch(e){}
  if(!p || p.state!==q.get('state')){ try{ p = JSON.parse(localStorage.getItem(MS_PENDING_KEY) || 'null'); }catch(e){ p = null; } }
  try{ sessionStorage.removeItem(MS_PENDING_KEY); localStorage.removeItem(MS_PENDING_KEY); }catch(e){}
  history.replaceState(null, '', location.pathname + location.search);
  if(!p || p.state!==q.get('state') || Date.now() - (p.at || 0) > 30 * 60000)
    return {error:'state', message:'This sign-in reply doesn’t match a sign-in started on this device, so it was ignored. Try again.'};
  if(q.get('error')) return {error: q.get('error'), message: msErrorText(q.get('error'), q.get('error_description')), pending: p};
  try{ await msRedeem(q.get('code'), p); }
  catch(e){ return {error: e.code || e.kind, message: e.message, pending: p}; }
  return {ok:true, pending: p};
}
/* Daily renewal without a click: a hidden frame asks Microsoft for a new code using the browser's
   Microsoft session (refresh tokens for web pages last 24 hours). Fails quietly when a click is needed. */
function msSilent(){
  const a = msAuthRaw(), c = syncConf();
  if(!c.clientId || !(a && a.account && a.account.username) || !canSyncHere()) return Promise.resolve(false);
  return new Promise(async resolve=>{
    const p = {state: randomB64url(18), verifier: randomB64url(48), clientId: c.clientId, tenant: c.tenant, redirect: msRedirectUri()};
    const f = document.createElement('iframe');
    f.hidden = true; f.setAttribute('aria-hidden', 'true'); f.title = 'Microsoft sign-in';
    f.src = msAuthorizeUrl(p, await pkceChallenge(p.verifier), 'none', a.account.username);
    const t0 = Date.now();
    let done = false;
    const finish = ok=>{ if(done) return; done = true; clearInterval(iv); f.remove(); resolve(ok); };
    const iv = setInterval(()=>{
      let href = '';
      try{ href = f.contentWindow.location.href; }catch(e){ href = ''; }      // still at Microsoft
      if(href && href.indexOf(p.redirect)===0 && /[#&](code|error)=/.test(href)){
        clearInterval(iv);
        const q = new URLSearchParams(href.split('#')[1] || '');
        if(q.get('state')!==p.state || !q.get('code')){ finish(false); return; }
        msRedeem(q.get('code'), p).then(()=> finish(true), ()=> finish(false));
      } else if(Date.now() - t0 > 12000) finish(false);
    }, 150);
    document.body.appendChild(f);
  });
}
let msRenewing = null;
async function msAccessToken(){
  const c = syncConf(), a = msAuthRaw();
  if(!a || a.clientId!==c.clientId || !(a.access || a.refresh)) throw syncErr('signin', 'Sign in with Microsoft to sync.');
  if(a.access && Date.now() < a.accessExp) return a.access;
  if(!msRenewing) msRenewing = (async ()=>{
    try{
      if(a.refresh){
        try{ return msKeep(await msTokenRequest(a.tenant, {client_id: a.clientId, grant_type:'refresh_token', refresh_token: a.refresh, scope: MS_SCOPES}), a).access; }
        catch(e){ if(e.kind!=='signin') throw e; }
      }
      if(await msSilent()) return msAuthRaw().access;
      const b = msAuthRaw(); if(b){ b.access = ''; b.refresh = ''; msAuthSave(b); }
      throw syncErr('signin', 'The Microsoft sign-in on this device has expired.');
    } finally { msRenewing = null; }
  })();
  return msRenewing;
}
function msForgetAccess(){ const a = msAuthRaw(); if(a){ a.accessExp = 0; msAuthSave(a); } }
function msErrorText(code, desc){
  const d = String(desc || ''), has = n=> d.indexOf(n) >= 0;
  if(has('AADSTS65001') || code==='consent_required') return 'Your organisation hasn’t approved the DPR Portal app yet. IT needs to grant admin consent for it (see the IT steps in the SharePoint guide).';
  if(has('AADSTS50011')) return `This address isn’t registered with the app: ${msRedirectUri()}. IT needs to add it under Single-page application in the app’s Authentication settings.`;
  if(has('AADSTS9002326')) return `The app is registered as a web app. IT needs to register ${msRedirectUri()} under Single-page application instead.`;
  if(has('AADSTS700016')) return 'Microsoft doesn’t know that app (client) ID in your organisation. Check the ID with IT.';
  if(has('AADSTS50194')) return 'The app is registered for your organisation only, so the portal also needs its Directory (tenant) ID. The planning manager enters it with the app ID in Team & access (IT has it).';
  if(has('AADSTS90002') || has('AADSTS90014')) return 'Microsoft doesn’t know that directory (tenant). Check the tenant ID with IT.';
  if(has('AADSTS65004')) return 'The request for access was declined, so the portal can’t reach SharePoint.';
  if(has('AADSTS50020') || has('AADSTS50034')) return 'That account isn’t part of the organisation the app belongs to. Sign in with your work account.';
  if(has('AADSTS53003') || has('AADSTS53000')) return 'Your organisation’s access rules blocked the sign-in on this device. Ask IT whether this device or app needs to be allowed.';
  if(code==='access_denied') return 'The sign-in was cancelled.';
  if(code==='login_required' || code==='interaction_required') return 'Microsoft needs you to sign in again.';
  const line = d.split(/\r?\n/)[0].replace(/^AADSTS\d+:\s*/, '');
  return line || ('Microsoft didn’t accept the sign-in' + (code? ' (' + code + ')' : '') + '.');
}
/* Leaving for Microsoft's sign-in page drops anything half-typed, so offer to save it first. */
async function msSignInSaved(next, opts){
  if(!(await saveBeforeAction('what you send to SharePoint'))) return;
  try{ await msSignIn(next, opts); }catch(e){ uiAlert(e.message, 'Can’t sign in'); }
}
function msSignOut(everywhere){
  const a = msAuthRaw();
  msAuthSave(null);
  try{ sessionStorage.setItem('dpr_no_auto', '1'); }catch(e){}
  setSyncChip();
  if(everywhere && a && canSyncHere())
    location.assign(msEndpoints().login + '/' + encodeURIComponent(a.tenant || 'organizations') + '/oauth2/v2.0/logout?post_logout_redirect_uri=' + encodeURIComponent(msRedirectUri()));
}

/* ---------- Microsoft Graph: the SharePoint folder ---------- */
async function gx(method, path, opts){
  opts = opts || {};
  const url = /^https?:\/\//.test(path)? path : msEndpoints().graph + path;
  for(let attempt = 0; ; attempt++){
    const token = await msAccessToken();
    let r;
    try{ r = await fetch(url, {method, headers: Object.assign({Authorization: 'Bearer ' + token}, opts.headers || {}), body: opts.body, cache:'no-store'}); }
    catch(e){ throw syncErr('offline', 'No connection to SharePoint.'); }
    if(r.status===401 && attempt < 1){ msForgetAccess(); continue; }
    if((r.status===429 || r.status===503 || r.status===504) && attempt < 3){
      await syncSleep(Math.min(30, (+r.headers.get('Retry-After') || 0) || 2 * (attempt + 1)) * 1000);
      continue;
    }
    if(r.status===404 && opts.missingOk) return null;
    if(!r.ok){
      let j = {}; try{ j = await r.json(); }catch(e){}
      const e = (j && j.error) || {};
      const kind = r.status===401? 'signin' : r.status===403? 'denied' : r.status===404? 'missing' : r.status===412? 'conflict' : 'graph';
      throw syncErr(kind, e.message || ('SharePoint answered ' + r.status + '.'), r.status, e.code || '');
    }
    if(r.status===204) return null;
    return r.json();
  }
}
function spPath(rel){ return rel.split('/').map(encodeURIComponent).join('/'); }
function spItem(rel){ const c = syncConf(); return `/drives/${encodeURIComponent(c.driveId)}/items/${encodeURIComponent(c.folderId)}:/${spPath(rel)}:`; }
function spGet(rel){ return gx('GET', spItem(rel), {missingOk:true}); }
async function spList(rel){
  let url = spItem(rel) + '/children?$top=500', all = [];
  while(url){
    const j = await gx('GET', url, {missingOk:true});
    if(!j) return all;
    all = all.concat(j.value || []);
    url = j['@odata.nextLink'] || '';
  }
  return all;
}
function spPut(rel, body, type, ifMatch){
  const h = {'Content-Type': type};
  if(ifMatch) h['If-Match'] = ifMatch;
  return gx('PUT', spItem(rel) + '/content', {headers: h, body});
}
/* Files come back through their pre-signed download address, which browsers can fetch without a CORS pre-flight. */
async function spDownload(item, asBytes){
  let url = item && item['@microsoft.graph.downloadUrl'];
  if(!url){ const c = syncConf(); const it = await gx('GET', `/drives/${encodeURIComponent(c.driveId)}/items/${encodeURIComponent(item.id)}`); url = it && it['@microsoft.graph.downloadUrl']; }
  if(!url) throw syncErr('graph', 'SharePoint didn’t offer ' + (item.name || 'a file') + ' for download.');
  let r;
  try{ r = await fetch(url, {cache:'no-store'}); }catch(e){ throw syncErr('offline', 'No connection to SharePoint.'); }
  if(!r.ok) throw syncErr('graph', 'SharePoint couldn’t send ' + (item.name || 'a file') + ' (' + r.status + ').', r.status);
  return asBytes? new Uint8Array(await r.arrayBuffer()) : r.json();
}
function shareIdOf(url){ return 'u!' + btoa(unescape(encodeURIComponent(url))).replace(/=+$/,'').replace(/\//g,'_').replace(/\+/g,'-'); }
/* A folder's address from the browser, a "Copy link" link, or a library view (…/AllItems.aspx?id=/sites/…) all work. */
function cleanFolderLink(link){
  let u = String(link || '').trim();
  const m = u.match(/https?:\/\/[^\s"'<>]+/); if(m) u = m[0];
  try{
    const x = new URL(u), id = x.searchParams.get('id') || x.searchParams.get('RootFolder');
    if(id && /\.aspx$/i.test(x.pathname)) return x.origin + encodeURI(decodeURIComponent(id));
  }catch(e){}
  return u;
}
async function spResolveFolder(link){
  const url = cleanFolderLink(link);
  if(!/^https?:\/\/\S+$/.test(url)) throw syncErr('link', 'Paste the link of the SharePoint folder. It starts with https://.');
  let it;
  try{ it = await gx('GET', '/shares/' + shareIdOf(url) + '/driveItem', {headers:{Prefer:'redeemSharingLinkIfNecessary'}, missingOk:true}); }
  catch(e){ if(e.kind==='denied') throw syncErr('denied', 'Your account can’t open that folder. Ask its owner to share it with you, then try again.', 403); throw e; }
  if(!it) throw syncErr('missing', 'SharePoint couldn’t find that folder. Check the link, and that the folder is shared with your account.', 404);
  if(!it.folder) throw syncErr('link', 'That link opens a file. Copy the link of the folder itself.');
  return {driveId: (it.parentReference || {}).driveId || '', folderId: it.id, folderName: it.name || '', folderUrl: it.webUrl || url};
}

/* ---------- this device ---------- */
function deviceId(){
  let id = '';
  try{ id = localStorage.getItem('dpr_device_id') || ''; }catch(e){}
  if(!/^[a-z0-9]{6,}$/.test(id)){ id = 'd' + randomCode(11, 'abcdefghijkmnpqrstuvwxyz23456789'); try{ localStorage.setItem('dpr_device_id', id); }catch(e){} }
  return id;
}
/* What this device already knows of the folder, per project (kept apart from the project's data and backups). */
function syncStateKey(){ return 'dpr_sync_' + (CFG.projectId || ''); }
function syncStateFresh(){ return {seen:{}, pushed:{}, setupHash:'', setupETag:'', wbHash:'', wbETag:'', lastOk:'', error:null}; }
let SYNC_ST = null;
function syncState(){
  if(!SYNC_ST || SYNC_ST._key!==syncStateKey()){
    let s = null; try{ s = JSON.parse(localStorage.getItem(syncStateKey()) || 'null'); }catch(e){}
    SYNC_ST = Object.assign(syncStateFresh(), s || {}, {_key: syncStateKey()});
  }
  return SYNC_ST;
}
function syncSave(){ try{ const s = Object.assign({}, syncState()); delete s._key; localStorage.setItem(syncStateKey(), JSON.stringify(s)); }catch(e){} }
function syncReset(extra){ SYNC_ST = Object.assign(syncStateFresh(), extra || {}, {_key: syncStateKey()}); syncSave(); }
async function syncHash(x){ return sha256Hex(canonJSON(x)); }
async function bytesHash(u8){ const d = await crypto.subtle.digest('SHA-256', u8); return Array.from(new Uint8Array(d)).map(b=> b.toString(16).padStart(2,'0')).join(''); }

/* ---------- what this device sends: its own entries, by month ---------- */
function cameFromElsewhere(x){ return !!(x && (x.via==='sync' || x.via==='setup')); }
function syncOwnByMonth(){
  const out = {};
  const bucket = ym=> out[ym] || (out[ym] = {progressLoc:{}, labour:{}, labourCamp:{}, machinery:{}, material:{}, concrete:[], rain:[], hindrance:[], bbs:[], pourCast:{}, stamps:{}, tomb:{}});
  const ymOf = d=> /^\d{4}-\d{2}/.test(d || '')? String(d).slice(0, 7) : '';
  const keys = new Set([...Object.keys(store.progressLoc || {}), ...Object.keys(store.progress || {})]);
  keys.forEach(k=>{
    const ym = ymOf(k.slice(k.lastIndexOf('|') + 1)); if(!ym) return;
    let L = (store.progressLoc || {})[k];
    if(!L){ const rec = (store.progress || {})[k]; if(!rec) return; const vals = {}; Object.keys(rec).forEach(s=>{ const a = entryAch(rec, s); if(a) vals[s] = a; }); L = {'': vals}; }
    Object.keys(L).forEach(lid=>{
      const sk = 'p|' + k + '|' + lid, s = store.stamps[sk];
      if(cameFromElsewhere(s)) return;
      const b = bucket(ym); (b.progressLoc[k] = b.progressLoc[k] || {})[lid] = L[lid];
      if(s) b.stamps[sk] = s;
    });
  });
  [['labour','labour|'], ['labourCamp','labour|'], ['machinery','mach|'], ['material','mat|']].forEach(([src, sk])=>{
    Object.keys(store[src] || {}).forEach(d=>{
      const ym = ymOf(d), s = store.stamps[sk + d];
      if(!ym || cameFromElsewhere(s)) return;
      const b = bucket(ym); b[src][d] = store[src][d];
      if(s) b.stamps[sk + d] = s;
    });
  });
  LOG_TYPES.forEach(t=> (store[t] || []).forEach(r=>{
    if(!r || !r.id || cameFromElsewhere(r)) return;
    bucket(ymOf(logDate(t, r)) || ymOf(r.at) || 'undated')[t].push(r);
  }));
  Object.keys(store.pourCast || {}).forEach(pid=>{
    const c = store.pourCast[pid];
    if(!c || cameFromElsewhere(c)) return;
    const ym = ymOf(c.date) || ymOf(c.at); if(ym) bucket(ym).pourCast[pid] = c;
  });
  Object.keys(store.tomb || {}).forEach(id=>{
    const tb = store.tomb[id];
    if(!tb || cameFromElsewhere(tb)) return;
    const ym = ymOf(tb.at); if(ym) bucket(ym).tomb[id] = tb;
  });
  return out;
}
function syncSetupBody(){
  return {config: CFG, plan: store.plan || {}, planAuditLog: store.planAuditLog || [], labourPresets: store.labourPresets || [],
    periods: store.periods || {}, periodLog: store.periodLog || []};
}
function syncSetupFile(){
  return Object.assign({kind:'dpr-setup', format:1, sync: SYNC_FORMAT, app:'DPR Portal v' + APP_VERSION, projectId: CFG.projectId,
    projectName: CFG.project.name || '', exportedAt: nowIso(), by: ME && ME.id!=='viewer'? {id: ME.id, name: ME.name} : null}, syncSetupBody());
}
function syncEntryFileName(ym){ return ym + '__' + deviceId() + '.json'; }

/* ---------- receiving: setup, workbook, everyone's entries ---------- */
function applySetupFromSync(pkg){
  SYNC_APPLYING = true;
  try{
    store.config = pkg.config; CFG = store.config;
    applyPendingRenames();
    store.plan = pkg.plan || {}; store.planAuditLog = pkg.planAuditLog || []; store.labourPresets = pkg.labourPresets || [];
    store.periods = pkg.periods || {}; store.periodLog = pkg.periodLog || [];
    persist();
  } finally { SYNC_APPLYING = false; }
  SYNC_NEEDS_RELOAD = true;
}
async function syncPull(st, rep){
  // 1. the project setup
  const meta = await spGet(SP_FILES.project);
  if(meta && meta.eTag!==st.setupETag){
    const pkg = await spDownload(meta);
    if(!pkg || pkg.kind!=='dpr-setup' || !pkg.config || !pkg.config.items) throw syncErr('graph', 'The project file in SharePoint isn’t a DPR Portal setup.');
    if(pkg.projectId && pkg.projectId!==CFG.projectId) throw syncErr('project', `The SharePoint folder now holds a different project (“${pkg.projectName || '?'}”).`);
    const localHash = await syncHash(syncSetupBody());
    const unsentHere = can('base') && localHash!==st.setupHash;
    if(!unsentHere || (pkg.config.updatedAt || '') > (CFG.updatedAt || '')){
      const remote = {config: pkg.config, plan: pkg.plan || {}, planAuditLog: pkg.planAuditLog || [], labourPresets: pkg.labourPresets || [], periods: pkg.periods || {}, periodLog: pkg.periodLog || []};
      if(await syncHash(remote)!==localHash){ applySetupFromSync(pkg); rep.setupBy = (pkg.by && pkg.by.name) || 'a planning manager'; }
      st.setupHash = await syncHash(syncSetupBody());
    }
    st.setupETag = meta.eTag;
  }
  if(!meta && !can('base')) rep.waiting = true;
  // 2. the project workbook
  if(CFG.template){
    const wb = await spGet(SP_FILES.workbook);
    if(wb && wb.eTag!==st.wbETag){
      let unsent = false;
      if(can('base')){ try{ unsent = (await bytesHash(await loadTemplateBytes()))!==st.wbHash && !!st.wbHash; }catch(e){ unsent = false; } }
      if(!unsent){
        const bytes = await spDownload(wb, true);
        await TPL_DB.put('template', bytes);
        st.wbHash = await bytesHash(bytes);
      }
      st.wbETag = wb.eTag;
    }
  }
  // 3. everyone else's entries
  const mine = deviceId(), from = new Set();
  let n = 0;
  for(const f of await spList(SP_FILES.entries)){
    const m = /^(\d{4}-\d{2}|undated)__([a-z0-9]+)\.json$/i.exec(f.name || '');
    if(!m || !f.file || m[2]===mine || st.seen[f.name]===f.eTag) continue;
    const j = await spDownload(f);
    if(j && j.kind==='dpr-sync-entries' && j.projectId===CFG.projectId && j.data){
      SYNC_APPLYING = true;
      try{
        const t = mergeTotals(mergeEntries(renamedEntries(j.data, j.setupUpdatedAt), {via:'sync'}));
        const changed = t.added + t.updated + t.removed;
        if(changed){ n += changed; if(j.by && j.by.name) from.add(j.by.name); }
      } finally { SYNC_APPLYING = false; }
    }
    st.seen[f.name] = f.eTag;
  }
  if(n){ SYNC_APPLYING = true; try{ persist(); } finally { SYNC_APPLYING = false; } SYNC_NEEDS_RENDER = true; }
  rep.received = n; rep.from = [...from];
}

/* ---------- sending: setup and workbook (planning managers), this device's entries ---------- */
async function syncPush(st, rep){
  if(!ME || ME.id==='viewer') return;
  if(can('base')){
    const h = await syncHash(syncSetupBody());
    if(h!==st.setupHash){
      let res = null;
      try{ res = await spPut(SP_FILES.project, JSON.stringify(syncSetupFile()), 'application/json', st.setupETag || undefined); }
      catch(e){
        if(e.kind!=='conflict') throw e;
        // another planning manager saved the setup meanwhile: the newer setup wins
        const meta = await spGet(SP_FILES.project), pkg = meta && await spDownload(meta);
        if(pkg && (pkg.config.updatedAt || '') > (CFG.updatedAt || '')){
          applySetupFromSync(pkg); rep.setupBy = (pkg.by && pkg.by.name) || 'another planning manager';
          st.setupHash = await syncHash(syncSetupBody()); st.setupETag = meta.eTag;
        } else res = await spPut(SP_FILES.project, JSON.stringify(syncSetupFile()), 'application/json');
      }
      if(res){ st.setupETag = res.eTag; st.setupHash = await syncHash(syncSetupBody()); rep.sentSetup = true; }
    }
    if(CFG.template){
      let bytes = null; try{ bytes = await loadTemplateBytes(); }catch(e){ bytes = null; }
      if(bytes){
        const wh = await bytesHash(bytes);
        if(wh!==st.wbHash){ const res = await spPut(SP_FILES.workbook, bytes, XLSX_TYPE); st.wbETag = res && res.eTag; st.wbHash = wh; }
      }
    }
  }
  const months = syncOwnByMonth(), names = {};
  Object.keys(months).forEach(ym=> names[syncEntryFileName(ym)] = ym);
  // months this device sent before that hold nothing of its own any more are emptied, so old versions don't linger
  Object.keys(st.pushed).forEach(name=>{ if(!names[name] && name.endsWith('__' + deviceId() + '.json')) names[name] = name.split('__')[0]; });
  let sent = 0;
  for(const name of Object.keys(names).sort()){
    const data = months[names[name]] || {};
    const h = await syncHash(data);
    if(st.pushed[name]===h) continue;
    const body = JSON.stringify({kind:'dpr-sync-entries', format: SYNC_FORMAT, app:'DPR Portal v' + APP_VERSION, projectId: CFG.projectId,
      month: names[name], device: deviceId(), by:{id: ME.id, name: ME.name}, savedAt: nowIso(), setupUpdatedAt: CFG.updatedAt || '', data});
    const res = await spPut(SP_FILES.entries + '/' + name, body, 'application/json');
    st.pushed[name] = h;
    if(res && res.eTag) st.seen[name] = res.eTag;
    sent++;
  }
  rep.sent = sent;
}

/* ---------- running it ---------- */
let syncRun = null, syncAgain = false, syncTimer = 0;
function syncKick(ms){
  if(!syncOn() || !canSyncHere() || !msAccount()) return;
  clearTimeout(syncTimer);
  syncTimer = setTimeout(()=>{ syncNow(); }, ms===undefined? 3000 : ms);
}
async function syncNow(opts){
  opts = opts || {};
  if(!syncOn() || !canSyncHere()){ setSyncChip(); return false; }
  if(syncRun){ syncAgain = true; return syncRun; }
  syncRun = (async ()=>{
    const st = syncState(), rep = {};
    setSyncChip('busy');
    try{
      await syncPull(st, rep);
      await syncPush(st, rep);
      st.error = null; st.lastOk = nowIso();
    }catch(e){
      if(!e.kind) console.error('Sync failed:', e);
      st.error = {kind: e.kind || 'graph', message: e.message || String(e), status: e.status || 0, at: nowIso()};
    }
    syncSave();
    setSyncChip();
    if(rep.received && !rep.setupBy) flash(`Received ${rep.received} update${rep.received===1? '' : 's'}` + (rep.from.length? ' from ' + rep.from.join(', ') : ''));
    syncRefreshUI(rep);
    if(opts.announce && !st.error) flash(rep.sent || rep.sentSetup? 'Sent and synced with SharePoint' : 'Up to date with SharePoint');
    return !st.error;
  })();
  try{ return await syncRun; }
  finally{ syncRun = null; if(syncAgain){ syncAgain = false; syncKick(400); } }
}
/* New data is shown at once when nothing is half-typed; otherwise it waits for the person to finish. */
function syncIdle(){
  return !anyUnsaved() && !document.querySelector('.dlg-overlay') && settingsOverlay.style.display!=='flex' && authOverlay().hidden && !document.getElementById('syncBusy');
}
function syncRefreshUI(rep){
  rep = rep || {};
  if(!SYNC_NEEDS_RELOAD && !SYNC_NEEDS_RENDER) return;
  if(!syncIdle()){ setSyncChip(); return; }
  if(SYNC_NEEDS_RELOAD){ SYNC_NEEDS_RELOAD = false; reloadKeepingPlace('Project setup updated' + (rep.setupBy? ' by ' + rep.setupBy : '')); return; }
  SYNC_NEEDS_RENDER = false;
  renderAll(); reloadLogs(); refreshPourDatalist();
  if(document.getElementById('panel-structure') && document.getElementById('panel-structure').classList.contains('active')) renderStructure();
  setSyncChip();
}
/* Reloading picks up a new setup everywhere; the tab, day, area and scroll position come back with it. */
function reloadKeepingPlace(msg){
  const tab = document.querySelector('.tab.active');
  try{ sessionStorage.setItem('dpr_resume', JSON.stringify({tab: tab? tab.dataset.tab : '', date: dateInput.value, tower: towerSelect.value, y: window.scrollY, msg: msg || ''})); }catch(e){}
  location.reload();
}
function resumePlace(){
  let r = null;
  try{ r = JSON.parse(sessionStorage.getItem('dpr_resume') || 'null'); sessionStorage.removeItem('dpr_resume'); }catch(e){ r = null; }
  if(!r) return;
  if(r.date) dateInput.value = r.date;
  if(r.tower && [...towerSelect.options].some(o=> o.value===r.tower)) towerSelect.value = r.tower;
  if(r.date || r.tower) renderAll();
  const t = r.tab && document.querySelector(`.tab[data-tab="${r.tab}"]`);
  if(t && !t.classList.contains('active')) t.click();
  if(r.y) setTimeout(()=> window.scrollTo(0, r.y), 60);
  if(r.msg) flash(r.msg);
}

/* ---------- header: the sync light ---------- */
function hhmm(iso){ return new Date(iso).toLocaleTimeString('en-IN', {hour:'numeric', minute:'2-digit'}); }
function setSyncChip(state){
  const chip = document.getElementById('syncChip'); if(!chip) return;
  if(!syncOn()){ chip.hidden = true; return; }
  chip.hidden = false;
  const st = syncState(), e = st.error;
  let cls = 'ok', text = 'Synced', title = 'In step with SharePoint';
  if(state==='busy'){ cls = 'busy'; text = 'Syncing…'; title = 'Sending and receiving entries'; }
  else if(!canSyncHere()){ cls = 'off'; text = 'Not syncing here'; title = syncWhereText(); }
  else if(!msAccount()){ cls = 'warn'; text = 'Sign in to sync'; title = 'Sign in with Microsoft to send and receive entries'; }
  else if(e){
    cls = (e.kind==='offline' || e.kind==='signin')? 'warn' : 'bad';
    text = {offline:'Offline', signin:'Sign in to sync', denied:'No access', missing:'Folder missing'}[e.kind] || 'Sync problem';
    title = syncAdvice(e);
  }
  else if(SYNC_NEEDS_RELOAD){ cls = 'note'; text = 'Update ready'; title = 'The project setup changed. It applies when you’ve saved what you’re typing.'; }
  else if(st.lastOk){ text = 'Synced ' + hhmm(st.lastOk); title = 'In step with SharePoint at ' + whenText(st.lastOk); }
  chip.className = 'sync-chip ' + cls;
  chip.innerHTML = `<i class="led" aria-hidden="true"></i><span>${escH(text)}</span>`;
  chip.title = title;
  chip.setAttribute('aria-label', 'SharePoint sync: ' + text);
}
function syncAdvice(e){
  const acc = msAccount(), who = acc? acc.username : 'your account';
  switch(e.kind){
    case 'offline': return 'No connection. What you save stays on this device and is sent when the connection is back.';
    case 'signin': return 'Sign in with Microsoft to keep syncing. What you save stays on this device meanwhile.';
    case 'denied': return `SharePoint didn’t let ${who} into the project folder. Ask the planning manager to share the folder with you, with edit access to its “entries” folder.`;
    case 'missing': return 'The project folder can’t be found in SharePoint. It may have been moved, renamed or deleted. The planning manager can connect it again in Team & access.';
    case 'project': return e.message + ' The planning manager can connect the right folder in Team & access.';
    case 'config': return e.message;
    default: return e.message || 'Something went wrong while syncing. It is tried again in a couple of minutes.';
  }
}
async function syncWaitingCount(){
  const st = syncState(), months = syncOwnByMonth();
  let n = 0;
  for(const ym of Object.keys(months)) if(st.pushed[syncEntryFileName(ym)]!==await syncHash(months[ym])) n++;
  if(can('base') && (await syncHash(syncSetupBody()))!==st.setupHash) n++;
  return n;
}
async function openSyncPanel(){
  const st = syncState(), acc = msAccount(), c = CFG.sync || {};
  const waiting = canSyncHere()? await syncWaitingCount() : 0;
  const node = document.createElement('div');
  node.innerHTML = `<div class="sync-rows">
      <div><span>Project folder</span><b>${escH(c.folderName || 'SharePoint')}</b>${c.folderUrl? ` <a href="${escH(c.folderUrl)}" target="_blank" rel="noopener">Open in SharePoint</a>` : ''}</div>
      <div><span>Microsoft account</span><b>${acc? escH(acc.name || acc.username) : 'Not signed in on this device'}</b>${acc && acc.name? `<small>${escH(acc.username)}</small>` : ''}</div>
      <div><span>Last in step</span><b>${st.lastOk? escH(whenText(st.lastOk)) : 'Not yet'}</b></div>
      <div><span>Waiting to send</span><b>${waiting? waiting + ' file' + (waiting===1? '' : 's') : 'Nothing'}</b></div>
    </div>
    ${!canSyncHere()? `<div class="warn-banner">${escH(syncWhereText())}</div>` : st.error? `<div class="warn-banner">${escH(syncAdvice(st.error))}</div>` : ''}
    ${SYNC_NEEDS_RELOAD? '<p class="hint">The planning manager changed the project setup. It applies once what you’re typing is saved, or now with Apply update.</p>' : ''}
    <p class="hint">Entries are saved on this device first, then sent to the project’s SharePoint folder. Everyone else’s entries arrive the same way, every couple of minutes while the portal is open.</p>`;
  const buttons = [{label:'Close', value:'close'}];
  if(acc) buttons.push({label:'Sign out of Microsoft', value:'out'});
  if(SYNC_NEEDS_RELOAD) buttons.push({label:'Apply update', value:'apply'});
  if(canSyncHere()) buttons.push(acc? {label:'Sync now', value:'sync', primary:true} : {label:'Sign in with Microsoft', value:'signin', primary:true});
  const r = await uiDialog({title:'SharePoint sync', node, buttons, cancelValue:'close'});
  if(r.value==='sync') syncNow({announce:true});
  else if(r.value==='signin') msSignInSaved('resume');
  else if(r.value==='apply'){ if(await saveBeforeAction('the update')){ SYNC_NEEDS_RELOAD = false; reloadKeepingPlace('Project setup updated'); } }
  else if(r.value==='out'){
    if(await uiConfirm('This device stops sending and receiving entries until someone signs in with Microsoft again. Everything saved here stays here.', {title:'Sign out of Microsoft?', ok:'Sign out'})) msSignOut(false);
  }
}

/* ---------- planning managers: connect the project to a SharePoint folder ---------- */
function syncTeamHtml(){
  const c = CFG.sync, on = syncOn(), acc = msAccount(), st = on? syncState() : null;
  const why = canSyncHere()? '' : `<div class="warn-banner" style="margin:0 0 10px;">${escH(syncWhereText())}</div>`;
  if(!on){
    const askId = !BUILD_SYNC.clientId;
    return `<div class="settings-section first sp-section">
      <h4>SharePoint sync <span class="sp-badge">${c && c.off? 'Stopped' : 'Off'}</span></h4>
      <p class="hint">Keep everyone’s copy in step through a SharePoint folder. You connect it once; site engineers then sign in with their Microsoft work account, and entries travel by themselves: no setup or entries files. Your IT team registers the portal with Microsoft 365 once beforehand (see <a href="https://github.com/hereikeepmystuff-svg/DPR---Portal/blob/main/docs/sharepoint.md" target="_blank" rel="noopener">the SharePoint guide</a>).</p>
      ${why}
      <div class="sp-form">
        <label class="dlg-field"><span>SharePoint folder for this project</span><input type="url" id="spLink" placeholder="https://yourcompany.sharepoint.com/sites/…/DPR" autocomplete="off" value="${escH((c && c.folderUrl) || '')}"></label>
        <div class="hint" style="margin:-4px 0 10px;">Make an empty folder for the project in SharePoint, open it, and paste its address or its “Copy link” link here.</div>
        <details class="sp-adv"${askId? ' open' : ''}><summary>App registration${askId? '' : ' (from this build)'}</summary>
          <label class="dlg-field"><span>Application (client) ID</span><input type="text" id="spClient" placeholder="00000000-0000-0000-0000-000000000000" autocomplete="off" value="${escH((c && c.clientId) || BUILD_SYNC.clientId || '')}"></label>
          <label class="dlg-field"><span>Directory (tenant) ID</span><input type="text" id="spTenant" placeholder="00000000-0000-0000-0000-000000000000" autocomplete="off" value="${escH((c && c.tenant && c.tenant!=='organizations'? c.tenant : '') || BUILD_SYNC.tenant || '')}"></label>
          <div class="hint" style="margin:0;">Both from IT, from the app they registered for the portal. The tenant ID can stay empty only if IT made the app available to any organisation. This page’s address, which IT registers with the app: <code>${escH(msRedirectUri())}</code></div>
        </details>
        <button class="btn blue" type="button" id="spConnect"${canSyncHere()? '' : ' disabled'}>Sign in with Microsoft and connect</button>
      </div>
    </div>`;
  }
  return `<div class="settings-section first sp-section">
    <h4>SharePoint sync <span class="sp-badge on">On</span></h4>
    ${why}
    <div class="sync-rows">
      <div><span>Project folder</span><b>${escH(c.folderName || '')}</b>${c.folderUrl? ` <a href="${escH(c.folderUrl)}" target="_blank" rel="noopener">Open in SharePoint</a>` : ''}</div>
      <div><span>Connected</span><b>${escH(whenText(c.connectedAt))}</b><small>by ${escH(userName(c.connectedBy))}</small></div>
      <div><span>This device</span><b>${acc? escH(acc.username) : 'Not signed in to Microsoft'}</b><small>${st.lastOk? 'last in step ' + escH(whenText(st.lastOk)) : ''}</small></div>
    </div>
    <p class="hint">Engineers join with the invite link and sign in with Microsoft. Add each person under People with their work email, so the portal knows them without a PIN, and share the SharePoint folder with them (edit access).</p>
    <div class="sp-actions">
      <button class="btn blue" type="button" id="spInvite">Invite link…</button>
      <button class="btn secondary" type="button" id="spSync"${canSyncHere()? '' : ' disabled'}>Sync now</button>
      <button class="btn ghost" type="button" id="spStop">Stop syncing…</button>
    </div>
  </div>`;
}
function syncTeamWire(){
  const b = id=> document.getElementById(id);
  if(b('spConnect')) b('spConnect').onclick = spConnectStart;
  if(b('spInvite')) b('spInvite').onclick = ()=> showInviteDialog(false);
  if(b('spSync')) b('spSync').onclick = ()=> syncNow({announce:true}).then(()=> renderTeamPane());
  if(b('spStop')) b('spStop').onclick = spStop;
}
async function spConnectStart(){
  const link = (document.getElementById('spLink').value || '').trim();
  const clientId = (document.getElementById('spClient').value || '').trim();
  const tenant = (document.getElementById('spTenant').value || '').trim() || 'organizations';
  if(!canSyncHere()){ uiAlert(syncWhereText(), 'Not available here'); return; }
  if(!/^https?:\/\/\S+/.test(cleanFolderLink(link))){ uiAlert('Paste the address or link of the SharePoint folder for this project. It starts with https://.', 'Folder link needed'); return; }
  if(!/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(clientId) && !window.__dprEndpoints){ uiAlert('Enter the Application (client) ID IT gave you. It looks like 1a2b3c4d-1234-5678-9abc-1234567890ab.', 'App ID needed'); return; }
  await msSignInSaved('connect', {conf:{clientId, tenant}, data:{link}});
}
const SP_README = (name)=> `DPR Portal: project folder for "${name}"

The DPR Portal keeps everyone's copy of this project in step through this folder.

  dpr-project.json    the project setup: BOQ, areas, floors and pours, plan, periods, team
  dpr-workbook.xlsx   the project's DPR workbook
  entries\\           the daily entries, one file per device and month

Please don't edit, rename or move these files: the portal reads and writes them. SharePoint keeps
earlier versions in each file's version history.

Who can change what: planning managers need edit access to the whole folder. Site engineers need
edit access to the "entries" folder; read access to the rest is enough.
`;
async function spConnectFinish(p){
  SYNC_OVERRIDE = {clientId: p.clientId, tenant: p.tenant};
  syncBusy('Connecting to SharePoint…');
  try{
    const f = await spResolveFolder((p.data || {}).link);
    SYNC_OVERRIDE = Object.assign({}, SYNC_OVERRIDE, f);
    const meta = await spGet(SP_FILES.project);
    const pkg = meta? await spDownload(meta) : null;
    if(pkg && pkg.projectId && pkg.projectId!==CFG.projectId){
      syncBusy('');
      const r = await uiDialog({title:'This folder already holds a project',
        message:`“${pkg.projectName || 'A project'}” was connected to this folder by ${(pkg.by && pkg.by.name) || 'someone'}. Choose an empty folder for “${CFG.project.name}”, or open “${pkg.projectName || 'that project'}” on this device instead. Opening it replaces the project here.`,
        cancelValue:false, buttons:[{label:'Choose another folder', value:false}, {label:'Open that project', value:'join', danger: hasDailyEntries()}]});
      if(r.value==='join') return spJoinFinish({clientId: p.clientId, tenant: p.tenant, data: f});
      SYNC_OVERRIDE = null; return;
    }
    CFG.sync = {provider:'sharepoint', clientId: p.clientId, tenant: p.tenant, driveId: f.driveId, folderId: f.folderId,
      folderName: f.folderName, folderUrl: f.folderUrl, connectedAt: nowIso(), connectedBy: ME? ME.id : ''};
    const acc = msAccount(), me = ME && userById(ME.id);
    if(acc && me && !me.email && !teamUsers().some(u=> u.email===acc.username)) me.email = acc.username;
    touchBase(); logAct('SharePoint', 'Connected the project to ' + (f.folderName || 'a SharePoint folder'));
    SYNC_OVERRIDE = null;
    syncReset(meta? {setupETag: meta.eTag} : {});
    persist();
    try{ await spPut(SP_FILES.readme, SP_README(CFG.project.name || ''), 'text/plain'); }catch(e){ /* the readme is a courtesy */ }
    // the entries folder exists from the start, so its access can be set for engineers before they join
    try{ await spPut(SP_FILES.entries + '/About this folder.txt', 'Each device’s DPR entries, one file per month. The DPR Portal reads and writes these files.\n', 'text/plain'); }catch(e){}
    syncBusy('Sending the project and its entries…');
    const ok = await syncNow();
    syncBusy('');
    if(!ok){ uiAlert(syncAdvice(syncState().error), 'Connected, but not everything was sent yet'); return; }
    await showInviteDialog(true);
  }catch(e){
    syncBusy(''); SYNC_OVERRIDE = null;
    uiAlert(e.kind? syncAdvice(e) : e.message, 'Couldn’t connect to SharePoint');
  }
}
async function spStop(){
  if(!(await uiConfirm('Everyone’s copy stops sending and receiving entries once it next syncs. What is already in SharePoint stays there, and you can connect again at any time. Setup and entries files work as before.', {title:'Stop SharePoint sync?', ok:'Stop syncing', danger:true}))) return;
  CFG.sync = Object.assign({}, CFG.sync, {off: true});
  touchBase(); logAct('SharePoint', 'Stopped syncing');
  try{
    if(canSyncHere() && msAccount()){
      SYNC_OVERRIDE = Object.assign({}, CFG.sync, {off: false});
      await spPut(SP_FILES.project, JSON.stringify(syncSetupFile()), 'application/json');
    }
  }catch(e){ uiAlert('Sync is off on this device, but SharePoint couldn’t be told: ' + syncAdvice(e), 'Not everyone knows yet'); }
  finally{ SYNC_OVERRIDE = null; }
  persist(); setSyncChip(); renderTeamPane();
}

/* ---------- invite links ---------- */
function portalAddress(){
  if(BUILD_SYNC.portalUrl) return BUILD_SYNC.portalUrl;
  return location.hostname==='appassets.androidplatform.net' || !canSyncHere()? '' : msRedirectUri();
}
function inviteLink(){
  const c = CFG.sync || {};
  const payload = {v:1, n: CFG.project.name || '', c: c.clientId, t: c.tenant, d: c.driveId, f: c.folderId, u: c.folderUrl};
  const code = b64url(new TextEncoder().encode(JSON.stringify(payload)));
  const base = portalAddress();
  return base? base + '#join=' + code : 'dprportal://join?p=' + code;
}
function parseInvite(text){
  const s = String(text || '').trim();
  const m = s.match(/[#&?]join=([A-Za-z0-9_-]+)/) || s.match(/dprportal:\/\/join\?p=([A-Za-z0-9_-]+)/);
  if(m){
    try{
      const j = JSON.parse(new TextDecoder().decode(b64urlBytes(m[1])));
      if(j && j.d && j.f) return {clientId: j.c || '', tenant: j.t || '', driveId: j.d, folderId: j.f, projectName: j.n || '', folderUrl: j.u || ''};
    }catch(e){}
    return null;
  }
  const u = cleanFolderLink(s);
  return /^https?:\/\/\S+$/.test(u)? {link: u} : null;
}
async function showInviteDialog(fresh){
  const link = inviteLink();
  const node = document.createElement('div');
  node.innerHTML = `<p class="hint" style="margin-top:0;">Send this link to the site team by WhatsApp or email. Opening it downloads the project once they sign in with their Microsoft work account. In the Android app: <i>Join with invite link</i>, and paste it.</p>
    <div class="invite-row"><input type="text" readonly class="invite-link" id="ivLink" value="${escH(link)}"><button class="btn secondary" type="button" id="ivCopy">Copy</button>${navigator.share? '<button class="btn secondary" type="button" id="ivShare">Share…</button>' : ''}</div>
    <ul class="invite-list">
      <li>Add each person under <b>People</b> with their <b>work email</b>: the portal then knows who they are without a PIN.</li>
      <li>Share the SharePoint folder with them in SharePoint: <b>edit</b> access for site engineers, <b>view</b> access for view-only people.</li>
      <li>Someone without their own Microsoft account can sign in with a shared site account you give them, then pick their name and PIN.</li>
    </ul>`;
  const copy = async ()=>{
    const inp = node.querySelector('#ivLink');
    try{ await navigator.clipboard.writeText(link); flash('Invite link copied'); }
    catch(e){ inp.focus(); inp.select(); flash('Link selected: copy it with Ctrl+C or the phone’s copy button'); }
  };
  node.querySelector('#ivCopy').onclick = copy;
  if(node.querySelector('#ivShare')) node.querySelector('#ivShare').onclick = ()=> navigator.share({title:'Join ' + (CFG.project.name || 'the project') + ' in the DPR Portal', text:'Join ' + (CFG.project.name || 'our project') + ' in the DPR Portal: open the link and sign in with your work account.', url: link}).catch(()=>{});
  await uiDialog({title: fresh? 'Connected to SharePoint' : 'Invite link', message: fresh? `Everything for “${CFG.project.name}” is now in the SharePoint folder, and this device keeps it in step.` : '', node, wide:true,
    buttons:[{label:'Done', value:true, primary:true}], cancelValue:true});
  renderTeamPane();
}

/* ---------- site engineers: join from an invite link ---------- */
function showJoinScreen(inv){
  const name = inv.projectName || 'the project';
  const conf = {clientId: inv.clientId || BUILD_SYNC.clientId || '', tenant: inv.tenant || BUILD_SYNC.tenant || 'organizations'};
  const android = /Android/i.test(navigator.userAgent) && !window.DPRAndroid && inv.driveId;
  const code = inv.driveId? b64url(new TextEncoder().encode(JSON.stringify({v:1, n: inv.projectName, c: inv.clientId, t: inv.tenant, d: inv.driveId, f: inv.folderId, u: inv.folderUrl}))) : '';
  const o = authShell(`
    <p class="auth-q">Join “${escH(name)}”</p>
    <p class="hint" style="margin-top:0;">Sign in with your Microsoft work account. The project and everyone’s entries download to this device, and from then on what you enter is shared by itself.</p>
    ${canSyncHere()? '' : `<div class="warn-banner">${escH(syncWhereText())}</div>`}
    ${conf.clientId? '' : '<div class="warn-banner">This link doesn’t say which app to sign in with. Ask the planning manager for the invite link from the portal’s Team &amp; access.</div>'}
    <div class="join-actions">
      <button class="btn blue" type="button" id="jnGo"${canSyncHere() && conf.clientId? '' : ' disabled'}>Sign in with Microsoft</button>
      ${android? `<a class="btn secondary" id="jnApp" href="intent://join?p=${code}#Intent;scheme=dprportal;package=com.dprportal.app;end">Open in the DPR Portal app</a>` : ''}
    </div>
    <div class="auth-foot"><button class="linkbtn" type="button" id="jnBack">Not now</button></div>`, inv.projectName || '');
  o.querySelector('#jnGo').onclick = ()=> msSignIn('join', {conf, data: inv}).catch(e=> uiAlert(e.message, 'Can’t sign in'));
  o.querySelector('#jnBack').onclick = ()=>{ hideAuth(); bootAccess(); };
}
async function joinWithLinkDialog(){
  if(!canSyncHere()){ uiAlert(syncWhereText(), 'Not available here'); return; }
  const node = document.createElement('div');
  node.innerHTML = `<label class="dlg-field"><span>Invite link</span><input type="text" id="jlLink" autocomplete="off" placeholder="Paste the link from your planning manager"></label>
    <details class="sp-adv"><summary>Only a SharePoint folder link?</summary>
      <p class="hint" style="margin-top:0;">Paste the folder’s link above, and the app ID your planning manager or IT gives you here.</p>
      <label class="dlg-field"><span>Application (client) ID</span><input type="text" id="jlClient" autocomplete="off" value="${escH(BUILD_SYNC.clientId || '')}"></label>
    </details>`;
  const r = await uiDialog({title:'Join with invite link', node, focusEl: node.querySelector('#jlLink'), cancelValue:false,
    buttons:[{label:'Cancel', value:false}, {label:'Continue', value:true, primary:true, validate:()=>{
      const inv = parseInvite(node.querySelector('#jlLink').value);
      if(!inv) return 'Paste the invite link (or the SharePoint folder link).';
      if(!(inv.clientId || node.querySelector('#jlClient').value.trim() || BUILD_SYNC.clientId)) return 'This is a folder link: also enter the app (client) ID.';
      return ''; }}]});
  if(r.value!==true) return;
  const inv = parseInvite(node.querySelector('#jlLink').value);
  if(!inv.clientId) inv.clientId = node.querySelector('#jlClient').value.trim() || BUILD_SYNC.clientId || '';
  if(inv.link){ try{ await msSignIn('join', {conf:{clientId: inv.clientId, tenant: inv.tenant || BUILD_SYNC.tenant || 'organizations'}, data: inv}); }catch(e){ uiAlert(e.message, 'Can’t sign in'); } return; }
  showJoinScreen(inv);
}
async function spJoinFinish(p){
  SYNC_OVERRIDE = {clientId: p.clientId, tenant: p.tenant};
  syncBusy('Opening the project from SharePoint…');
  try{
    let loc = p.data || {};
    if(!loc.driveId) loc = Object.assign({}, loc, await spResolveFolder(loc.link));
    SYNC_OVERRIDE = Object.assign({}, SYNC_OVERRIDE, {driveId: loc.driveId, folderId: loc.folderId});
    const meta = await spGet(SP_FILES.project);
    if(!meta) throw syncErr('config', 'This SharePoint folder isn’t connected to the portal yet. The planning manager connects it in Team & access, then sends the invite link.');
    const pkg = await spDownload(meta);
    if(!pkg || pkg.kind!=='dpr-setup' || !pkg.config || !pkg.config.items) throw syncErr('config', 'The project file in that folder isn’t a DPR Portal setup.');
    const same = pkg.projectId===CFG.projectId;
    if(!same && CFG.team && hasDailyEntries()){
      syncBusy('');
      if(!(await uiConfirm(`This device holds entries for “${CFG.project.name}”. Opening “${pkg.projectName}” replaces that project here and deletes its entries on this device. Send them to your planning manager first if they’re still needed.`, {title:'Switch to a different project?', ok:'Replace project', danger:true}))){ SYNC_OVERRIDE = null; return; }
      syncBusy('Opening the project from SharePoint…');
    }
    SYNC_APPLYING = true;
    try{
      if(!same){
        ['progress','labour','labourCamp','machinery','material','progressLoc','pourCast','stamps','tomb','sent','pourGridExtra'].forEach(k=> store[k] = {});
        LOG_TYPES.forEach(t=> store[t] = []);
        store.activity = [];
      }
      store.config = pkg.config; CFG = store.config;
      if(same) applyPendingRenames(); else store.renamesAppliedAt = ((CFG.renames || []).slice(-1)[0] || {}).at || '';
      store.plan = pkg.plan || {}; store.planAuditLog = pkg.planAuditLog || []; store.labourPresets = pkg.labourPresets || [];
      store.periods = pkg.periods || {}; store.periodLog = pkg.periodLog || [];
      if(!CFG.sync || CFG.sync.off) CFG.sync = {provider:'sharepoint', clientId: p.clientId, tenant: p.tenant, driveId: loc.driveId, folderId: loc.folderId, folderName: loc.folderName || '', folderUrl: loc.folderUrl || ''};
      store.activity.push({at: nowIso(), by:'', act:'Joined from SharePoint', what: `${pkg.projectName || ''} (${(msAccount() || {}).username || ''})`});
      persist();
    } finally { SYNC_APPLYING = false; }
    SYNC_OVERRIDE = null;
    syncReset({setupETag: meta.eTag, setupHash: await syncHash(syncSetupBody())});
    const me = ME; ME = null;                     // nothing is sent from here until the person is known
    syncBusy('Downloading everyone’s entries…');
    await syncNow();
    ME = me;
    const u = syncMatchedUser(true);
    if(u) writeSession(u.id, true); else clearSession();
    syncBusy('');
    SYNC_NEEDS_RELOAD = false;
    reloadKeepingPlace(u? 'Welcome, ' + u.name.split(' ')[0] + ': you’re in step with SharePoint' : `“${pkg.projectName}” is on this device. Pick your name to sign in.`);
  }catch(e){
    syncBusy(''); SYNC_OVERRIDE = null;
    uiAlert(e.kind? syncAdvice(e) : e.message, 'Couldn’t open the project');
  }
}
/* The Android app passes on dprportal://join links it was opened with. */
window.__dprJoin = function(link){
  const inv = parseInvite(link);
  if(!inv){ uiAlert('That link isn’t a DPR Portal invite.', 'Can’t join'); return; }
  if(inv.folderId && CFG.sync && CFG.sync.folderId===inv.folderId && !CFG.sync.off){ flash('This device is already in step with “' + (inv.projectName || CFG.project.name) + '”'); return; }
  if(inv.link){ joinWithLinkDialog(); return; }
  showJoinScreen(inv);
};
function joinFromAddress(){
  const m = location.hash.match(/[#&]join=([A-Za-z0-9_-]+)/);
  if(!m) return null;
  history.replaceState(null, '', location.pathname + location.search);
  return parseInvite('#join=' + m[1]);
}

/* ---------- who is this: a team member recognised by their Microsoft account ---------- */
function syncMatchedUser(ignoreOptOut){
  if(!ignoreOptOut){ try{ if(sessionStorage.getItem('dpr_no_auto')) return null; }catch(e){} }
  const acc = msAccount();
  if(!acc || !acc.username || !CFG.team) return null;
  const ids = new Set([acc.username].concat(acc.names || []));
  const hits = teamUsers().filter(u=> u.email && ids.has(u.email.toLowerCase()));
  return hits.length===1? hits[0] : null;
}

function syncSignInNote(){
  if(!syncOn()) return '';
  const acc = msAccount();
  if(!acc) return canSyncHere()? '<p class="hint" style="margin-top:-6px;">With your Microsoft work account the portal knows you without a PIN: use <b>Sign in with Microsoft</b> below.</p>' : '';
  return `<p class="hint" style="margin-top:-6px;">Signed in to Microsoft as <b>${escH(acc.username)}</b>. Pick your name and enter your PIN.</p>`;
}

/* ---------- busy veil ---------- */
function syncBusy(msg){
  let v = document.getElementById('syncBusy');
  if(!msg){ if(v) v.remove(); return; }
  if(!v){ v = document.createElement('div'); v.id = 'syncBusy'; v.className = 'busy-veil'; v.setAttribute('role', 'status'); document.body.appendChild(v); }
  v.innerHTML = `<div class="box"><span class="spinner" aria-hidden="true"></span><span>${escH(msg)}</span></div>`;
}

/* ---------- start ---------- */
const persistHere = persist;
persist = function(){
  const ok = persistHere();
  if(ok && !SYNC_APPLYING && ME && ME.id!=='viewer') syncKick();
  return ok;
};
async function syncBoot(){
  const chip = document.getElementById('syncChip');
  if(chip) chip.onclick = openSyncPanel;
  resumePlace();
  setSyncChip();
  let res = null;
  try{ res = await msHandleRedirect(); }catch(e){ res = {error: e.kind || 'auth', message: e.message}; }
  if(res && res.error) await uiAlert(res.message, 'Microsoft sign-in didn’t finish');
  else if(res && res.ok){
    const next = res.pending.next;
    if(next==='connect') return spConnectFinish(res.pending);
    if(next==='join') return spJoinFinish(res.pending);
    try{ sessionStorage.removeItem('dpr_no_auto'); }catch(e){}
    if(!ME && CFG.team){ const u = syncMatchedUser(); if(u) await signInAs(u, true, true); }
  }
  const inv = joinFromAddress();
  if(inv){
    if(inv.folderId && CFG.sync && CFG.sync.folderId===inv.folderId && !CFG.sync.off && msAccount()) flash('This device is already in step with “' + (inv.projectName || CFG.project.name) + '”');
    else{ showJoinScreen(inv); return; }
  }
  if(syncOn() && canSyncHere() && msAccount()) syncNow();
  setSyncChip();
}
setInterval(()=>{ if(document.visibilityState==='visible' && navigator.onLine!==false && syncOn() && canSyncHere() && msAccount()) syncNow(); }, 120000);
setInterval(()=>{ if(SYNC_NEEDS_RENDER || SYNC_NEEDS_RELOAD) syncRefreshUI({}); }, 4000);
document.addEventListener('visibilitychange', ()=>{ if(document.visibilityState==='visible') syncKick(800); });
window.addEventListener('online', ()=> syncKick(800));
