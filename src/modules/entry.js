/* =================== FASTER DAILY ENTRY (v2.2) =================== */
/* The forms on screen always belong to one context: the date, and for progress the tower and entry
   mode, they were drawn for. Each section remembers what it showed when it was drawn, so the portal
   knows when something was typed but not saved: it marks the tab, offers to save before the date,
   tower or person changes, and Ctrl+S saves the tab you're on. */
const FORM = {date:'', tower:'', mode:'tower', modeSel:'pours'};
const DATED = ['progress','labour','machinery','material'];
const LOGS = ['concrete','rain','hindrance','bbs'];
const SEC_LABEL = {progress:'Progress', labour:'Labour', machinery:'Machinery', material:'Material & staff', concrete:'Concrete pours', rain:'Rain register', hindrance:'Hindrances', bbs:'BBS checks'};
const SNAP = {};

function entryDate(){ return dateInput.value || todayStr(); }
function dayLabel(d){
  if(!d) return '';
  const x = new Date(d+'T00:00:00');
  return isNaN(x)? d : ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'][x.getDay()]+' '+x.getDate()+' '+MONTHS[x.getMonth()];
}
function relDay(d){
  const n = daysBetween(d, todayStr());
  return n===0? 'today' : n===1? 'yesterday' : n===-1? 'tomorrow' : n>1? n+' days ago' : 'in '+(-n)+' days';
}
function lastDateWith(map, date, pred){ let best = ''; Object.keys(map||{}).forEach(d=>{ if(d<date && d>best && (!pred || pred(map[d]))) best = d; }); return best; }
function setDayNote(id, html){ const el = document.getElementById(id); if(!el) return; el.innerHTML = html||''; el.hidden = !html; }

/* ---------- reading each form ---------- */
function readItemList(){
  const out = [];
  entryBody.querySelectorAll('.today-input').forEach(i=>{ const v = parseFloat(i.value)||0; if(v>0) out.push([+i.dataset.sno, v]); });
  return out;
}
function collectLabour(){
  const rows = [];
  labourBody.querySelectorAll('tr').forEach(tr=>{
    const counts = {};
    tr.querySelectorAll('.labourCount').forEach(inp=>{ const v = parseFloat(inp.value); if(!isNaN(v) && v>0) counts[inp.dataset.field] = v; });
    const contractor = tr.querySelector('.contractorInput').value.trim(), category = tr.querySelector('.categoryInput').value.trim();
    if(!contractor && !category && !Object.keys(counts).length) return;   // an empty row isn't a crew
    rows.push({contractor, tower: tr.querySelector('.towerInputSel').value, category, counts});
  });
  const campRows = [];
  labourCampBody.querySelectorAll('tr').forEach(tr=>{
    const contractor = tr.querySelector('.lcContractor').value.trim(), count = parseFloat(tr.querySelector('.lcCount').value)||0;
    if(contractor || count>0) campRows.push({contractor, category: tr.querySelector('.lcCategory').value.trim(), count, remark: tr.querySelector('.lcRemark').value.trim()});
  });
  return {rows, campRows};
}
function collectMachinery(){
  const rec = {};
  machineryBody.querySelectorAll('.machineryCount').forEach(inp=>{ const v = parseFloat(inp.value); if(!isNaN(v) && v>0) rec[inp.dataset.sno] = v; });
  return rec;
}
function collectMaterial(){
  const rec = {};
  materialRows.querySelectorAll('.materialInput').forEach(inp=>{ const v = parseFloat(inp.value); if(!isNaN(v)) rec[inp.dataset.key] = v; });
  staffRows.querySelectorAll('.staffInput').forEach(inp=>{ const v = parseFloat(inp.value); if(!isNaN(v)) rec[inp.dataset.key] = v; });
  rec.remark = document.getElementById('materialRemark').value.trim();
  return rec;
}
/* Untouched starter rows are not entries, so each log keeps only rows with something in them. */
const LOG_READ = {
  concrete: ()=> [...concreteBody.querySelectorAll('tr')].map(tr=> ({ id: tr.dataset.id||'', date: tr.querySelector('.cDate').value, tower: tr.querySelector('.cTower').value,
      structure: tr.querySelector('.cStruct').value, grade: tr.querySelector('.cGrade').value, qty: parseFloat(tr.querySelector('.cQty').value)||0 }))
    .filter(r=> (+r.qty>0) || (r.structure||'').trim()),
  rain: ()=> [...rainBody.querySelectorAll('tr')].map(tr=> ({ id: tr.dataset.id||'', date: tr.querySelector('.rDate').value, start: tr.querySelector('.rStart').value,
      end: tr.querySelector('.rEnd').value, intensity: tr.querySelector('.rIntensity').value, affected: tr.querySelector('.rAffected').value }))
    .filter(r=> r.start || r.end || (r.affected||'').trim()),
  hindrance: ()=> [...hindranceBody.querySelectorAll('tr')].map(tr=> ({ id: tr.dataset.id||'', desc: tr.querySelector('.hDesc').value, start: tr.querySelector('.hStart').value,
      end: tr.querySelector('.hEnd').value, ongoing: tr.querySelector('.hOngoing').checked }))
    .filter(r=> (r.desc||'').trim()),
  bbs: ()=> [...bbsBody.querySelectorAll('tr')].map(tr=> ({ id: tr.dataset.id||'', date: tr.querySelector('.bDate').value, start: tr.querySelector('.bStart').value,
      end: tr.querySelector('.bEnd').value, qty: parseFloat(tr.querySelector('.bQty').value)||0, uom: tr.querySelector('.bUom').value, tower: tr.querySelector('.bTower').value,
      staff: tr.querySelector('.bStaff').value, remarks: tr.querySelector('.bRemarks').value }))
    .filter(r=> (+r.qty>0) || (r.staff||'').trim() || (r.remarks||'').trim())
};
const SECTION_READ = {
  progress: ()=> JSON.stringify(readItemList()),
  labour: ()=> JSON.stringify(collectLabour()),
  machinery: ()=> JSON.stringify(collectMachinery()),
  material: ()=> JSON.stringify(collectMaterial()),
  concrete: ()=> JSON.stringify(LOG_READ.concrete()),
  rain: ()=> JSON.stringify(LOG_READ.rain()),
  hindrance: ()=> JSON.stringify(LOG_READ.hindrance()),
  bbs: ()=> JSON.stringify(LOG_READ.bbs())
};
function snapSection(k){ try{ SNAP[k] = SECTION_READ[k](); }catch(e){ SNAP[k] = undefined; } scheduleDirtyUI(); }
function isDirty(k){
  if(k==='progress' && FORM.mode==='pours') return typeof pgUnsaved==='function' && pgUnsaved()>0;
  if(SNAP[k]===undefined) return false;
  try{ return SECTION_READ[k]() !== SNAP[k]; }catch(e){ return false; }
}
function dirtyMap(){ const d = {}; DATED.concat(LOGS).forEach(k=> d[k] = isDirty(k)); return d; }
function anyUnsaved(){ return DATED.concat(LOGS).some(isDirty); }

