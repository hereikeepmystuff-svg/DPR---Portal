/* =================== TEAM & ACCESS (planning managers) =================== */
function lastActive(uid){ for(let i=store.activity.length-1; i>=0; i--){ if(store.activity[i].by===uid) return store.activity[i].at; } return ''; }
function renderTeamPane(){
  const box = document.getElementById('teamPane'); if(!box) return;
  const all = (CFG.team && CFG.team.users) || [];
  const order = {pm:0, engineer:1};
  const people = all.slice().sort((a,b)=> ((a.active===false)-(b.active===false)) || (order[a.role]-order[b.role]) || a.name.localeCompare(b.name));
  const stale = CFG.updatedAt && (!store.lastSetupExport || store.lastSetupExport.at < CFG.updatedAt);
  box.innerHTML = `
    <div class="settings-section first">
      <h4>People</h4>
      <p class="hint">Planning managers change the base data. Site engineers make the daily entries, for the ${escH(T('zones').toLowerCase())} on their account (all of them if none are set). Each person signs in with their own PIN or password, and every saved entry records who made it.</p>
      <div class="table-scroll"><table class="team-table"><thead><tr><th>Person</th><th>Role</th><th>${escH(T('zones'))}</th><th>Site-wide reports</th><th>Signs in with</th><th>Last active here</th><th></th></tr></thead><tbody>
      ${people.map(u=>{
        const off = u.active===false, la = lastActive(u.id);
        return `<tr class="${off? 'inactive' : ''}">
          <td><div class="person">${avatarHtml(u)}<b>${escH(u.name)}</b>${ME && u.id===ME.id? ' <span class="you">you</span>' : ''}</div></td>
          <td>${escH(ROLE_LABEL[u.role])}</td>
          <td>${u.role==='engineer'? ((u.towers||[]).length? escH(u.towers.join(', ')) : 'All') : '—'}</td>
          <td>${u.role==='engineer'? (u.siteWide===false? 'No' : 'Yes') : '—'}</td>
          <td>${u.pin? 'PIN' : 'Password'}</td>
          <td>${la? escH(whenText(la)) : '—'}</td>
          <td class="row-actions">${off? `<button class="btn ghost" type="button" data-restore="${escH(u.id)}">Restore</button>` :
            `<button class="btn ghost" type="button" data-edit="${escH(u.id)}">Edit</button><button class="btn ghost" type="button" data-reset="${escH(u.id)}">New ${u.pin? 'PIN' : 'password'}</button>${ME && u.id!==ME.id? `<button class="btn ghost" type="button" data-remove="${escH(u.id)}">Remove</button>` : ''}`}</td></tr>`;
      }).join('')}
      </tbody></table></div>
      <button class="btn blue" type="button" id="tmAdd" style="margin-top:12px;">+ Add person</button>
    </div>

    <div class="settings-section">
      <h4>Who can do what</h4>
      <div class="table-scroll"><table class="perm-table"><thead><tr><th>Action</th><th>Planning manager</th><th>Site engineer</th><th>View only</th></tr></thead><tbody>
        ${PERM_ROWS.map(([label, perm, note])=> `<tr><td>${escH(label)}${note? `<div class="hint" style="margin:2px 0 0;">${escH(note)}</div>` : ''}</td>${['pm','engineer','viewer'].map(r=> `<td class="perm-cell">${PERMS[perm].includes(r)? '<span class="tick" aria-label="Yes">✓</span>' : '<span class="dash" aria-label="No">—</span>'}</td>`).join('')}</tr>`).join('')}
      </tbody></table></div>
      <p class="hint">These rules are checked in the browser, so they keep people to their job rather than stop someone set on getting around them. Moved to a shared backend such as SharePoint, the same three roles become server-enforced groups.</p>
    </div>

    <div class="settings-section">
      <h4>Share with engineers</h4>
      <p class="hint">Each engineer works on their own copy of this portal (this same file, or the shared link). Files keep the copies in step: you send the setup out, engineers send their entries back.</p>
      <div class="xchange">
        <div class="xcard">
          <h5><span class="step">1</span>Send the setup</h5>
          <p class="hint">BOQ, ${escH(T('zones').toLowerCase())}, floors &amp; pours, plan, periods, the team and its PINs${CFG.template && CFG.template.source==='idb'? ', and the project workbook' : ''}. Engineers open it once to join, and again after each change.</p>
          <label class="hint" style="display:block; margin:0 0 10px;"><input type="checkbox" id="tmInclEntries" checked> Include everyone&rsquo;s entries so far (keeps their cumulative figures up to date)</label>
          <button class="btn blue" type="button" id="tmExportSetup">Save setup file</button>
          <div class="hint ${stale? 'warn-text' : ''}" style="margin-top:8px;">${store.lastSetupExport? 'Last saved '+escH(whenText(store.lastSetupExport.at))+'.' : 'Not shared yet.'}${stale? ' The base data has changed since then — send a new one.' : ''}</div>
        </div>
        <div class="xcard">
          <h5><span class="step">2</span>Bring entries in</h5>
          <p class="hint">Import the entries files engineers send you. You can pick several at once. Newer entries replace older ones, nothing is counted twice, and days in closed periods are left alone.</p>
          <button class="btn blue" type="button" id="tmImportEntries">Import entries files&hellip;</button>
        </div>
      </div>
    </div>

    <div class="settings-section">
      <h4>Recovery code</h4>
      <p class="hint">Resets a planning manager password if it&rsquo;s forgotten. ${CFG.team && CFG.team.recovery? 'A code exists; creating a new one replaces it.' : '<b>No code yet</b> — create one and keep it somewhere safe.'}</p>
      <button class="btn secondary" type="button" id="tmRecovery">Create new recovery code</button>
    </div>

    <div class="settings-section">
      <h4>Recent activity on this device</h4>
      <div class="controls" style="margin:6px 0 10px;"><div class="field"><label for="tmActFilter">Show</label><select id="tmActFilter"><option value="">Everyone</option>${all.map(u=> `<option value="${escH(u.id)}">${escH(u.name)}</option>`).join('')}</select></div></div>
      <div class="table-scroll" style="max-height:34vh;"><table><thead><tr><th>When</th><th>Who</th><th>What</th><th>Details</th></tr></thead><tbody id="tmActBody"></tbody></table></div>
    </div>`;
  const b = id=> document.getElementById(id);
  b('tmAdd').onclick = ()=> personDialog(null);
  box.querySelectorAll('[data-edit]').forEach(x=> x.onclick = ()=> personDialog(userById(x.dataset.edit)));
  box.querySelectorAll('[data-reset]').forEach(x=> x.onclick = ()=> resetSecretDialog(userById(x.dataset.reset)));
  box.querySelectorAll('[data-remove]').forEach(x=> x.onclick = ()=> setActive(userById(x.dataset.remove), false));
  box.querySelectorAll('[data-restore]').forEach(x=> x.onclick = ()=> setActive(userById(x.dataset.restore), true));
  b('tmExportSetup').onclick = exportSetupFile;
  b('tmImportEntries').onclick = importEntriesFiles;
  b('tmRecovery').onclick = async ()=>{ await createRecoveryCode(false); renderTeamPane(); };
  b('tmActFilter').onchange = renderActivity;
  renderActivity();
}
function renderActivity(){
  const body = document.getElementById('tmActBody'); if(!body) return;
  const f = (document.getElementById('tmActFilter')||{}).value || '';
  const rows = store.activity.filter(a=> !f || a.by===f).slice(-300).reverse();
  body.innerHTML = rows.length? rows.map(a=> `<tr><td style="white-space:nowrap;">${escH(whenText(a.at))}</td><td>${escH(userName(a.by))}</td><td>${escH(a.act)}</td><td>${escH(a.what)}</td></tr>`).join('')
    : '<tr><td colspan="4" class="hint">Nothing recorded yet.</td></tr>';
}
async function personDialog(u){
  const isNew = !u, zones = CFG.towers;
  const cur = u || {name:'', role:'engineer', towers:[], siteWide:true, pin:true};
  const node = document.createElement('div');
  node.className = 'person-form';
  node.innerHTML = `
    <label class="dlg-field"><span>Name</span><input id="pfName" type="text" value="${escH(cur.name)}" autocomplete="off"></label>
    <div class="dlg-field"><span>Role</span>
      <div class="seg" role="radiogroup">
        <label><input type="radio" name="pfRole" value="engineer" ${cur.role==='engineer'? 'checked' : ''}> Site engineer</label>
        <label><input type="radio" name="pfRole" value="pm" ${cur.role==='pm'? 'checked' : ''}> Planning manager</label>
      </div></div>
    <div class="dlg-field eng-only"><span>${escH(T('zones'))} they enter progress for</span>
      <div class="chips">${zones.map(z=> `<label class="chip"><input type="checkbox" class="pfZone" value="${escH(z)}" ${(cur.towers||[]).includes(z)? 'checked' : ''}> ${escH(z)}</label>`).join('')}</div>
      <span class="hint" style="text-transform:none; letter-spacing:0; font-weight:400; margin:4px 0 0;">Leave all unticked to allow every ${escH(T('zone').toLowerCase())}.</span></div>
    <label class="check-line eng-only"><input type="checkbox" id="pfSite" ${cur.siteWide!==false? 'checked' : ''}> Can enter site-wide reports (labour, machinery, material &amp; staff, site logs)</label>
    <label class="dlg-field"><span id="pfSecretLabel"></span><input id="pfSecret" type="text" autocomplete="off"></label>`;
  const sec = node.querySelector('#pfSecret'), lab = node.querySelector('#pfSecretLabel');
  const role = ()=> node.querySelector('input[name="pfRole"]:checked').value;
  const sync = ()=>{
    const r = role();
    node.querySelectorAll('.eng-only').forEach(el=> el.hidden = r!=='engineer');
    lab.textContent = r==='pm'? (isNew? 'Password (6+ characters)' : 'New password (leave blank to keep)') : (isNew? 'PIN (4–8 digits)' : 'New PIN (leave blank to keep)');
    sec.inputMode = r==='pm'? 'text' : 'numeric';
    if(isNew && r!=='pm' && (!sec.value || !/^\d+$/.test(sec.value))) sec.value = randomPin();
    if(isNew && r==='pm' && /^\d{4}$/.test(sec.value)) sec.value = '';
  };
  node.querySelectorAll('input[name="pfRole"]').forEach(x=> x.onchange = sync);
  sync();
  const r = await uiDialog({title: isNew? 'Add a person' : 'Edit '+cur.name, node, focusEl: node.querySelector('#pfName'), wide:true, cancelValue:false,
    buttons:[{label:'Cancel', value:false}, {label: isNew? 'Add person' : 'Save', value:true, primary:true, validate:()=>{
      const name = node.querySelector('#pfName').value.trim(), rr = role(), s = sec.value.trim();
      if(!name) return 'Enter a name.';
      if(teamUsers().some(x=> x.name.toLowerCase()===name.toLowerCase() && (!u || x.id!==u.id))) return 'Someone on the team already has that name.';
      if(u && u.role==='pm' && rr!=='pm' && activePMs().length<2) return 'This is the only planning manager. Add another before changing their role.';
      if(rr==='pm' && (isNew || s) && s.length<6) return 'Use at least 6 characters for a planning manager’s password.';
      if(rr!=='pm' && (isNew || s) && !/^\d{4,8}$/.test(s)) return 'A PIN is 4 to 8 digits.';
      return ''; }}]});
  if(r.value!==true) return;
  const name = node.querySelector('#pfName').value.trim(), rr = role(), s = sec.value.trim();
  const towers = [...node.querySelectorAll('.pfZone:checked')].map(x=> x.value);
  const rec = u || {id:genId('u-'), active:true, created:nowIso()};
  const before = u? JSON.stringify([u.role, u.towers, u.siteWide]) : '';
  Object.assign(rec, {name, role:rr, towers: rr==='engineer'? towers : [], siteWide: rr==='engineer'? node.querySelector('#pfSite').checked : true});
  if(isNew || s){ rec.secret = await makeSecret(s); rec.pin = rr!=='pm'; }
  else if(rec.pin && rr==='pm'){ /* role became planning manager but kept a PIN: still allowed until they change it */ }
  if(isNew) CFG.team.users.push(rec);
  logAct('Team', isNew? `Added ${name} (${ROLE_LABEL[rr]})` : `Updated ${name}`+(before!==JSON.stringify([rec.role, rec.towers, rec.siteWide])? ' (role or access changed)' : '')+(s? ', new '+(rec.pin? 'PIN' : 'password') : ''));
  touchBase(); persist();
  if(ME && rec.id===ME.id){ applyAccess(); renderAll(); }
  renderTeamPane();
  if(isNew || s) await uiAlert(`Give ${name} this ${rec.pin? 'PIN' : 'password'}: ${s}\n\nThey sign in with it on their own copy after opening your setup file. Send a new setup file so their copy knows about this change.`, isNew? name+' added' : 'Sign-in changed');
}
async function resetSecretDialog(u){
  const word = u.pin? 'PIN' : 'password', val = u.pin? randomPin() : '';
  const s = await uiPrompt(`Set a new ${word} for ${u.name}. Their old ${word} stops working once the new setup file reaches their copy.`,
    {title:'New '+word+' for '+u.name, label:'New '+word, value:val, ok:'Set '+word,
     validate:v=> u.pin? (/^\d{4,8}$/.test(v[0].trim())? '' : 'A PIN is 4 to 8 digits.') : (v[0].trim().length>=6? '' : 'Use at least 6 characters.')});
  if(s===null) return;
  u.secret = await makeSecret(s.trim());
  logAct('Team', `New ${word} for ${u.name}`); touchBase(); persist(); renderTeamPane();
  flash(`New ${word} set for ${u.name}`);
}
async function setActive(u, on){
  if(!on){
    if(u.role==='pm' && activePMs().length<2){ uiAlert('This is the only planning manager, so they can’t be removed.', 'Can’t remove'); return; }
    if(!(await uiConfirm(`${u.name} won’t be able to sign in once your next setup file reaches their copy. Their saved entries stay, still marked with their name. You can restore them later.`, {title:'Remove '+u.name+'?', ok:'Remove', danger:true}))) return;
  }
  u.active = on;
  logAct('Team', (on? 'Restored ' : 'Removed ')+u.name); touchBase(); persist(); renderTeamPane();
}

