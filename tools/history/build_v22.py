import re, sys
SP = '/tmp/claude-0/-home-claude/56db3af5-e95d-5731-bda3-4d43f7b29fb9/scratchpad'
SRC = '/mnt/user-data/outputs/dpr_portal_v2.1.html'
DST = '/mnt/user-data/outputs/dpr_portal_v2.2.html'
s = open(SRC, encoding='utf-8').read()

def rep(old, new, cnt=1):
    global s
    n = s.count(old)
    assert n == cnt, (n, old[:160])
    s = s.replace(old, new)

def rep_between(start, end, new):
    """Replace the text from start (inclusive) up to end (exclusive); start must be unique."""
    global s
    assert s.count(start) == 1, ('start', s.count(start), start[:120])
    a = s.index(start); b = s.index(end, a)
    s = s[:a] + new + s[b:]

# ---------------------------------------------------------------- CSS
css = open(SP+'/v22/entry.css', encoding='utf-8').read()
rep("@media (prefers-reduced-motion: reduce){", css.strip()+"\n\n@media (prefers-reduced-motion: reduce){")

# ---------------------------------------------------------------- HTML
CHEV_L = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="15 5 8 12 15 19"/></svg>'
CHEV_R = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="9 5 16 12 9 19"/></svg>'
rep('''  <div class="controls">
    <div class="field">
      <label for="dateInput">Entry date</label>
      <input type="date" id="dateInput">
    </div>
    <div class="spacer"></div>
    <div class="field" style="align-items:flex-end;">''', f'''  <div class="controls day-bar">
    <div class="field">
      <label for="dateInput">Entry date</label>
      <div class="date-step">
        <button type="button" class="step-btn" id="datePrev" title="Previous day" aria-label="Previous day">{CHEV_L}</button>
        <input type="date" id="dateInput">
        <button type="button" class="step-btn" id="dateNext" title="Next day" aria-label="Next day">{CHEV_R}</button>
        <button type="button" class="btn ghost today-btn" id="dateToday" title="Go to today">Today</button>
      </div>
    </div>
    <div class="field day-field">
      <label>Day status</label>
      <div class="day-check" id="dayCheck" aria-label="What is saved for this day"></div>
    </div>
    <div class="field export-field" style="align-items:flex-end;">''')
rep('<button class="btn blue needs-entry" id="saveBtn">Save progress entry</button>',
    '<button class="btn blue needs-entry" id="saveBtn" title="Save (Ctrl+S)">Save progress entry</button>')
SEARCH_ICON = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" aria-hidden="true"><circle cx="11" cy="11" r="7"/><line x1="16.5" y1="16.5" x2="21" y2="21"/></svg>'
rep('''    <div class="table-scroll" id="towerTableWrap">''', f'''    <div class="list-tools" id="itemTools">
      <label class="search-box">{SEARCH_ICON}<input type="search" id="itemSearch" placeholder="Find an item: name, BOQ no. or #" aria-label="Find an item" autocomplete="off"></label>
      <div class="pill-group" id="itemFilter" role="group" aria-label="Which items to show">
        <button type="button" data-f="month" title="Items with a planned quantity this month, plus anything already entered">Planned this month <b></b></button>
        <button type="button" data-f="entered" title="Items with a quantity for this day">Entered <b></b></button>
        <button type="button" data-f="all">All items <b></b></button>
      </div>
      <span class="hint" id="itemFilterInfo"></span>
    </div>
    <div class="table-scroll" id="towerTableWrap">''')
rep('''            <td class="num" id="footBefore">0</td>
            <td class="num" id="footPct">0%</td>
            <td class="num" id="footPlanned">0</td>
            <td class="num" id="footToday">0</td>''', '''            <td class="num" id="footBefore" data-label="Before today">0</td>
            <td class="num" id="footPct" data-label="Complete">0%</td>
            <td class="num" id="footPlanned" data-label="Planned">0</td>
            <td class="num" id="footToday" data-label="Today">0</td>''')
rep('''&middot; Planned is fixed for the month and can only be changed via <b>Edit monthly plan</b> above, which is password-protected and logs every change.</div>''',
    '''&middot; Planned is fixed for the month: only a planning manager changes it, through <b>Edit monthly plan</b>, and every change is logged. &middot; Keys: <kbd>Enter</kbd> or <kbd>&darr;</kbd> moves down the list, <kbd>Ctrl</kbd>+<kbd>S</kbd> saves, <kbd>/</kbd> jumps to the item search.</div>''')