/* ---------- unsaved changes on the tabs ---------- */
const SAVE_BTNS = [['saveLabourBtn','labour'],['saveMachineryBtn','machinery'],['saveMaterialBtn','material'],['saveConcreteBtn','concrete'],['saveRainBtn','rain'],['saveHindranceBtn','hindrance'],['saveBbsBtn','bbs']];
let dirtyTimer = 0;
function scheduleDirtyUI(){ clearTimeout(dirtyTimer); dirtyTimer = setTimeout(updateDirtyUI, 120); }
let LAST_DIRTY = {};
function updateDirtyUI(){
  const d = dirtyMap(); LAST_DIRTY = d;
  const tabs = {entry:d.progress, labour:d.labour, machinery:d.machinery, material:d.material, sitelogs: LOGS.some(k=> d[k])};
  document.querySelectorAll('.tab').forEach(t=>{ const u = !!tabs[t.dataset.tab]; t.classList.toggle('unsaved', u); if(u) t.title = 'Unsaved changes'; else t.removeAttribute('title'); });
  document.querySelectorAll('.subtab').forEach(t=> t.classList.toggle('unsaved', !!d[t.dataset.sub]));
  SAVE_BTNS.forEach(([id,k])=>{ const b = document.getElementById(id); if(b) b.classList.toggle('pulse', !!d[k]); });
  if(FORM.mode!=='pours') document.getElementById('saveBtn').classList.toggle('pulse', !!d.progress);
  renderDayStrip(d);
  updateFab();
}
/* When the tab's own Save button has scrolled out of sight and there is something to save, a
   floating Save button follows you down long lists (most useful on phones). */
const SAVE_BTN_OF = {progress:'saveBtn', labour:'saveLabourBtn', machinery:'saveMachineryBtn', material:'saveMaterialBtn', concrete:'saveConcreteBtn', rain:'saveRainBtn', hindrance:'saveHindranceBtn', bbs:'saveBbsBtn'};
const SAVE_ICON = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 3h11l3 3v13a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2z"/><path d="M8 3v5h7V3"/><rect x="8" y="13" width="8" height="6" rx="1"/></svg>';
function updateFab(){
  const fab = document.getElementById('fabSave'); if(!fab) return;
  const k = activeSaveKey(), btn = k && document.getElementById(SAVE_BTN_OF[k]);
  let show = !!(k && LAST_DIRTY[k] && btn && !btn.disabled && btn.offsetParent!==null);
  if(show){ const r = btn.getBoundingClientRect(); show = r.bottom < 8 || r.top > window.innerHeight - 8; }
  if(fab.hidden===show) fab.hidden = !show;
  if(show && fab.dataset.k!==k){ fab.dataset.k = k; fab.innerHTML = SAVE_ICON+escH('Save '+(k==='material'? 'material & staff' : SEC_LABEL[k].toLowerCase())); }
}
let fabRaf = 0;
window.addEventListener('scroll', ()=>{ if(!fabRaf) fabRaf = requestAnimationFrame(()=>{ fabRaf = 0; updateFab(); }); }, {passive:true});
window.addEventListener('resize', ()=> updateFab());
document.getElementById('fabSave').addEventListener('click', ()=>{ const k = activeSaveKey(); if(k) SAVE_FN[k](); });
document.addEventListener('input', scheduleDirtyUI, true);
document.addEventListener('change', scheduleDirtyUI, true);
document.addEventListener('click', e=>{ if(e.target.closest && e.target.closest('.panel button, .panel .row-x, .panel a, .tab, .subtab')) scheduleDirtyUI(); }, true);
window.addEventListener('beforeunload', e=>{ if(anyUnsaved()){ e.preventDefault(); e.returnValue = ''; } });