/* =================== ENTRIES FILES: engineers -> planning manager =================== */
const ENTRY_TYPES = [['progress','Progress'],['cast','Pours cast'],['labour','Labour'],['machinery','Machinery'],['material','Material & staff'],['concrete','Concrete pours'],['rain','Rain register'],['hindrance','Hindrances'],['bbs','BBS checks']];
const LOG_TYPES = ['concrete','rain','hindrance','bbs'];
function logDate(t, r){ return t==='hindrance'? r.start : r.date; }
/* mine: leave out records that arrived in a setup file and haven't been changed here since. */
function collectEntries(from, to, mine){
  const inR = d=> !!d && d>=from && d<=to;
  const recent = r=> !!(r && r.at && r.at.slice(0,10)>=from);
  const fromSetup = x=> !!(mine && x && x.via==='setup');
  const out = {progressLoc:{}, labour:{}, labourCamp:{}, machinery:{}, material:{}, concrete:[], rain:[], hindrance:[], bbs:[], pourCast:{}, stamps:{}, tomb:{}};
  const keys = new Set([...Object.keys(store.progressLoc||{}), ...Object.keys(store.progress||{})]);
  keys.forEach(k=>{
    const d = k.slice(k.lastIndexOf('|')+1); if(!inR(d)) return;
    let L = store.progressLoc[k];
    if(!L){ const rec = store.progress[k]; if(!rec) return; const vals = {}; Object.keys(rec).forEach(s=>{ const a = entryAch(rec, s); if(a) vals[s] = a; }); L = {'': vals}; }
    const lids = Object.keys(L).filter(lid=> !fromSetup(store.stamps['p|'+k+'|'+lid]));
    if(!lids.length) return;
    out.progressLoc[k] = {}; lids.forEach(lid=>{ out.progressLoc[k][lid] = L[lid]; const sk = 'p|'+k+'|'+lid; if(store.stamps[sk]) out.stamps[sk] = store.stamps[sk]; });
  });
  const days = (src, dst, sk, skipSk)=> Object.keys(store[src]||{}).forEach(d=>{ if(!inR(d) || fromSetup(store.stamps[(sk||skipSk)+d])) return; out[dst][d] = store[src][d]; if(sk && store.stamps[sk+d]) out.stamps[sk+d] = store.stamps[sk+d]; });
  days('labour','labour','labour|'); days('labourCamp','labourCamp','', 'labour|'); days('machinery','machinery','mach|'); days('material','material','mat|');
  LOG_TYPES.forEach(t=> (store[t]||[]).forEach(r=>{ if((inR(logDate(t,r)) || recent(r)) && !fromSetup(r)) out[t].push(r); }));
  Object.keys(store.pourCast||{}).forEach(pid=>{ const c = store.pourCast[pid]; if((inR(c.date) || recent(c)) && !fromSetup(c)) out.pourCast[pid] = c; });
  Object.keys(store.tomb||{}).forEach(id=>{ if(recent(store.tomb[id])) out.tomb[id] = store.tomb[id]; });
  return out;
}
function countEntries(d){
  const n = {};
  n.progress = Object.keys(d.progressLoc||{}).reduce((s,k)=> s + Object.keys(d.progressLoc[k]).length, 0);
  n.cast = Object.keys(d.pourCast||{}).length;
  n.labour = Object.keys(d.labour||{}).length; n.machinery = Object.keys(d.machinery||{}).length; n.material = Object.keys(d.material||{}).length;
  LOG_TYPES.forEach(t=> n[t] = (d[t]||[]).length);
  return n;
}
function countText(n){ const parts = ENTRY_TYPES.filter(([k])=> n[k]).map(([k,l])=> `${l} ${n[k]}`); return parts.length? parts.join(' · ') : 'Nothing in this date range'; }
async function sendEntriesDialog(){
  if(!need('send')) return;
  const last = store.sent[ME.id];
  const firstOfMonth = todayStr().slice(0,8)+'01';
  const node = document.createElement('div');
  node.innerHTML = `<div class="dlg-row"><label class="dlg-field"><span>From</span><input type="date" id="seFrom" value="${escH(last? last.to : firstOfMonth)}"></label>
    <label class="dlg-field"><span>To</span><input type="date" id="seTo" value="${escH(todayStr())}"></label></div>
    <div class="send-count" id="seCount"></div>`;
  const upd = ()=>{ const f = node.querySelector('#seFrom').value, t = node.querySelector('#seTo').value; node.querySelector('#seCount').textContent = (f && t && f<=t)? countText(countEntries(collectEntries(f, t, true))) : 'Pick a valid date range.'; };
  node.querySelectorAll('input').forEach(i=> i.addEventListener('input', upd)); upd();
  const r = await uiDialog({title:'Send my entries', message:'Saves a file with every entry for these dates (including changes made since you last sent). Send it to your planning manager; sending the same days again is safe.',
    node, cancelValue:false, buttons:[{label:'Cancel', value:false}, {label:'Save file', value:true, primary:true, validate:()=>{
      const f = node.querySelector('#seFrom').value, t = node.querySelector('#seTo').value;
      if(!f || !t || f>t) return 'Pick a start date on or before the end date.'; return ''; }}]});
  if(r.value!==true) return;
  const from = node.querySelector('#seFrom').value, to = node.querySelector('#seTo').value;
  const data = collectEntries(from, to, true);
  const file = {kind:'dpr-entries', format:1, app:'DPR Portal v'+APP_VERSION, projectId: CFG.projectId, projectName: CFG.project.name||'',
    from:{id: ME.id, name: ME.name, role: ME.role}, exportedAt: nowIso(), range:{from, to}, data};
  const fname = `${fileStem()}_entries_${ME.name.replace(/[^a-zA-Z0-9]+/g,'_')}_${to}.json`;
  const res = await saveFile(fname, JSON.stringify(file), 'application/json');
  if(res!=='saved') return;
  store.sent[ME.id] = {at: nowIso(), to};
  logAct('Sent entries', `${from} to ${to}: ${countText(countEntries(data))}`); persist();
  flash('Saved '+fname+' — send it to your planning manager');
  if(document.getElementById('maSend')) renderMyAccount();
}
function canonJSON(x){
  if(Array.isArray(x)) return '['+x.map(canonJSON).join(',')+']';
  if(x && typeof x==='object') return '{'+Object.keys(x).sort().map(k=> JSON.stringify(k)+':'+canonJSON(x[k])).join(',')+'}';
  return JSON.stringify(x===undefined? null : x);
}
function canonObj(o){ return canonJSON(o||{}); }
function newerThan(inc, loc){ return ((inc && inc.at) || '') > ((loc && loc.at) || ''); }
/* Merges a set of daily entries into this device: newer wins (by the time each record was saved),
   identical records are left alone, and history or closed-period days are skipped. */