# labour: copy last day, note
rep('''        <button class="btn secondary" id="addLabourRow">+ Add crew row</button>
        <button class="btn blue" id="saveLabourBtn">Save labour report</button>''', '''        <button class="btn secondary" id="copyLabourBtn" title="Copy the crews from the last day that was saved">Copy last day</button>
        <button class="btn secondary" id="addLabourRow">+ Add crew row</button>
        <button class="btn blue" id="saveLabourBtn" title="Save (Ctrl+S)">Save labour report</button>''')
rep('''    <div class="saved-by empty" id="labourSavedBy"></div>''', '''    <div class="saved-by empty" id="labourSavedBy"></div>
    <div class="day-note" id="labourNote" hidden></div>''')
rep('''One row per contractor crew present today. Day shift 8AM&ndash;8PM, night shift 8PM&ndash;8AM.</div>''',
    '''One row per contractor crew present today. Day shift 8AM&ndash;8PM, night shift 8PM&ndash;8AM. Empty rows aren&rsquo;t saved.</div>''')
# machinery
rep('''Count of each equipment type deployed on site today. Prefilled from the last recorded value &mdash; adjust as needed.</div>
      <button class="btn blue" id="saveMachineryBtn">Save machinery report</button>''', '''Count of each equipment type deployed on site today. A day that isn&rsquo;t saved yet starts from the last saved day &mdash; adjust as needed.</div>
      <button class="btn blue" id="saveMachineryBtn" title="Save (Ctrl+S)">Save machinery report</button>''')
rep('''    <div class="saved-by empty" id="machSavedBy"></div>''', '''    <div class="saved-by empty" id="machSavedBy"></div>
    <div class="day-note" id="machNote" hidden></div>''')
# material
rep('''    <fieldset class="pfs" id="fsMaterial">''', '''    <fieldset class="pfs" id="fsMaterial">
    <div class="day-note" id="matNote" hidden></div>''')
rep('''<button class="btn blue" id="saveMaterialBtn">''', '''<button class="btn blue" id="saveMaterialBtn" title="Save (Ctrl+S)">''')
for b in ['saveConcreteBtn','saveRainBtn','saveHindranceBtn','saveBbsBtn']:
    rep(f'<button class="btn blue" id="{b}">', f'<button class="btn blue" id="{b}" title="Save (Ctrl+S)">')

rep('<div id="authOverlay" class="auth-overlay" hidden></div>', '<div id="authOverlay" class="auth-overlay" hidden></div>\n<button type="button" id="fabSave" class="fab-save" hidden></button>')
rep("el.innerHTML=`<span class=\"led\"></span>PERIOD ${fmtMonth(p).toUpperCase()}", "el.innerHTML=`<span class=\"led\"></span><span class=\"pp-word\">PERIOD </span>${fmtMonth(p).toUpperCase()}")

# version
rep('title="What&rsquo;s new">v2.1</button>', 'title="What&rsquo;s new">v2.2</button>')
rep('<span class="ver">DPR Portal v2.1</span>', '<span class="ver">DPR Portal v2.2</span>')
rep("const APP_VERSION = '2.1';", "const APP_VERSION = '2.2';")
rep("""const CHANGELOG = [
  {v:'v2.1',""", """const CHANGELOG = [
  {v:'v2.2', date:'19 Oct 2026', items:[
    'Day status at the top shows what is saved for the selected day (progress per tower, labour, machinery, material & staff) and takes you straight to what is missing.',
    'Step through dates with the arrows beside the date, or jump back to Today.',
    'Unsaved changes are marked on their tab. Changing the date or tower, signing out, exporting or sending entries first offers to save them. Ctrl+S saves the tab you are on.',
    'Progress item list: find an item by name, BOQ number or #, and show only the items planned this month or already entered.',
    'Faster keyboard entry: Enter and the arrow keys move down the column in the progress, labour, machinery, material and staff lists, and the mouse wheel no longer changes a number by accident.',
    'Labour can be copied from the last saved day, with or without the head counts. Machinery and staff on site start from the last saved day instead of fixed defaults.',
    'Soft checks: an entry that takes an item past its BOQ quantity, or ten times its plan for the day, is highlighted and confirmed before saving. Future dates are flagged.',
    'On phones the progress item list and the labour table become cards that are easier to fill in, and a floating Save button follows you down long lists.',
    'Planning managers can make the portal lock after a spell without use (Team & access, Shared computers). Unlocking keeps anything typed but not saved.',
    'Fixes: machinery counts saved as zero no longer come back as defaults; empty starter rows are no longer saved as labour crews; new site-log rows start on the entry date; numbers pasted into material and staff lists fill down the list.']},
  {v:'v2.1',""")