/* ---------- saving ---------- */
async function saveProgress(o){
  o = o||{};
  const tower = towerSelect.value, date = dateInput.value;
  if(isLockedDate(date)){ flash(isHistoryDate(date)? 'This date is already recorded in the workbook — nothing to save here.' : fmtMonth(date.slice(0,7))+' is closed.'); return false; }
  if(!need('progress', tower)) return false;
  if(entryMode()==='pours'){ savePourGrid(tower, date); return true; }
  const vals = Object.assign({}, locValues(tower, date, '') || {});
  const warn = [];
  entryBody.querySelectorAll('tr[data-sno]').forEach(tr=>{
    const inp = tr.querySelector('.today-input'); if(!inp) return;
    const sno = parseInt(inp.dataset.sno,10), a = parseFloat(inp.value)||0;
    if(a>0) vals[sno] = a; else delete vals[sno];
    const it = CFG.items.find(i=> i.sno===sno);
    if(!it || !(a>0) || (inp.dataset.saved==='1' && +inp.dataset.orig===a)) return;   // unchanged values were checked when first saved
    const total = +it.total_qty||0, planned = parseFloat(tr.dataset.planned)||0;
    const prior = (parseFloat(tr.dataset.before)||0) + (parseFloat(tr.dataset.others)||0), cum = prior + a;
    if(total>0 && prior <= total && cum > total + 1e-9) warn.push(`${it.sno}. ${it.short}: takes the cumulative to ${fmt(cum)} of ${fmt(total)} ${it.uom}`);
    else if(planned>0 && a >= planned*10) warn.push(`${it.sno}. ${it.short}: ${fmt(a)} ${it.uom} is ten times or more the day’s plan (${fmt(planned)})`);
    else if(total>=20 && a > total*0.5) warn.push(`${it.sno}. ${it.short}: ${fmt(a)} ${it.uom} in one day is more than half the BOQ quantity (${fmt(total)})`);
  });
  if(warn.length && !(await uiConfirm('Please check these entries:\n• '+warn.join('\n• ')+'\n\nSave if the figures are right: work beyond the plan or the BOQ quantity is allowed.', {title:'Check before saving', ok:'Save anyway', cancel:'Go back'}))) return false;
  saveLocValues(tower, date, '', vals); stamp('p|'+tower+'|'+date+'|');
  logAct('Progress', tower+' · '+date+' · whole '+T('zone').toLowerCase()); persist();
  flash('Saved progress — '+tower+' (whole '+T('zone').toLowerCase()+') — '+date);
  const ae = document.activeElement, keep = ae && ae.classList && ae.classList.contains('today-input') && entryBody.contains(ae)? ae.dataset.sno : '';
  renderEntry();
  if(keep){ const el = entryBody.querySelector(`.today-input[data-sno="${keep}"]`); if(el && el.offsetParent!==null){ el.focus({preventScroll:true}); try{ el.select(); }catch(e){} } }
  return true;
}
function saveLabour(){
  const date = dateInput.value;
  if(!need('site')) return false;
  if(blockIfClosed(date,'labour')) return false;
  const {rows, campRows} = collectLabour();
  store.labour[date] = rows; store.labourCamp[date] = campRows;
  stamp('labour|'+date); logAct('Labour report', date+' · '+rows.length+' crew row(s)');
  persist(); setSavedBy('labourSavedBy', stampOf('labour|'+date)); renderLabourNote(date);
  snapSection('labour');
  flash('Saved labour report — '+date);
  return true;
}
function saveMachinery(){
  const date = dateInput.value;
  if(!need('site')) return false;
  if(blockIfClosed(date,'machinery counts')) return false;
  store.machinery[date] = collectMachinery(); stamp('mach|'+date); logAct('Machinery report', date);
  persist(); setSavedBy('machSavedBy', stampOf('mach|'+date)); setDayNote('machNote', '');
  snapSection('machinery');
  flash('Saved machinery report — '+date);
  return true;
}
function saveMaterial(){
  const date = dateInput.value;
  if(!need('site')) return false;
  if(blockIfClosed(date,'material & staff')) return false;
  store.material[date] = collectMaterial(); stamp('mat|'+date); logAct('Material & staff', date);
  persist(); setSavedBy('matSavedBy', stampOf('mat|'+date)); setDayNote('matNote', '');
  snapSection('material');
  flash('Saved material & staff report — '+date);
  return true;
}
function saveConcrete(){
  if(!need('site')) return false;
  const sl = stampLogRows(store.concrete, LOG_READ.concrete());
  const kept = sl.rows;
  if(closedLogEdit(store.concrete, kept, 'date', 'concrete')) return false;
  sl.commit(); store.concrete = kept;
  logAct('Concrete log', kept.length+' row(s)');
  const castN = castFromConcrete(kept); persist();
  if(castN) setTimeout(()=>flash(castN+' pour(s) marked cast from the concrete log'), 1200);
  loadConcrete(); flash('Saved concrete log — '+kept.length+' pour(s)');
  return true;
}
function saveRain(){
  if(!need('site')) return false;
  const sl = stampLogRows(store.rain, LOG_READ.rain());
  const kept = sl.rows;
  if(closedLogEdit(store.rain, kept, 'date', 'rain register')) return false;
  sl.commit(); store.rain = kept;
  logAct('Rain register', kept.length+' row(s)'); persist(); loadRain();
  flash('Saved rain register — '+kept.length+' event(s)');
  return true;
}
function saveHindrance(){
  if(!need('site')) return false;
  const sl = stampLogRows(store.hindrance, LOG_READ.hindrance());
  const kept = sl.rows;
  if(closedLogEdit(store.hindrance, kept, 'start', 'hindrance')) return false;
  sl.commit(); store.hindrance = kept;
  logAct('Hindrance log', kept.length+' row(s)'); persist(); loadHindrance();
  flash('Saved hindrance log — '+kept.length+' item(s)');
  return true;
}
function saveBbs(){
  if(!need('site')) return false;
  const sl = stampLogRows(store.bbs, LOG_READ.bbs());
  const kept = sl.rows;
  if(closedLogEdit(store.bbs, kept, 'date', 'BBS')) return false;
  sl.commit(); store.bbs = kept;
  logAct('BBS log', kept.length+' row(s)'); persist(); loadBbs();
  flash('Saved BBS checking log — '+kept.length+' item(s)');
  return true;
}
const SAVE_FN = {progress:o=> saveProgress(o), labour:saveLabour, machinery:saveMachinery, material:saveMaterial, concrete:saveConcrete, rain:saveRain, hindrance:saveHindrance, bbs:saveBbs};
async function saveSections(keys){
  for(const k of keys){
    let ok = false;
    try{ ok = await SAVE_FN[k](); }catch(e){ console.error(e); ok = false; }
    if(!ok){ scheduleDirtyUI(); return false; }
  }
  return true;
}