function mergeEntries(d, opts){
  opts = opts || {};
  const dry = !!opts.dryRun, allowClosed = !!opts.allowClosed, via = opts.via || '';
  const mark = x=> via? Object.assign({}, x||{by:'', at:''}, {via}) : x;
  const st = {}; ENTRY_TYPES.forEach(([k])=> st[k] = {added:0, updated:0, unchanged:0, kept:0, skipped:0, removed:0});
  const blocked = date=> (!allowClosed && isClosedDate(date));
  const stamps = d.stamps || {}, tomb = d.tomb || {};
  // progress
  Object.keys(d.progressLoc||{}).forEach(k=>{
    const cut = k.lastIndexOf('|'), tower = k.slice(0,cut), date = k.slice(cut+1), locs = d.progressLoc[k];
    Object.keys(locs).forEach(lid=>{
      const S = st.progress;
      if(!CFG.towers.includes(tower) || isHistoryDate(date) || blocked(date)){ S.skipped++; return; }
      const vals = locs[lid]||{}, sk = 'p|'+k+'|'+lid, inc = stamps[sk], loc = store.stamps[sk];
      const cur = locValues(tower, date, lid), curEmpty = !cur || !Object.keys(cur).length;
      if(curEmpty && !Object.keys(vals).length) return;
      if(cur && canonObj(cur)===canonObj(vals)){ S.unchanged++; if(!dry && inc && !loc) store.stamps[sk] = mark(inc); return; }
      if(!curEmpty && !newerThan(inc, loc)){ S.kept++; return; }
      if(!dry){ saveLocValues(tower, date, lid, Object.assign({}, vals)); if(inc || via) store.stamps[sk] = mark(inc); }
      curEmpty? S.added++ : S.updated++;
    });
  });
  // whole-day reports
  const day = (type, keys, sk, getCur, apply)=>{
    keys.forEach(date=>{
      const S = st[type];
      if(blocked(date)){ S.skipped++; return; }
      const inc = stamps[sk+date], loc = store.stamps[sk+date], cur = getCur(date), next = apply(date, true);
      const curEmpty = cur===null;
      if(!curEmpty && canonJSON(cur)===canonJSON(next)){ S.unchanged++; if(!dry && inc && !loc) store.stamps[sk+date] = mark(inc); return; }
      if(!curEmpty && !newerThan(inc, loc)){ S.kept++; return; }
      if(!dry){ apply(date, false); if(inc || via) store.stamps[sk+date] = mark(inc); }
      curEmpty? S.added++ : S.updated++;
    });
  };
  const labourDays = [...new Set([...Object.keys(d.labour||{}), ...Object.keys(d.labourCamp||{})])];
  day('labour', labourDays, 'labour|',
    date=> (store.labour[date]===undefined && store.labourCamp[date]===undefined)? null : {l: store.labour[date]||[], c: store.labourCamp[date]||[]},
    (date, peek)=>{ const v = {l: (d.labour||{})[date] || store.labour[date] || [], c: (d.labourCamp||{})[date] || store.labourCamp[date] || []}; if(!peek){ store.labour[date] = v.l; store.labourCamp[date] = v.c; } return v; });
  day('machinery', Object.keys(d.machinery||{}), 'mach|', date=> store.machinery[date]===undefined? null : store.machinery[date],
    (date, peek)=>{ const v = d.machinery[date]; if(!peek) store.machinery[date] = v; return v; });
  day('material', Object.keys(d.material||{}), 'mat|', date=> store.material[date]===undefined? null : store.material[date],
    (date, peek)=>{ const v = d.material[date]; if(!peek) store.material[date] = v; return v; });
  // site-log rows
  LOG_TYPES.forEach(t=>{
    const S = st[t], list = dry? (store[t]||[]).slice() : (store[t] = store[t]||[]);
    (d[t]||[]).forEach(r=>{
      if(!r || !r.id) return;
      const tb = store.tomb[r.id];
      if(tb && tb.at >= (r.at||'')){ S.kept++; return; }
      if(blocked(logDate(t, r))){ S.skipped++; return; }
      const i = list.findIndex(x=> x.id===r.id);
      if(i<0){
        if(list.some(x=> canonRow(Object.assign({}, x, {id:''}))===canonRow(Object.assign({}, r, {id:''})))){ S.unchanged++; return; }
        if(!dry) list.push(mark(r)); S.added++; return;
      }
      if(canonRow(list[i])===canonRow(r)){ S.unchanged++; return; }
      if(!newerThan(r, list[i])){ S.kept++; return; }
      if(!dry) list[i] = mark(r); S.updated++;
    });
    Object.keys(tomb).forEach(id=>{
      const i = list.findIndex(x=> x.id===id);
      if(i>=0 && (list[i].at||'') <= tomb[id].at && !blocked(logDate(t, list[i]))){ if(!dry){ list.splice(i,1); } S.removed++; }
    });
  });
  // pours cast
  Object.keys(d.pourCast||{}).forEach(pid=>{
    const S = st.cast, c = d.pourCast[pid], tb = store.tomb['cast|'+pid], loc = store.pourCast[pid];
    if(tb && tb.at >= (c.at||'')){ S.kept++; return; }
    if(blocked(c.date)){ S.skipped++; return; }
    if(loc && loc.date===c.date){ S.unchanged++; return; }
    if(loc && !newerThan(c, loc)){ S.kept++; return; }
    if(!dry) store.pourCast[pid] = mark(c); loc? S.updated++ : S.added++;
  });
  Object.keys(tomb).filter(k=> k.startsWith('cast|')).forEach(k=>{
    const pid = k.slice(5), loc = store.pourCast[pid];
    if(loc && (loc.at||'') <= tomb[k].at && !blocked(loc.date)){ if(!dry) delete store.pourCast[pid]; st.cast.removed++; }
  });
  if(!dry) Object.keys(tomb).forEach(id=>{ if(!store.tomb[id] || store.tomb[id].at < tomb[id].at) store.tomb[id] = tomb[id]; });
  return st;
}
function mergeTotals(st){ const t = {added:0, updated:0, unchanged:0, kept:0, skipped:0, removed:0}; Object.values(st).forEach(s=> Object.keys(t).forEach(k=> t[k]+=s[k])); return t; }
function mergeTableHtml(st){
  const rows = ENTRY_TYPES.filter(([k])=> Object.values(st[k]).some(Boolean));
  if(!rows.length) return '<p class="hint">Nothing to merge in this file.</p>';
  return `<div class="table-scroll" style="max-height:40vh;"><table class="merge-table"><thead><tr><th>Type</th><th class="num">New</th><th class="num">Updated</th><th class="num">Removed</th><th class="num">Same</th><th class="num">Newer here</th><th class="num">Skipped</th></tr></thead><tbody>
    ${rows.map(([k,l])=>{ const s = st[k]; return `<tr><td>${escH(l)}</td><td class="num">${s.added||''}</td><td class="num">${s.updated||''}</td><td class="num">${s.removed||''}</td><td class="num">${s.unchanged||''}</td><td class="num">${s.kept||''}</td><td class="num">${s.skipped||''}</td></tr>`; }).join('')}
  </tbody></table></div>`;
}
async function importEntriesFiles(){
  if(!need('import')) return;
  const files = await pickFile('.json,application/json', true);
  if(!files.length) return;
  const loaded = [], problems = [];
  for(const f of files){
    try{
      const j = JSON.parse(await readText(f));
      if(j.kind!=='dpr-entries' || !j.data){ problems.push(`${f.name}: not an entries file from this portal.`); continue; }
      if(j.projectId!==CFG.projectId){ problems.push(`${f.name}: it’s for “${j.projectName||'another project'}”, not this one. The engineer needs your current setup file first.`); continue; }
      loaded.push({name:f.name, j});
    }catch(e){ problems.push(`${f.name}: couldn’t be read (${e.message}).`); }
  }
  if(!loaded.length){ uiAlert(problems.join('\n'), 'Nothing imported'); return; }
  loaded.sort((a,b)=> (a.j.exportedAt||'').localeCompare(b.j.exportedAt||''));
  const node = document.createElement('div');
  node.innerHTML = loaded.map(x=>{
    const st = mergeEntries(x.j.data, {dryRun:true}), t = mergeTotals(st);
    return `<div class="merge-file"><div class="merge-head">${avatarHtml(userById(x.j.from && x.j.from.id) || {name:(x.j.from||{}).name||'?', role:(x.j.from||{}).role||'engineer'})}<div><b>${escH((x.j.from||{}).name||'Unknown')}</b>
      <div class="hint" style="margin:0;">${escH(x.j.range? x.j.range.from+' to '+x.j.range.to : '')} · saved ${escH(whenText(x.j.exportedAt))} · ${t.added} new, ${t.updated} updated${t.removed? ', '+t.removed+' removed' : ''}</div></div></div>${mergeTableHtml(st)}</div>`;
  }).join('') + (problems.length? `<div class="warn-banner" style="margin-top:10px;">${problems.map(escH).join('<br>')}</div>` : '')
    + '<p class="hint">“Newer here”: this device has a later version, so it’s kept. “Skipped”: the day is in a closed period, before the workbook’s baseline date, or for a '+escH(T('zone').toLowerCase())+' this project no longer has.</p>';
  const r = await uiDialog({title: loaded.length===1? 'Import these entries?' : `Import ${loaded.length} entries files?`, node, wide:true, cancelValue:false,
    buttons:[{label:'Cancel', value:false}, {label:'Import', value:true, primary:true}]});
  if(r.value!==true) return;
  let added = 0, updated = 0;
  loaded.forEach(x=>{
    const t = mergeTotals(mergeEntries(x.j.data, {}));
    added += t.added; updated += t.updated;
    logAct('Imported entries', `from ${(x.j.from||{}).name||'?'} (${x.j.range? x.j.range.from+' to '+x.j.range.to : x.name}): ${t.added} new, ${t.updated} updated, ${t.kept} kept, ${t.skipped} skipped`);
  });
  persist(); renderAll(); reloadLogs(); renderTeamPane();
  flash(`Imported ${added} new and ${updated} updated record(s)`);
}