# ---------------------------------------------------------------- JS: controls and guards
rep("""dateInput.addEventListener('change', async ()=>{ if(typeof pgGuard==='function' && !(await pgGuard((t,d)=>{ dateInput.value=d; }))) return; renderAll(); });""",
    """dateInput.addEventListener('change', async ()=>{
  if(!dateInput.value){ dateInput.value = FORM.date || todayStr(); return; }
  if(dateInput.value===FORM.date) return;
  if(!(await leaveGuard('date'))) return;
  renderAll();
});""")
rep("""towerSelect.addEventListener('change', async ()=>{ if(!(await pgGuard(t=>{ towerSelect.value=t; }))) return; renderEntry(); });""",
    """towerSelect.addEventListener('change', async ()=>{ if(!(await leaveGuard('tower'))) return; renderEntry(); });""")
rep("""entryModeSel.addEventListener('change', renderEntry);""",
    """entryModeSel.addEventListener('change', async ()=>{ if(!(await leaveGuard('mode'))) return; renderEntry(); });""")
rep("""  document.getElementById('saveBtn').classList.toggle('pulse', n>0);
}""", """  document.getElementById('saveBtn').classList.toggle('pulse', n>0);
  if(typeof scheduleDirtyUI==='function') scheduleDirtyUI();
}""")
rep("""window.addEventListener('beforeunload', e=>{ if(pgUnsaved()){ e.preventDefault(); e.returnValue=''; } });\n""", "")