/* ---------- before moving on: save, discard or keep editing ---------- */
function sectionWhere(k){
  if(k==='progress') return `${SEC_LABEL.progress} · ${FORM.tower} · ${dayLabel(FORM.date)}`;
  if(DATED.includes(k)) return `${SEC_LABEL[k]} · ${dayLabel(FORM.date)}`;
  return SEC_LABEL[k];
}
function restoreForm(){
  if(FORM.date) dateInput.value = FORM.date;
  if([...towerSelect.options].some(o=> o.value===FORM.tower)) towerSelect.value = FORM.tower;
  entryModeSel.value = FORM.modeSel;
}
async function leaveGuard(why){
  const keys = (why==='tower' || why==='mode')? ['progress'] : why==='date'? DATED : DATED.concat(LOGS);
  const dirty = keys.filter(isDirty);
  if(!dirty.length) return true;
  const r = await uiDialog({title:'Save your changes first?', message:'These changes aren’t saved yet:\n'+dirty.map(k=> '• '+sectionWhere(k)).join('\n'),
    cancelValue:'keep', buttons:[{label:'Keep editing', value:'keep'}, {label:'Discard', value:'discard'}, {label: why==='signout'? 'Save and sign out' : 'Save and continue', value:'save', primary:true}]});
  if(r.value==='keep'){ restoreForm(); return false; }
  if(r.value==='discard'){ if(dirty.includes('progress') && FORM.mode==='pours') PG.key = ''; return true; }
  const next = {date: dateInput.value, tower: towerSelect.value, modeSel: entryModeSel.value};
  restoreForm();                               // save against the day and tower the changes belong to
  if(!(await saveSections(dirty))) return false;
  dateInput.value = next.date; towerSelect.value = next.tower; entryModeSel.value = next.modeSel;
  return true;
}
/* Exports and entries files hold saved data only: offer to save what's on screen first. */
async function saveBeforeAction(what){
  const dirty = DATED.concat(LOGS).filter(isDirty); if(!dirty.length) return true;
  const r = await uiDialog({title:'Save your changes first?', message:`Unsaved changes aren’t included in ${what}:\n`+dirty.map(k=> '• '+sectionWhere(k)).join('\n'),
    cancelValue:false, buttons:[{label:'Cancel', value:false}, {label:'Continue without them', value:'go'}, {label:'Save first', value:'save', primary:true}]});
  if(r.value==='go') return true;
  if(r.value!=='save') return false;
  return saveSections(dirty);
}
let exportBypass = false;
document.getElementById('exportBtn').addEventListener('click', async e=>{
  if(exportBypass || !anyUnsaved()) return;
  e.stopImmediatePropagation(); e.preventDefault();
  if(!(await saveBeforeAction('the export'))) return;
  exportBypass = true;
  try{ document.getElementById('exportBtn').click(); } finally { exportBypass = false; }
}, true);