/* =================== SETUP FILES: planning manager -> engineers =================== */
async function buildSetupPackage(includeEntries){
  if(!CFG.updatedAt) touchBase();
  const pkg = {kind:'dpr-setup', format:1, app:'DPR Portal v'+APP_VERSION, projectId: CFG.projectId, projectName: CFG.project.name||'',
    exportedAt: nowIso(), by:{id: ME.id, name: ME.name},
    config: CFG, plan: store.plan||{}, planAuditLog: store.planAuditLog||[], labourPresets: store.labourPresets||[], periods: store.periods||{}, periodLog: store.periodLog||[]};
  if(CFG.template && CFG.template.source==='idb'){ try{ const b = await TPL_DB.get('template'); if(b) pkg.templateB64 = bytesToB64(new Uint8Array(b)); }catch(e){ console.error(e); } }
  if(includeEntries) pkg.entries = collectEntries('0000-01-01', '9999-12-31');
  return pkg;
}
async function exportSetupFile(){
  if(!need('team')) return;
  const incl = !!(document.getElementById('tmInclEntries')||{}).checked;
  const pkg = await buildSetupPackage(incl);
  const fname = `${fileStem()}_setup_${todayStr()}.json`;
  const res = await saveFile(fname, JSON.stringify(pkg), 'application/json');
  if(res!=='saved') return;
  store.lastSetupExport = {at: nowIso(), by: ME.id};
  logAct('Shared setup', fname+(incl? ' (with entries)' : '')); persist(); renderTeamPane();
  await uiAlert(`Send ${fname} to each engineer together with the portal file (or its link). On their copy they choose “Open setup file”, then sign in with the PIN you gave them.`, 'Setup file saved');
}
function hasDailyEntries(){
  return Object.keys(store.progress||{}).length || Object.keys(store.labour||{}).length || Object.keys(store.machinery||{}).length
    || Object.keys(store.material||{}).length || LOG_TYPES.some(t=> (store[t]||[]).length);
}
async function joinFromSetupFile(){
  const files = await pickFile('.json,application/json', false);
  if(!files.length) return;
  let pkg;
  try{ pkg = JSON.parse(await readText(files[0])); }catch(e){ uiAlert('That file couldn’t be read as a setup file.', 'Not a setup file'); return; }
  if(!pkg || pkg.kind!=='dpr-setup' || !pkg.config || !pkg.config.items){
    uiAlert(pkg && pkg.kind==='dpr-entries'? 'That’s an entries file. Planning managers import those in Settings → Team & access.' : 'Choose the setup file your planning manager saved from Settings → Team & access.', 'Not a setup file');
    return;
  }
  const same = pkg.projectId===CFG.projectId;
  const pdate = whenText(pkg.exportedAt);
  if(!same && CFG.team && hasDailyEntries()){
    if(!(await uiConfirm(`This device holds entries for “${CFG.project.name}”. Opening a setup file for “${pkg.projectName}” replaces that project here and deletes its entries on this device. Send them to your planning manager first if they’re still needed.`, {title:'Switch to a different project?', ok:'Replace project', danger:true}))) return;
  } else if(same && CFG.updatedAt && pkg.config.updatedAt && pkg.config.updatedAt < CFG.updatedAt){
    if(!(await uiConfirm(`This setup file (${pdate}) is older than the setup already on this device (${whenText(CFG.updatedAt)}). Use it anyway?`, {title:'Older setup file', ok:'Use older setup'}))) return;
  } else if(same){
    if(!(await uiConfirm(`Update this device to the setup saved by ${(pkg.by||{}).name||'the planning manager'} on ${pdate}? Your entries here are kept.`, {title:'Update project setup?', ok:'Update setup'}))) return;
  }
  if(!same){
    ['progress','labour','labourCamp','machinery','material','progressLoc','pourCast','stamps','tomb','sent','pourGridExtra'].forEach(k=> store[k] = {});
    LOG_TYPES.forEach(t=> store[t] = []);
    store.activity = [];
  }
  store.config = pkg.config; CFG = store.config;
  store.plan = pkg.plan||{}; store.planAuditLog = pkg.planAuditLog||[]; store.labourPresets = pkg.labourPresets||[];
  store.periods = pkg.periods||{}; store.periodLog = pkg.periodLog||[];
  if(pkg.templateB64){ try{ await TPL_DB.put('template', b64ToBytes(pkg.templateB64)); }catch(e){ console.error(e); } }
  let note = '';
  if(pkg.entries){ const t = mergeTotals(mergeEntries(pkg.entries, {allowClosed:true, via:'setup'})); note = ` It also brought ${t.added+t.updated} entr${t.added+t.updated===1? 'y' : 'ies'} from the master copy.`; }
  store.activity.push({at: nowIso(), by: ME? ME.id : '', act:'Opened setup file', what: `${files[0].name} (saved ${pdate} by ${(pkg.by||{}).name||'?'})`});
  if(!persist()) return;
  await uiAlert(`“${pkg.projectName}” is set up on this device.${note} Sign in to continue.`, same? 'Setup updated' : 'Project ready');
  clearSession();
  location.reload();
}