# ---------------------------------------------------------------- JS: progress entry
rep_between("function renderEntry(){", "function recalcEntryRow(tr, it, before){", r"""function renderEntry(){
  const tower = towerSelect.value, date = dateInput.value;
  const hasPours = poursOf(tower).length>0;
  document.getElementById('entryModeField').style.display = hasPours? '' : 'none';
  const mode = entryMode();
  Object.assign(FORM, {tower, date, mode, modeSel: entryModeSel.value});
  document.getElementById('towerTableWrap').style.display = mode==='pours'? 'none' : '';
  document.getElementById('itemTools').style.display = mode==='pours'? 'none' : '';
  document.getElementById('pourGridWrap').style.display = mode==='pours'? '' : 'none';
  const noAccess = !can('progress', tower);
  const locked = isLockedDate(date) || noAccess;
  const warnBanner = document.getElementById('pastDateWarning'), today = todayStr();
  if(!locked && date!==today){
    warnBanner.innerHTML = date<today
      ? `&#9888; You&rsquo;re entering data for <b>${escH(dayLabel(date))}</b>, ${escH(relDay(date))}. Double-check this is intentional before saving.`
      : `&#9888; <b>${escH(dayLabel(date))}</b> is in the future (${escH(relDay(date))}). Progress is normally entered on or after the day the work is done.`;
    warnBanner.style.display = 'block';
  } else warnBanner.style.display = 'none';
  document.getElementById('saveBtn').disabled = locked;
  document.getElementById('clearTodayBtn').disabled = locked;
  const lockedNote = document.getElementById('lockedDateNote');
  lockedNote.style.display = locked ? 'block' : 'none';
  lockedNote.innerHTML = !locked? '' : isHistoryDate(date)
    ? 'This date is already recorded in the project workbook and is shown read-only below — it\'s part of the cumulative baseline, so there\'s nothing to enter here.'
    : isClosedDate(date)? '&#128274; <b>'+fmtMonth(date.slice(0,7))+' is closed.</b> Entries are shown read-only. A planning manager can reopen the period if a correction is needed.'
    : '&#128274; <b>View only.</b> '+escH(denyText('progress', tower));
  lockedNote.style.background = isHistoryDate(date)? 'var(--green-soft)' : isClosedDate(date)? 'var(--amber-soft)' : 'var(--blue-wash)';
  setSavedBy('entrySavedBy', latestStamp('p|'+tower+'|'+date+'|'));
  if(mode==='pours'){ renderPourGrid(tower, date, locked); scheduleDirtyUI(); return; }

  entryBody.dataset.mode = 'tower';
  entryBody.innerHTML = '';
  const pm = plannedSnosInMonth(tower, date.slice(0,7));
  CFG.items.forEach(it=>{
    let planned = getPlanned(tower, date, it.sno);
    const before = achievedBefore(tower, it.sno, date);
    const hist = !locked ? null : (isHistoryDate(date) ? historicalTowerPA(tower, date, it.sno)
                 : {p:planned, a:entryAch(store.progress[tower+'|'+date], it.sno)});
    if(locked && hist && isHistoryDate(date)) planned = hist.p;
    const value = currentTodayVals(tower, date, it.sno).a, lockedAch = hist? hist.a : 0;
    const others = locked? 0 : otherLocsToday(tower, date, it.sno);
    const hasEntry = locked ? (lockedAch>0) : (value !== '' || others>0);
    const tr = document.createElement('tr');
    if(hasEntry) tr.classList.add('has-entry');
    tr.dataset.sno = it.sno; tr.dataset.before = before; tr.dataset.planned = planned;
    tr.dataset.lockedAch = lockedAch; tr.dataset.budget = 0; tr.dataset.others = others;
    tr.dataset.pm = pm.has(it.sno)? '1' : '';
    tr.dataset.q = [it.sno, it.boq_id, it.short, it.desc].join(' ').toLowerCase();
    const uom = escH(it.uom);
    const achievedCell = locked
      ? `<td class="num plan-cell c-today" data-label="Today · ${uom}" title="Locked — recorded in the workbook or in a closed period">${lockedAch? fmt(lockedAch): '—'}</td>`
      : `<td class="num c-today" data-label="Today · ${uom}"><input type="number" class="today-input ${value!==''?'has-value':''}" min="0" step="any" data-sno="${it.sno}" value="${value}"${value!==''? ` data-saved="1" data-orig="${value}"` : ''} placeholder="0" aria-label="${escH(it.short)}, today (${uom})" title="${value!==''?'Already entered for this date':''}">${others? `<div class="loc-note" title="Entered against pours in this tower today">+${fmt(others)} at pours</div>` : ''}</td>`;
    tr.innerHTML = `
      <td class="num c-sno">${it.sno}</td>
      <td class="item-desc c-item"><div class="short" title="${escH(it.desc)}">${escH(it.short)}</div><div class="boq">${escH(it.boq_id)}</div></td>
      <td class="c-uom">${uom}</td>
      <td class="num c-rate">${fmt(it.rate)}</td>
      <td class="num c-total">${fmt(it.total_qty)}</td>
      <td class="num c-before" data-label="Before today${it.total_qty>0? ' · BOQ '+fmt(it.total_qty) : ''}">${fmt(before)}</td>
      <td class="num pct-cell-holder c-pct"></td>
      <td class="num plan-cell c-plan" data-label="Planned" title="Fixed for the month — a planning manager sets it in Edit monthly plan">${planned? fmt(planned): '—'}</td>
      ${achievedCell}
    `;
    entryBody.appendChild(tr);
    recalcEntryRow(tr, it, before);
  });
  recalcEntryFooter();
  entryBody.querySelectorAll('.today-input').forEach(inp=> inp.addEventListener('input', ()=>{
    inp.classList.add('touched');
    const tr = inp.closest('tr');
    const it = CFG.items.find(i=>i.sno===parseInt(tr.dataset.sno,10));
    recalcEntryRow(tr, it, parseFloat(tr.dataset.before));
    recalcEntryFooter();
  }));
  applyItemFilter();
  snapSection('progress');
}
""")
rep_between("function recalcEntryRow(tr, it, before){", "function recalcEntryFooter(){", r"""function recalcEntryRow(tr, it, before){
  const achInp = tr.querySelector('.today-input');
  const a = achInp ? (parseFloat(achInp.value)||0) : (parseFloat(tr.dataset.lockedAch)||0);
  const inclToday = before + a + (parseFloat(tr.dataset.others)||0);
  tr.querySelector('.pct-cell-holder').innerHTML = it.total_qty>0? pctCellHtml(inclToday, it.total_qty) : '<span class="hint" style="margin:0;">—</span>';
  if(achInp){
    const over = it.total_qty>0 && a>0 && inclToday > it.total_qty + 1e-9;
    achInp.classList.toggle('over', over);
    achInp.title = over? `Takes the cumulative to ${fmt(inclToday)} ${it.uom}, past the BOQ quantity of ${fmt(it.total_qty)}` : (achInp.dataset.saved==='1'? 'Already entered for this date' : '');
  }
}
""")
rep("""  entryBody.querySelectorAll('.today-input').forEach(inp=> inp.value='');
  entryBody.querySelectorAll('tr[data-sno]').forEach(tr=>{
    const it = CFG.items.find(i=>i.sno===parseInt(tr.dataset.sno,10));
    recalcEntryRow(tr, it, parseFloat(tr.dataset.before));
  });
  recalcEntryFooter();
});""", """  entryBody.querySelectorAll('.today-input').forEach(inp=> inp.value='');
  entryBody.querySelectorAll('tr[data-sno]').forEach(tr=>{
    const it = CFG.items.find(i=>i.sno===parseInt(tr.dataset.sno,10));
    recalcEntryRow(tr, it, parseFloat(tr.dataset.before));
  });
  recalcEntryFooter(); scheduleDirtyUI();
  flash('Cleared the quantities on screen — nothing changes until you save');
});""")
rep_between("document.getElementById('saveBtn').addEventListener('click', ()=>{", "/* ---------- Structure tab ---------- */",
    "document.getElementById('saveBtn').addEventListener('click', ()=> saveProgress());\n\n")