/* ---------- date: step a day, back to today ---------- */
function stepDate(n){
  const d = entryDate();
  dateInput.value = n===0? todayStr() : U.addDays(d, n);
  dateInput.dispatchEvent(new Event('change'));
}
function syncDateControls(){
  const t = document.getElementById('dateToday'); if(t) t.disabled = dateInput.value===todayStr();
}
document.getElementById('datePrev').addEventListener('click', ()=> stepDate(-1));
document.getElementById('dateNext').addEventListener('click', ()=> stepDate(1));
document.getElementById('dateToday').addEventListener('click', ()=>{ if(dateInput.value!==todayStr()) stepDate(0); });

/* ---------- day status: what's saved for the selected day ---------- */
function progressTowersFor(){
  if(ME && ME.role==='engineer' && (ME.towers||[]).length){ const m = ME.towers.filter(t=> CFG.towers.includes(t)); if(m.length) return m; }
  return CFG.towers.slice();
}
function towerReported(t, date){
  if(isHistoryDate(date)) return true;
  const rec = store.progress[t+'|'+date];
  if(rec && Object.keys(rec).some(s=> entryAch(rec, s)>0)) return true;
  const p = 'p|'+t+'|'+date+'|';
  return Object.keys(store.stamps).some(k=> k.startsWith(p));
}
function renderDayStrip(d){
  const box = document.getElementById('dayCheck'); if(!box) return;
  const date = dateInput.value;
  const fixed = !date? '' : isHistoryDate(date)? '<span class="dchip lock"><i class="led"></i>Recorded in the project workbook</span>' : null;
  if(fixed!==null){ if(box._html!==fixed){ box._html = fixed; box.innerHTML = fixed; } return; }
  d = d || dirtyMap();
  const closed = isClosedDate(date), chips = [];
  const towers = progressTowersFor(), done = towers.filter(t=> towerReported(t, date));
  chips.push({k:'progress', tab:'entry', label:'Progress', count: towers.length>1? `${done.length}/${towers.length}` : '',
    state: towers.length && done.length===towers.length? 'done' : done.length? 'part' : 'todo',
    title: towers.map(t=> (done.includes(t)? '✓ ' : '○ ')+t).join('\n')});
  const siteVisible = !ME || ME.role!=='engineer' || ME.siteWide!==false;
  if(siteVisible){
    [['labour','Labour', store.labour[date]!==undefined, 'labour|'], ['machinery','Machinery', store.machinery[date]!==undefined, 'mach|'], ['material','Material & staff', store.material[date]!==undefined, 'mat|']]
      .forEach(([k,label,ok,sp])=> chips.push({k, tab:k, label, state: ok? 'done' : 'todo', title: ok? (savedByText(stampOf(sp+date)) || 'Saved') : 'Not saved for this day yet'}));
    const nC = (store.concrete||[]).filter(r=> r.date===date).length, nR = (store.rain||[]).filter(r=> r.date===date).length;
    if(nC) chips.push({k:'concrete', tab:'sitelogs', sub:'concrete', label:'Concrete', count:String(nC), state:'info', title: nC+' pour(s) in the concrete log for this day'});
    if(nR) chips.push({k:'rain', tab:'sitelogs', sub:'rain', label:'Rain', count:String(nR), state:'info', title: nR+' rain event(s) for this day'});
  }
  const html = chips.map(c=> `<button type="button" class="dchip ${c.state}${d[c.k]? ' unsaved' : ''}${closed? ' closed' : ''}" data-k="${c.k}" data-tab="${c.tab}"${c.sub? ` data-sub="${c.sub}"` : ''}
      title="${escH((c.title||'')+(d[c.k]? '\nUnsaved changes' : '')+(closed? '\n'+fmtMonth(date.slice(0,7))+' is closed' : ''))}"><i class="led"></i>${escH(c.label)}${c.count? ` <b>${escH(c.count)}</b>` : ''}${d[c.k]? '<em>unsaved</em>' : ''}</button>`).join('');
  if(box._html===html) return;            // unchanged: keep the buttons (and keyboard focus) as they are
  box._html = html; box.innerHTML = html;
  box.querySelectorAll('.dchip[data-tab]').forEach(b=> b.addEventListener('click', ()=> b.dataset.k==='progress'? openTowerMenu(b) : goTab(b.dataset.tab, b.dataset.sub)));
}
function goTab(tab, sub){
  const t = document.querySelector(`.tab[data-tab="${tab}"]`); if(t && !t.classList.contains('active')) t.click();
  if(sub){ const s = document.querySelector(`.subtab[data-sub="${sub}"]`); if(s && !s.classList.contains('active')) s.click(); }
}
function closePopMenu(){ const m = document.getElementById('popMenu'); if(m) m.remove(); document.removeEventListener('mousedown', popMenuOutside, true); }
function popMenuOutside(e){ const m = document.getElementById('popMenu'); if(m && !m.contains(e.target) && !e.target.closest('.dchip')) closePopMenu(); }
function openTowerMenu(anchor){
  if(document.getElementById('popMenu')){ closePopMenu(); return; }
  const towers = progressTowersFor(), date = dateInput.value;
  if(towers.length<2){ goTab('entry'); if(towers[0] && towerSelect.value!==towers[0]){ towerSelect.value = towers[0]; towerSelect.dispatchEvent(new Event('change')); } return; }
  const r = anchor.getBoundingClientRect();
  const m = document.createElement('div'); m.id = 'popMenu'; m.className = 'menu-pop'; m.setAttribute('role','menu');
  m.innerHTML = towers.map(t=>{ const ok = towerReported(t, date);
    return `<button type="button" role="menuitem" data-t="${escH(t)}" ${t===towerSelect.value? 'aria-current="true"' : ''}><span class="mi-state ${ok? 'ok' : 'no'}">${ok? '✓' : '○'}</span>${escH(t)}</button>`; }).join('');
  m.style.top = (r.bottom + 8)+'px';
  m.style.left = Math.max(12, Math.min(r.left, window.innerWidth - 230))+'px';
  document.body.appendChild(m);
  m.querySelectorAll('button').forEach(b=> b.addEventListener('click', ()=>{
    closePopMenu(); goTab('entry');
    if(towerSelect.value!==b.dataset.t){ towerSelect.value = b.dataset.t; towerSelect.dispatchEvent(new Event('change')); }
  }));
  m.addEventListener('keydown', e=>{
    const items = [...m.querySelectorAll('button')], i = items.indexOf(document.activeElement);
    if(e.key==='Escape'){ closePopMenu(); anchor.focus(); }
    else if(e.key==='ArrowDown'){ e.preventDefault(); (items[i+1]||items[0]).focus(); }
    else if(e.key==='ArrowUp'){ e.preventDefault(); (items[i-1]||items[items.length-1]).focus(); }
  });
  setTimeout(()=> document.addEventListener('mousedown', popMenuOutside, true), 0);
  (m.querySelector('[aria-current="true"]') || m.querySelector('button')).focus();
}