# ---------------------------------------------------------------- JS: labour
rep_between("function addLabourRow(prefill){", "document.getElementById('addLabourRow')", r"""function addLabourRow(prefill){
  labourRowSeq++;
  const rid = 'lr'+labourRowSeq;
  const tr = document.createElement('tr');
  tr.dataset.rid = rid;
  let cells = `<td class="c-x"><span class="row-x" data-remove="${rid}" title="Remove this row">&times;</span></td>
    <td class="c-con" data-label="Contractor"><input type="text" class="contractorInput" style="width:150px;" value="${escH((prefill&&prefill.contractor)||'')}" placeholder="Contractor name"></td>
    <td class="c-twr" data-label="${escH(T('zone'))}"><select class="towerInputSel" style="min-width:70px;">${labourTowerOptionsHtml(prefill&&prefill.tower)}</select></td>
    <td class="c-cat" data-label="Category"><input type="text" class="categoryInput" style="width:130px;" value="${escH((prefill&&prefill.category)||'')}" placeholder="Crew type"></td>`;
  labourFieldDefs().forEach(f=>{
    const val = (prefill && prefill.counts && prefill.counts[f.key]) || '';
    const lab = (f.key[0]==='D'? 'Day ' : f.key[0]==='N'? 'Night ' : '')+f.label;
    cells += `<td class="c-n" data-label="${escH(lab)}"><input type="number" class="today-input small labourCount" min="0" data-field="${escH(f.key)}" value="${val}" aria-label="${escH(lab)}"></td>`;
  });
  cells += `<td class="num row-total c-tot" data-label="Total">0</td>`;
  tr.innerHTML = cells;
  labourBody.appendChild(tr);
  tr.querySelector('[data-remove]').addEventListener('click', ()=>{ tr.remove(); recalcLabourTotals(); });
  tr.querySelectorAll('.labourCount').forEach(inp=> inp.addEventListener('input', recalcLabourTotals));
  recalcLabourTotals();
}
""")
rep_between("function loadLabourForDate(date){", "/* ---- Contractor presets ---- */", r"""function loadLabourForDate(date){
  labourBody.innerHTML = '';
  const rows = store.labour[date];
  if(rows && rows.length){ rows.forEach(r=> addLabourRow(r)); }
  else { addLabourRow(); }
  renderLabourNote(date);
  snapSection('labour');
}

""")
rep_between("function loadLabourCampForDate(date){", "/* =================== MACHINERY =================== */", r"""function loadLabourCampForDate(date){
  labourCampBody.innerHTML = '';
  const rows = store.labourCamp[date];
  if(rows && rows.length){ rows.forEach(r=> addCampRow(r)); }
  else { addCampRow(); }
  snapSection('labour');
}

document.getElementById('saveLabourBtn').addEventListener('click', ()=> saveLabour());
document.getElementById('copyLabourBtn').addEventListener('click', ()=> copyLastLabour());

""")
rep("""    <td><input type="text" class="lcContractor" style="width:190px;" value="${(prefill&&prefill.contractor)||''}" placeholder="Contractor name"></td>
    <td><input type="text" class="lcCategory" style="width:140px;" value="${(prefill&&prefill.category)||''}" placeholder="Crew type"></td>
    <td><input type="number" class="today-input small lcCount" min="0" value="${(prefill&&prefill.count)||''}"></td>
    <td><input type="text" class="lcRemark" style="width:180px;" value="${(prefill&&prefill.remark)||''}" placeholder="Reason (optional)"></td>`;""",
    """    <td><input type="text" class="lcContractor" style="width:190px;" value="${escH((prefill&&prefill.contractor)||'')}" placeholder="Contractor name"></td>
    <td><input type="text" class="lcCategory" style="width:140px;" value="${escH((prefill&&prefill.category)||'')}" placeholder="Crew type"></td>
    <td><input type="number" class="today-input small lcCount" min="0" value="${(prefill&&prefill.count)||''}"></td>
    <td><input type="text" class="lcRemark" style="width:180px;" value="${escH((prefill&&prefill.remark)||'')}" placeholder="Reason (optional)"></td>`;""")

# ---------------------------------------------------------------- JS: machinery
rep_between("function loadMachineryForDate(date){", "function recalcMachineryTotal(){", r"""function loadMachineryForDate(date){
  machineryBody.innerHTML = '';
  const own = store.machinery[date];
  const src = own? '' : lastDateWith(store.machinery, date, r=> Object.keys(r||{}).length>0);
  const from = own || (src? store.machinery[src] : null);
  CFG.machinery.forEach(m=>{
    const val = from? (from[m.sno]!==undefined? from[m.sno] : '') : m.default;
    const tr = document.createElement('tr');
    tr.innerHTML = `<td class="num">${m.sno}</td><td>${escH(m.label)}</td><td>${escH(m.uom)}</td>
      <td class="num"><input type="number" class="today-input machineryCount" min="0" data-sno="${m.sno}" value="${val||''}" aria-label="${escH(m.label)}, count today"></td>`;
    machineryBody.appendChild(tr);
  });
  machineryBody.querySelectorAll('.machineryCount').forEach(inp=> inp.addEventListener('input', recalcMachineryTotal));
  recalcMachineryTotal();
  setDayNote('machNote', own? '' : src? `Not saved for ${escH(dayLabel(date))} yet. The counts are copied from ${escH(dayLabel(src))}: check them and save.`
    : CFG.machinery.some(m=> +m.default>0)? `Not saved for ${escH(dayLabel(date))} yet. The usual counts are filled in: check them and save.` : '');
  snapSection('machinery');
}
""")
rep_between("document.getElementById('saveMachineryBtn').addEventListener('click', ()=>{", "/* =================== MATERIAL & STAFF =================== */",
    "document.getElementById('saveMachineryBtn').addEventListener('click', ()=> saveMachinery());\n\n")

# ---------------------------------------------------------------- JS: material & staff
rep_between("function loadMaterialForDate(date){", "/* =================== OVERVIEW =================== */", r"""function loadMaterialForDate(date){
  materialRows.innerHTML = ''; staffRows.innerHTML = '';
  const saved = store.material[date], rec = saved || {};
  CFG.material_items.forEach(mi=>{
    const val = rec[mi.key] !== undefined ? rec[mi.key] : '';
    const row = document.createElement('div'); row.className='mat-row';
    row.innerHTML = `<label>${escH(mi.label)} <span class="uom">${escH(mi.uom)}</span></label><input type="number" class="today-input materialInput" min="0" step="any" data-key="${escH(mi.key)}" value="${val}" placeholder="0" aria-label="${escH(mi.label)} received (${escH(mi.uom)})">`;
    materialRows.appendChild(row);
  });
  document.getElementById('materialRemark').value = rec.remark || '';
  const hasStaff = r=> !!r && CFG.staff_roles.some(sr=> r[staffKey(sr)]!==undefined);
  const src = saved? '' : lastDateWith(store.material, date, hasStaff);
  const from = saved || (src? store.material[src] : null);
  CFG.staff_roles.forEach(sr=>{
    const key = staffKey(sr);
    const val = from? (from[key]!==undefined? from[key] : '') : sr.default;
    const row = document.createElement('div'); row.className='staff-row';
    row.innerHTML = `<label>${escH(sr.label)}</label><input type="number" class="today-input staffInput" min="0" data-key="${escH(key)}" value="${val==null? '' : val}" aria-label="${escH(sr.label)} on site">`;
    staffRows.appendChild(row);
  });
  setDayNote('matNote', saved? '' : src? `Not saved for ${escH(dayLabel(date))} yet. Staff numbers are copied from ${escH(dayLabel(src))}: check them, add the day&rsquo;s material and save.` : '');
  snapSection('material');
}
document.getElementById('saveMaterialBtn').addEventListener('click', ()=> saveMaterial());

""")