/* ---------- progress item list: find and filter ---------- */
let ITEM_F = '';
function itemFilterPref(){ try{ return localStorage.getItem('dpr_item_filter') || ''; }catch(e){ return ''; } }
function setItemFilter(f){ ITEM_F = f; try{ localStorage.setItem('dpr_item_filter', f); }catch(e){} applyItemFilter(); }
function plannedSnosInMonth(tower, ym){
  const set = new Set(), n = daysInMonth(ym);
  for(let d=1; d<=n; d++){
    const ds = ym+'-'+String(d).padStart(2,'0');
    CFG.items.forEach(it=>{ if(!set.has(it.sno) && getPlanned(tower, ds, it.sno)>0) set.add(it.sno); });
  }
  return set;
}
function applyItemFilter(){
  const tools = document.getElementById('itemTools'); if(!tools) return;
  const rows = [...entryBody.querySelectorAll('tr[data-sno]')];
  const q = (document.getElementById('itemSearch').value||'').trim().toLowerCase();
  const has = tr=>{ const i = tr.querySelector('.today-input'); return (i && i.value!=='') || (+tr.dataset.others>0) || tr.classList.contains('has-entry'); };
  const inMonth = tr=> tr.dataset.pm==='1' || has(tr);
  const pmCount = rows.filter(tr=> tr.dataset.pm==='1').length;
  const counts = {month: pmCount? rows.filter(inMonth).length : 0, entered: rows.filter(has).length, all: rows.length};
  let f = ITEM_F || itemFilterPref() || (pmCount? 'month' : 'all');
  if(f==='month' && !pmCount) f = 'all';      // nothing planned this month: show everything
  let shown = 0;
  rows.forEach(tr=>{
    const vis = q? (String(tr.dataset.sno)===q || (tr.dataset.q||'').includes(q)) : f==='all'? true : f==='month'? inMonth(tr) : has(tr);
    tr.hidden = !vis; if(vis) shown++;
  });
  tools.querySelectorAll('#itemFilter button').forEach(b=>{
    const on = !q && b.dataset.f===f;
    b.classList.toggle('active', on); b.setAttribute('aria-pressed', String(on));
    b.querySelector('b').textContent = counts[b.dataset.f];
    if(b.dataset.f==='month'){ b.disabled = !pmCount; b.title = pmCount? 'Items with a planned quantity this month, plus anything already entered' : 'No plan is set for this month yet'; }
  });
  document.getElementById('itemFilterInfo').innerHTML = q? `${shown} match${shown===1? '' : 'es'}` : (shown<rows.length? `Showing ${shown} of ${rows.length} items` : '');
  let empty = document.getElementById('itemEmptyRow');
  if(!shown && rows.length){
    if(!empty){ empty = document.createElement('tr'); empty.id = 'itemEmptyRow'; entryBody.appendChild(empty); }
    empty.innerHTML = `<td colspan="9" class="hint" style="text-align:center; padding:18px;">${q? 'No item matches that search.' : f==='entered'? 'Nothing entered for this day yet.' : 'No items to show.'} <button type="button" class="linkbtn" id="itemShowAll">Show all items</button></td>`;
    empty.querySelector('#itemShowAll').onclick = ()=>{ document.getElementById('itemSearch').value = ''; setItemFilter('all'); };
  } else if(empty) empty.remove();
}
document.querySelectorAll('#itemFilter button').forEach(b=> b.addEventListener('click', ()=>{ document.getElementById('itemSearch').value = ''; setItemFilter(b.dataset.f); }));
(function(){
  const s = document.getElementById('itemSearch');
  s.addEventListener('input', applyItemFilter);
  s.addEventListener('keydown', e=>{
    if(e.key==='Escape' && s.value){ e.preventDefault(); s.value = ''; applyItemFilter(); return; }
    if(e.key==='Enter' || e.key==='ArrowDown'){
      const first = [...entryBody.querySelectorAll('tr[data-sno]:not([hidden]) .today-input')][0];
      if(first){ e.preventDefault(); first.focus(); try{ first.select(); }catch(_){} }
    }
  });
})();