# ---------------------------------------------------------------- JS: site logs
rep("""    <td><input type="date" class="cDate" value="${(prefill&&prefill.date)||todayStr()}"></td>""",
    """    <td><input type="date" class="cDate" value="${(prefill&&prefill.date)||entryDate()}"></td>""")
rep("""    <td><input type="date" class="rDate" value="${(prefill&&prefill.date)||todayStr()}"></td>""",
    """    <td><input type="date" class="rDate" value="${(prefill&&prefill.date)||entryDate()}"></td>""")
rep("""    <td><input type="date" class="hStart" value="${(prefill&&prefill.start)||todayStr()}"></td>""",
    """    <td><input type="date" class="hStart" value="${(prefill&&prefill.start)||entryDate()}"></td>""")
rep("""    <td><input type="date" class="bDate" value="${(prefill&&prefill.date)||todayStr()}"></td>""",
    """    <td><input type="date" class="bDate" value="${(prefill&&prefill.date)||entryDate()}"></td>""")
rep_between("document.getElementById('saveConcreteBtn').addEventListener('click', ()=>{", "function loadConcrete(){",
    "document.getElementById('saveConcreteBtn').addEventListener('click', ()=> saveConcrete());\n")
rep("""function loadConcrete(){ concreteBody.innerHTML=''; (store.concrete.length? store.concrete: []).forEach(r=> addConcreteRow(r)); if(!store.concrete.length) addConcreteRow(); }""",
    """function loadConcrete(){ concreteBody.innerHTML=''; (store.concrete.length? store.concrete: []).forEach(r=> addConcreteRow(r)); if(!store.concrete.length) addConcreteRow(); snapSection('concrete'); }""")
rep_between("document.getElementById('saveRainBtn').addEventListener('click', ()=>{", "function loadRain(){",
    "document.getElementById('saveRainBtn').addEventListener('click', ()=> saveRain());\n")
rep("""function loadRain(){ rainBody.innerHTML=''; (store.rain.length? store.rain: []).forEach(r=> addRainRow(r)); if(!store.rain.length) addRainRow(); }""",
    """function loadRain(){ rainBody.innerHTML=''; (store.rain.length? store.rain: []).forEach(r=> addRainRow(r)); if(!store.rain.length) addRainRow(); snapSection('rain'); }""")
rep_between("document.getElementById('saveHindranceBtn').addEventListener('click', ()=>{", "function loadHindrance(){",
    "document.getElementById('saveHindranceBtn').addEventListener('click', ()=> saveHindrance());\n")
rep("""function loadHindrance(){ hindranceBody.innerHTML=''; (store.hindrance.length? store.hindrance: []).forEach(r=> addHindranceRow(r)); if(!store.hindrance.length) addHindranceRow(); }""",
    """function loadHindrance(){ hindranceBody.innerHTML=''; (store.hindrance.length? store.hindrance: []).forEach(r=> addHindranceRow(r)); if(!store.hindrance.length) addHindranceRow(); snapSection('hindrance'); }""")
rep_between("document.getElementById('saveBbsBtn').addEventListener('click', ()=>{", "function loadBbs(){",
    "document.getElementById('saveBbsBtn').addEventListener('click', ()=> saveBbs());\n")
rep("""function loadBbs(){ bbsBody.innerHTML=''; (store.bbs.length? store.bbs: []).forEach(r=> addBbsRow(r)); if(!store.bbs.length) addBbsRow(); }""",
    """function loadBbs(){ bbsBody.innerHTML=''; (store.bbs.length? store.bbs: []).forEach(r=> addBbsRow(r)); if(!store.bbs.length) addBbsRow(); snapSection('bbs'); }""")

# ---------------------------------------------------------------- JS: dialogs, sign-out, lock, team
rep("""    function onKey(e){
      if(e.key==='Escape'){""", """    function onKey(e){
      if(e.target && e.target.closest && e.target.closest('#authOverlay')) return;   // the screen lock sits above dialogs
      if(e.key==='Escape'){""")
rep("""async function signOut(toSignIn){
  if(typeof pgUnsaved==='function' && pgUnsaved()){
    if(!(await uiConfirm('You have unsaved pour entries. Signing out discards them.', {title:'Discard unsaved entries?', ok:'Discard and sign out', cancel:'Keep editing', danger:true}))) return;
    PG.key = '';
  }
  closeSettings(); closeUserMenu();
  if(ME && ME.id!=='viewer'){ logAct('Signed out', ''); persist(); }
  ME = null; clearSession();
  applyAccess(); renderAll();""", """async function signOut(toSignIn, opts){
  if(opts && opts.force) PG.key = '';
  else if(!(await leaveGuard('signout'))) return;
  closeSettings(); closeUserMenu(); closePopMenu();
  if(ME && ME.id!=='viewer'){ logAct('Signed out', ''); persist(); }
  ME = null; clearSession(); setLockFlag('');
  applyAccess(); renderAll(); reloadLogs();""")
rep("""async function signInAs(u, remember, fresh){
  ME = u;""", """async function signInAs(u, remember, fresh){
  ME = u; setLockFlag(''); lastActivity = Date.now();""")
rep("""  if(!CFG.team) showWelcome();
  else if(!ME) showSignIn();
}""", """  if(!CFG.team) showWelcome();
  else if(!ME) showSignIn();
  else if(ME.id!=='viewer' && lockFlag()===ME.id) lockScreen();
}""")
rep("""async function sendEntriesDialog(){""", """async function sendEntriesDialog(){
  if(!(await saveBeforeAction('the entries file'))) return;""")
rep("""      <button class="btn secondary" type="button" id="tmRecovery">Create new recovery code</button>
    </div>""", """      <button class="btn secondary" type="button" id="tmRecovery">Create new recovery code</button>
    </div>

    <div class="settings-section">
      <h4>Shared computers</h4>
      <p class="hint">Lock the portal after a spell without use, so the next person can&rsquo;t make entries under someone else&rsquo;s name. Unlocking needs the same PIN or password, and anything typed but not saved is kept. The setting reaches engineers&rsquo; copies with the next setup file.</p>
      <div class="field" style="max-width:280px;"><label for="tmLock">Lock the screen</label><select id="tmLock">${[0,5,10,15,30,60].map(m=> `<option value="${m}" ${autoLockMins()===m? 'selected' : ''}>${m? 'After '+m+' minutes without use' : 'Never'}</option>`).join('')}</select></div>
    </div>""")
rep("""  b('tmRecovery').onclick = async ()=>{ await createRecoveryCode(false); renderTeamPane(); };""",
    """  b('tmRecovery').onclick = async ()=>{ await createRecoveryCode(false); renderTeamPane(); };
  b('tmLock').onchange = e=>{
    const m = +e.target.value; CFG.team.autoLock = m; touchBase();
    logAct('Team', m? `Screen lock after ${m} minutes without use` : 'Screen lock turned off'); persist(); lastActivity = Date.now();
    flash(m? `The portal now locks after ${m} minutes without use` : 'Screen lock is off');
  };""")

# ---------------------------------------------------------------- JS: paste grids, render, module
rep("""  if(target.classList.contains('machineryCount'))
    return [...document.querySelectorAll('#machineryBody tr')].map(tr=> [tr.querySelector('.machineryCount')]);
  return null;""", """  if(target.classList.contains('machineryCount'))
    return [...document.querySelectorAll('#machineryBody tr')].map(tr=> [tr.querySelector('.machineryCount')]);
  if(target.classList.contains('materialInput')) return [...document.querySelectorAll('#materialRows .materialInput')].map(i=> [i]);
  if(target.classList.contains('staffInput')) return [...document.querySelectorAll('#staffRows .staffInput')].map(i=> [i]);
  if(target.classList.contains('lcCount')) return [...document.querySelectorAll('#labourCampBody .lcCount')].map(i=> [i]);
  return null;""")
rep("""function renderAll(){
  renderPeriodBadge();
  renderEntry();""", """function renderAll(){
  renderPeriodBadge();
  FORM.date = dateInput.value;
  renderEntry();""")
rep("""  if(document.getElementById('panel-dpr').classList.contains('active')) renderDprSheet();
}
bootAccess();""", """  if(document.getElementById('panel-dpr').classList.contains('active')) renderDprSheet();
  syncDateControls();
  updateDirtyUI();
}
bootAccess();""")
mod = open(SP+'/v22/entry.js', encoding='utf-8').read()
rep("/* =================== INIT =================== */", mod + "\n/* =================== INIT =================== */")

open(DST, 'w', encoding='utf-8').write(s)
js = s[s.index('<script>\n', s.index('</head>'))+8 : s.rindex('</script>')]
open(SP+'/v22/js_v22.js', 'w', encoding='utf-8').write(js)
left = re.findall(r'(?<![A-Za-z_.])(alert|confirm|prompt)\(', js)
print('native dialogs left:', left, '| pgGuard calls:', js.count('pgGuard('), '| size', len(s))