/* ---------- keyboard: Enter and arrows move down a column, Ctrl+S saves, / finds an item ---------- */
function moveInGrid(t, dir){
  const grid = gridFor(t); if(!grid) return false;
  let r = -1, c = -1;
  for(let i=0; i<grid.length; i++){ const j = grid[i].indexOf(t); if(j>=0){ r = i; c = j; break; } }
  if(r<0) return false;
  let r2 = r + dir;
  while(grid[r2] && !(grid[r2][c] && grid[r2][c].offsetParent!==null && !grid[r2][c].disabled)) r2 += dir;
  const next = grid[r2] && grid[r2][c];
  if(!next) return null;
  next.focus(); try{ next.select(); }catch(e){}
  return true;
}
document.addEventListener('keydown', e=>{
  const t = e.target;
  if(!(t && t.tagName==='INPUT' && t.type==='number') || e.altKey || e.ctrlKey || e.metaKey) return;
  if(e.key!=='Enter' && e.key!=='ArrowDown' && e.key!=='ArrowUp') return;
  if(t.closest('.dlg-overlay, #authOverlay')) return;
  const dir = (e.key==='ArrowUp' || (e.key==='Enter' && e.shiftKey))? -1 : 1;
  const moved = moveInGrid(t, dir);
  if(moved===false) return;
  e.preventDefault();
  if(moved===null && e.key==='Enter' && dir>0) flash('End of the list — press Ctrl+S to save');
});
/* A scroll of the mouse wheel over a focused number box changes its value in some browsers. */
document.addEventListener('wheel', e=>{ const t = e.target; if(t && t.tagName==='INPUT' && t.type==='number' && document.activeElement===t) t.blur(); }, {passive:true});
function activeSaveKey(){
  const tab = (document.querySelector('.tab.active')||{dataset:{}}).dataset.tab;
  if(tab==='entry') return 'progress';
  if(tab==='labour' || tab==='machinery' || tab==='material') return tab;
  if(tab==='sitelogs') return (document.querySelector('.subtab.active')||{dataset:{}}).dataset.sub || '';
  return '';
}
document.addEventListener('keydown', e=>{
  if(!((e.ctrlKey || e.metaKey) && !e.altKey && !e.shiftKey && (e.key==='s' || e.key==='S'))) return;
  e.preventDefault();
  if(document.querySelector('.dlg-overlay') || !authOverlay().hidden || settingsOverlay.style.display==='flex') return;
  const k = activeSaveKey();
  if(!k){ flash('Nothing to save on this tab'); return; }
  if(k==='progress'? !can('progress', towerSelect.value) : !can('site')){ flash(k==='progress'? denyText('progress', towerSelect.value) : denyText('site')); return; }
  SAVE_FN[k]();
});
document.addEventListener('keydown', e=>{
  if(e.key!=='/' || e.ctrlKey || e.metaKey || e.altKey) return;
  const t = e.target; if(t && (/^(INPUT|TEXTAREA|SELECT)$/.test(t.tagName) || t.isContentEditable)) return;
  if(!document.getElementById('panel-entry').classList.contains('active') || FORM.mode==='pours') return;
  if(document.querySelector('.dlg-overlay') || !authOverlay().hidden || settingsOverlay.style.display==='flex') return;
  e.preventDefault(); const s = document.getElementById('itemSearch'); s.focus(); s.select();
});

/* ---------- labour: start from the last saved day ---------- */
const hasCrew = rows=> (rows||[]).some(x=> (x.contractor||'').trim() || Object.keys(x.counts||{}).length);
function renderLabourNote(date){
  const src = store.labour[date]===undefined? lastDateWith(store.labour, date, hasCrew) : '';
  if(!src){ setDayNote('labourNote', ''); return; }
  setDayNote('labourNote', `Nothing saved for ${escH(dayLabel(date))} yet.${can('site')? ` <button type="button" class="linkbtn" id="labourCopyLink">Copy the crews from ${escH(dayLabel(src))}</button>` : ''}`);
  const b = document.getElementById('labourCopyLink'); if(b) b.onclick = copyLastLabour;
}
async function copyLastLabour(){
  if(!need('site')) return;
  const date = dateInput.value, src = lastDateWith(store.labour, date, hasCrew);
  if(!src){ uiAlert('No labour report is saved before '+dayLabel(date)+' yet.', 'Nothing to copy'); return; }
  const onScreen = collectLabour().rows.length;
  const r = await uiDialog({title:'Copy labour from '+dayLabel(src)+'?',
    message:(onScreen? 'The crew rows on screen are replaced. ' : '')+'Copy each crew with its head counts, or just the crew list so you can type today’s counts. Nothing is saved until you press Save.',
    cancelValue:false, buttons:[{label:'Cancel', value:false}, {label:'Crews only', value:'crews'}, {label:'Crews and counts', value:'all', primary:true}]});
  if(!r.value) return;
  const rows = (store.labour[src]||[]).filter(x=> (x.contractor||'').trim() || (x.category||'').trim() || Object.keys(x.counts||{}).length);
  labourBody.innerHTML = '';
  rows.forEach(x=> addLabourRow({contractor:x.contractor, tower:x.tower, category:x.category, counts: r.value==='all'? Object.assign({}, x.counts) : {}}));
  if(!rows.length) addLabourRow();
  scheduleDirtyUI();
  flash(`Copied ${rows.length} crew row(s) from ${dayLabel(src)} — check them and press Save`);
  const first = labourBody.querySelector('.labourCount'); if(first) first.focus();
}

/* ---------- screen lock on shared computers ---------- */
function lockKey(){ return 'dpr_locked_'+CFG.projectId; }
function setLockFlag(id){
  try{ if(id){ sessionStorage.setItem(lockKey(), id); localStorage.setItem(lockKey(), id); } else { sessionStorage.removeItem(lockKey()); localStorage.removeItem(lockKey()); } }catch(e){}
}
function lockFlag(){ try{ return sessionStorage.getItem(lockKey()) || localStorage.getItem(lockKey()) || ''; }catch(e){ return ''; } }
function autoLockMins(){ return +((CFG.team && CFG.team.autoLock) || 0); }
let lastActivity = Date.now();
['pointerdown','keydown','wheel','touchstart'].forEach(ev=> document.addEventListener(ev, ()=>{ lastActivity = Date.now(); }, {capture:true, passive:true}));
setInterval(()=>{
  const mins = autoLockMins();
  if(!mins || !ME || ME.id==='viewer' || !authOverlay().hidden) return;
  if(Date.now() - lastActivity >= mins*60000) lockScreen();
}, 10000);
function lockScreen(){
  if(!ME || ME.id==='viewer') return;
  const u = ME; setLockFlag(u.id); closeUserMenu(); closePopMenu();
  const pending = DATED.concat(LOGS).filter(isDirty);
  const mins = autoLockMins();
  const o = authShell(`
    <p class="auth-q">This portal is locked</p>
    <div class="lock-who">${avatarHtml(u, 'lg')}<div><b>${escH(u.name)}</b><div class="hint" style="margin:2px 0 0;">${escH(ROLE_LABEL[u.role])}${mins? ` &middot; locked after ${mins} minutes without use` : ''}</div></div></div>
    <form class="auth-pin" id="lockForm" autocomplete="off">
      <div class="field"><label for="lockSecret">${u.pin? 'PIN' : 'Password'}</label><input type="password" id="lockSecret" autocomplete="current-password"${u.pin? ' inputmode="numeric"' : ''}></div>
      <button class="btn blue" type="submit">Unlock</button>
    </form>
    <div class="err-text" id="lockErr" role="alert"></div>
    ${pending.length? `<p class="hint">Unsaved changes are waiting: ${escH(pending.map(k=> SEC_LABEL[k]).join(', '))}. Unlock to save them.</p>` : ''}
    <div class="auth-foot" id="lockFoot"><button class="linkbtn" type="button" id="lockSwitch">Not ${escH(u.name)}? Sign in as someone else</button></div>`);
  o.classList.add('lock');
  const inp = o.querySelector('#lockSecret'), err = o.querySelector('#lockErr');
  o.querySelector('#lockForm').addEventListener('submit', async e=>{
    e.preventDefault();
    const f = authFails[u.id] || {n:0, until:0};
    if(Date.now() < f.until){ err.textContent = `Too many attempts. Try again in ${Math.ceil((f.until-Date.now())/1000)} seconds.`; return; }
    if(await checkSecret(u.secret, inp.value)){
      authFails[u.id] = {n:0, until:0}; setLockFlag(''); o.classList.remove('lock'); hideAuth(); lastActivity = Date.now();
      flash('Unlocked — welcome back, '+u.name.split(' ')[0]);
    } else {
      f.n++; if(f.n>=5){ f.until = Date.now()+30000; f.n = 0; }
      authFails[u.id] = f;
      err.textContent = (u.pin? 'That PIN' : 'That password')+' isn’t right.'+(f.until>Date.now()? ' Wait 30 seconds before trying again.' : '');
      inp.select();
    }
  });
  const switchUser = ()=>{ o.classList.remove('lock'); setLockFlag(''); signOut(true, {force:true}); };
  o.querySelector('#lockSwitch').onclick = ()=>{
    if(!pending.length){ switchUser(); return; }
    const foot = o.querySelector('#lockFoot');
    foot.innerHTML = `<div class="lock-warn">Signing in as someone else discards ${escH(u.name)}’s unsaved changes (${escH(pending.map(k=> SEC_LABEL[k]).join(', '))}).<br>
      <button class="btn secondary" type="button" id="lockCancel">Cancel</button><button class="btn danger" type="button" id="lockDiscard">Discard and switch</button></div>`;
    foot.querySelector('#lockCancel').onclick = ()=> lockScreen();
    foot.querySelector('#lockDiscard').onclick = switchUser;
  };
  setTimeout(()=> inp.focus(), 30);
}
