import re, sys
SP = '/tmp/claude-0/-home-claude/56db3af5-e95d-5731-bda3-4d43f7b29fb9/scratchpad'
SRC = '/mnt/user-data/outputs/dpr_portal_v2.0.html'
DST = '/mnt/user-data/outputs/dpr_portal_v2.1.html'
s = open(SRC, encoding='utf-8').read()

def rep(old, new, cnt=1):
    global s
    n = s.count(old)
    assert n == cnt, (n, old[:140])
    s = s.replace(old, new)

def between(start, end):
    """Replace-helper: returns the exact text from start (inclusive) to end (exclusive)."""
    a = s.index(start); b = s.index(end, a)
    return s[a:b]

# ---------------------------------------------------------------- CSS
rep("  --veil:rgba(214,222,234,.66);", "  --veil:rgba(214,222,234,.66);\n  --slate-a:#A3AEC2; --slate-b:#6E7B93;")
css = open(SP+'/v21/access.css', encoding='utf-8').read()
css = css.replace("position:sticky; bottom:-32px;", "position:sticky; bottom:0;")
css = css.replace("  .set-savebar{margin:22px -18px -24px; padding:12px 18px 14px;}\n", "")
rep("@media (prefers-reduced-motion: reduce){", css.strip()+"\n\n@media (prefers-reduced-motion: reduce){")

# ---------------------------------------------------------------- HTML
rep('<body>\n<div class="wrap">', '<body>\n<div id="authOverlay" class="auth-overlay" hidden></div>\n<div class="wrap">')
rep('<button id="versionBtn" class="ver-pill" type="button" title="What&rsquo;s new">v2.0</button>',
    '<button id="userChip" class="user-chip" type="button" hidden aria-haspopup="menu"></button>\n        <button id="versionBtn" class="ver-pill" type="button" title="What&rsquo;s new">v2.1</button>')
rep('<button class="btn secondary" id="editPlanBtn">', '<button class="btn secondary needs-base" id="editPlanBtn">')
rep('<button class="btn secondary" id="clearTodayBtn">', '<button class="btn secondary needs-entry" id="clearTodayBtn">')
rep('<button class="btn blue" id="saveBtn">', '<button class="btn blue needs-entry" id="saveBtn">')
rep('    <div id="pourGridWrap" style="display:none;">', '    <div class="saved-by empty" id="entrySavedBy"></div>\n    <div id="pourGridWrap" style="display:none;">')

# labour panel: fieldset, read-only banner, saved-by, dynamic header
rep('  <div class="panel" id="panel-labour">\n    <div class="labour-toolbar">',
    '  <div class="panel" id="panel-labour">\n    <div class="ro-banner"></div>\n    <fieldset class="pfs" id="fsLabour">\n    <div class="labour-toolbar">')
rep('<button class="btn secondary" id="managePresetsBtn">', '<button class="btn secondary needs-base" id="managePresetsBtn">')
rep('    <div class="card" id="presetManager" style="display:none; margin-bottom:14px;">',
    '    <div class="saved-by empty" id="labourSavedBy"></div>\n    <div class="card needs-base" id="presetManager" style="display:none; margin-bottom:14px;">')
old_head = between('      <table id="labourTable" style="min-width:1600px;">', '        <tbody id="labourBody"></tbody>')
rep(old_head, '      <table id="labourTable" style="min-width:1600px;">\n        <thead>\n          <tr id="labourHeadRow"></tr>\n          <tr id="labourTradeHeader"></tr>\n        </thead>\n')
rep('<tfoot><tr><td colspan="22">Total labour on site today</td>', '<tfoot><tr><td colspan="22" id="labourFootLabel">Total labour on site today</td>')
rep('      </div>\n    </div>\n  </div>\n\n  <!-- ===================== MACHINERY',
    '      </div>\n    </div>\n    </fieldset>\n  </div>\n\n  <!-- ===================== MACHINERY')
# machinery
rep('  <div class="panel" id="panel-machinery">\n    <div class="labour-toolbar">',
    '  <div class="panel" id="panel-machinery">\n    <div class="ro-banner"></div>\n    <fieldset class="pfs" id="fsMachinery">\n    <div class="labour-toolbar">')
rep('Save machinery report</button>\n    </div>\n    <div class="table-scroll">',
    'Save machinery report</button>\n    </div>\n    <div class="saved-by empty" id="machSavedBy"></div>\n    <div class="table-scroll">')
rep('<td class="num" id="machineryTotal">0</td></tr></tfoot>\n      </table>\n    </div>\n  </div>',
    '<td class="num" id="machineryTotal">0</td></tr></tfoot>\n      </table>\n    </div>\n    </fieldset>\n  </div>')
# material
rep('  <div class="panel" id="panel-material">\n    <div class="two-col">',
    '  <div class="panel" id="panel-material">\n    <div class="ro-banner"></div>\n    <fieldset class="pfs" id="fsMaterial">\n    <div class="two-col">')
rep('      <button class="btn blue" id="saveMaterialBtn">Save material &amp; staff report</button>\n    </div>\n  </div>',
    '      <button class="btn blue" id="saveMaterialBtn">Save material &amp; staff report</button>\n      <div class="saved-by empty" id="matSavedBy" style="margin-top:10px;"></div>\n    </div>\n    </fieldset>\n  </div>')
# site logs
rep('  <div class="panel" id="panel-sitelogs">\n',
    '  <div class="panel" id="panel-sitelogs">\n    <div class="ro-banner"></div>\n    <fieldset class="pfs" id="fsLogs">\n')
rep('        <tbody id="bbsBody"></tbody></table>\n      </div>\n    </div>\n  </div>',
    '        <tbody id="bbsBody"></tbody></table>\n      </div>\n    </div>\n    </fieldset>\n  </div>')
# footer
foot = between('  <footer class="foot">', '  </footer>')
rep(foot, '''  <footer class="foot">
    <span class="ver">DPR Portal v2.1</span> &middot; Entries are saved in this browser; engineers&rsquo; copies stay in step through setup and entries files (Settings &rarr; Team &amp; access) &middot; Baseline from the project workbook (DPR_Format.xlsx for Linkbay); site-log history stays in that workbook
''')

# ---------------------------------------------------------------- JS: version + dialogs
rep("const APP_VERSION = '2.0';", "const APP_VERSION = '2.1';")
rep("const CHANGELOG = [\n", """const CHANGELOG = [
  {v:'v2.1', date:'19 Oct 2026', items:[
    'Team & access: planning managers, site engineers and a view-only mode. Each person signs in with their own PIN or password; a recovery code resets a forgotten planning-manager password.',
    'Only planning managers change base data: BOQ, towers, lists, floors & pours, the monthly plan, the project workbook and periods. Engineers make the daily entries, optionally limited to their own towers and to progress only.',
    'Every saved entry records who made it and when. Settings shows the activity on each device, pour rows and site-log rows show initials, and the printable DPR lists who recorded the day.',
    'Engineers can work on their own copy: the planning manager sends a setup file, engineers send their entries back as a file, and the import keeps the newest version of each record without double counting.',
    'Settings are split into tabs: Team & access, Project, BOQ & lists, Floors & pours, Workbook & periods, Data.',
    'Fixes: saving Settings no longer drops floors & pours, workbook history or the workbook link; \u201ctoday\u201d follows your local date instead of UTC; the labour table header follows the project\u2019s own trades; backups, CSVs and templates also download in the claude.ai viewer; a warning appears if the browser refuses to save.']},
""")
rep("const box = document.createElement('div'); box.className = 'dlg'+(o.wide? ' wide' : '');",
    "const box = document.createElement('div'); box.className = 'dlg'+(o.wide? ' wide' : '');\n    if(o.cls) box.classList.add(o.cls);")
rep("const f=[...box.querySelectorAll('input,button')]; if(!f.length) return;",
    "const f=[...box.querySelectorAll('input:not([type=hidden]):not([hidden]),select,textarea,button')].filter(x=> !x.disabled && x.offsetParent!==null); if(!f.length) return;")
rep("    (inputs[0] || (primaryDanger && safe) || primary || box).focus();",
    "    (o.focusEl || inputs[0] || (primaryDanger && safe) || primary || box).focus();")

# ---------------------------------------------------------------- JS: storage + dates
rep("function persist(){ try{ localStorage.setItem(STORAGE_KEY, JSON.stringify(store)); }catch(e){} }",
"""let persistWarned = false;
function persist(){
  try{ localStorage.setItem(STORAGE_KEY, JSON.stringify(store)); return true; }
  catch(e){
    console.error('Saving to browser storage failed:', e);
    if(!persistWarned){ persistWarned = true; uiAlert('This browser refused to save the portal\\u2019s data (its storage may be full or blocked, for example in a private window). Changes made now may be lost when the page closes. Export a full data backup from Settings \\u2192 Data, or send your entries, before closing.', 'Couldn\\u2019t save on this device'); }
    return false;
  }
}""")
rep("function todayStr(){ return new Date().toISOString().slice(0,10); }",
    "function todayStr(){ const d = new Date(); return d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+String(d.getDate()).padStart(2,'0'); }")
rep("  if(Object.keys(vals).length) L[locId] = vals; else delete L[locId];",
    "  L[locId] = vals;   // kept even when emptied, so clearing a record travels in entries files")

# ---------------------------------------------------------------- JS: labour header follows the project's trades
rep("""function renderLabourTradeHeader(){
  labourTradeHeader.innerHTML = '';
  CFG.labour_day_trades.forEach(tr=>{ const th=document.createElement('th'); th.textContent=tr; labourTradeHeader.appendChild(th); });
  CFG.labour_night_trades.forEach(tr=>{ const th=document.createElement('th'); th.textContent=tr; labourTradeHeader.appendChild(th); });
}""", """function renderLabourTradeHeader(){
  const d = CFG.labour_day_trades||[], n = CFG.labour_night_trades||[], x = CFG.labour_extra_roles||[];
  document.getElementById('labourHeadRow').innerHTML = `<th rowspan="2" style="width:26px;"></th><th rowspan="2">Contractor</th><th rowspan="2">${escH(T('zone'))}</th><th rowspan="2">Category</th>`
    + (d.length? `<th class="grp" colspan="${d.length}">Day shift</th>` : '') + (n.length? `<th class="grp" colspan="${n.length}">Night shift</th>` : '')
    + x.map(r=> `<th rowspan="2">${escH(r)}</th>`).join('') + '<th rowspan="2" class="num">Total</th>';
  labourTradeHeader.innerHTML = [...d, ...n].map(t=> `<th>${escH(t)}</th>`).join('');
  const foot = document.getElementById('labourFootLabel'); if(foot) foot.colSpan = 4 + d.length + n.length + x.length;
  const tbl = document.getElementById('labourTable'); if(tbl) tbl.style.minWidth = Math.max(900, 420 + 66*(d.length+n.length+x.length))+'px';
}""")

# ---------------------------------------------------------------- JS: progress entry (access, stamps)
rep("""  const locked = isLockedDate(date);
  const warnBanner = document.getElementById('pastDateWarning');""", """  const noAccess = !can('progress', tower);
  const locked = isLockedDate(date) || noAccess;
  const warnBanner = document.getElementById('pastDateWarning');""")
rep("""  lockedNote.innerHTML = !locked? '' : isHistoryDate(date)
    ? 'This date is already recorded in the project workbook and is shown read-only below \\u2014 it\\'s part of the cumulative baseline, so there\\'s nothing to enter here.'
    : '&#128274; <b>'+fmtMonth(date.slice(0,7))+' is closed.</b> Entries are shown read-only. Reopen the period from Settings \\u2192 Periods if a correction is needed.';""",
"""  lockedNote.innerHTML = !locked? '' : isHistoryDate(date)
    ? 'This date is already recorded in the project workbook and is shown read-only below \\u2014 it\\'s part of the cumulative baseline, so there\\'s nothing to enter here.'
    : isClosedDate(date)? '&#128274; <b>'+fmtMonth(date.slice(0,7))+' is closed.</b> Entries are shown read-only. A planning manager can reopen the period if a correction is needed.'
    : '&#128274; <b>View only.</b> '+escH(denyText('progress', tower));
  lockedNote.style.background = isHistoryDate(date)? 'var(--green-soft)' : isClosedDate(date)? 'var(--amber-soft)' : 'var(--blue-wash)';
  setSavedBy('entrySavedBy', latestStamp('p|'+tower+'|'+date+'|'));""")
rep("""document.getElementById('editPlanBtn').addEventListener('click', ()=> openLockedPanel(renderPlanEditor));""",
    """document.getElementById('editPlanBtn').addEventListener('click', ()=>{ if(!need('plan')) return; openSettingsOverlay(); renderPlanEditor(); });""")
rep("""  if(isLockedDate(date)){ flash(isHistoryDate(date)? 'This date is already recorded in the workbook \\u2014 nothing to save here.' : fmtMonth(date.slice(0,7))+' is closed.'); return; }
  if(entryMode()==='pours'){ savePourGrid(tower, date); return; }""",
"""  if(isLockedDate(date)){ flash(isHistoryDate(date)? 'This date is already recorded in the workbook \\u2014 nothing to save here.' : fmtMonth(date.slice(0,7))+' is closed.'); return; }
  if(!need('progress', tower)) return;
  if(entryMode()==='pours'){ savePourGrid(tower, date); return; }""")
rep("""  saveLocValues(tower, date, '', vals); persist();
  flash('Saved progress \\u2014 '+tower+' (whole tower) \\u2014 '+date);""",
"""  saveLocValues(tower, date, '', vals); stamp('p|'+tower+'|'+date+'|');
  logAct('Progress', tower+' \\u00b7 '+date+' \\u00b7 whole '+T('zone').toLowerCase()); persist();
  flash('Saved progress \\u2014 '+tower+' (whole '+T('zone').toLowerCase()+') \\u2014 '+date);""")
# pour grid
rep("""      <td><span class="pour-chip ${st.status}">${STATUS_LABEL[st.status]}</span></td>""",
    """      <td><span class="pour-chip ${st.status}">${STATUS_LABEL[st.status]}</span>${byChip(stampOf('p|'+tower+'|'+date+'|'+lid))}</td>""")
rep("""    saveLocValues(tower,date,lid,vals); n++;""", """    saveLocValues(tower,date,lid,vals); stamp('p|'+tower+'|'+date+'|'+lid); n++;""")
rep("""  let c=0; PG.cast.forEach(id=>{ store.pourCast[id]={date, source:'entry table', at:new Date().toISOString()}; c++; });
  persist();""", """  let c=0; PG.cast.forEach(id=>{ store.pourCast[id]={date, source:'entry table', at:nowIso(), by: ME? ME.id : ''}; delete store.tomb['cast|'+id]; c++; });
  if(n||c) logAct('Progress', `${tower} \\u00b7 ${date} \\u00b7 ${n} pour(s)${c? ', '+c+' marked cast' : ''}`);
  persist();""")
rep("""    if(blockIfClosed(c.date,'pour status')) return;
    if(!(await uiConfirm(""", """    if(blockIfClosed(c.date,'pour status')) return;
    if(!need('cast', towerSelect.value)) return;
    if(!(await uiConfirm(""")
rep("""    delete store.pourCast[a.dataset.id]; persist(); renderEntry();""",
    """    delete store.pourCast[a.dataset.id]; store.tomb['cast|'+a.dataset.id] = {at: nowIso(), by: ME? ME.id : ''};
    logAct('Pour cast cleared', a.dataset.id.split('|').join(' \\u203a ')); persist(); renderEntry();""")
rep("""    if(p && !store.pourCast[pourId(p)] && r.date){ store.pourCast[pourId(p)]={date:r.date, source:'concrete log', at:new Date().toISOString()}; n++; }""",
    """    if(p && !store.pourCast[pourId(p)] && r.date){ store.pourCast[pourId(p)]={date:r.date, source:'concrete log', at:nowIso(), by: ME? ME.id : ''}; delete store.tomb['cast|'+pourId(p)]; n++; }""")

# ---------------------------------------------------------------- JS: labour / machinery / material saves
rep("""  const date = dateInput.value;
  if(blockIfClosed(date,'labour')) return;""", """  const date = dateInput.value;
  if(!need('site')) return;
  if(blockIfClosed(date,'labour')) return;""")
rep("""  store.labourCamp[date] = campRows;

  persist();
  flash('Saved labour report \\u2014 '+date);""", """  store.labourCamp[date] = campRows;
  stamp('labour|'+date); logAct('Labour report', date+' \\u00b7 '+rows.length+' crew row(s)');
  persist(); setSavedBy('labourSavedBy', stampOf('labour|'+date));
  flash('Saved labour report \\u2014 '+date);""")
rep("""  const date = dateInput.value;
  if(blockIfClosed(date,'machinery counts')) return;""", """  const date = dateInput.value;
  if(!need('site')) return;
  if(blockIfClosed(date,'machinery counts')) return;""")
rep("""  store.machinery[date] = rec; persist();""", """  store.machinery[date] = rec; stamp('mach|'+date); logAct('Machinery report', date);
  persist(); setSavedBy('machSavedBy', stampOf('mach|'+date));""")
rep("""  const date = dateInput.value;
  if(blockIfClosed(date,'material & staff')) return;""", """  const date = dateInput.value;
  if(!need('site')) return;
  if(blockIfClosed(date,'material & staff')) return;""")
rep("""  store.material[date] = rec; persist();""", """  store.material[date] = rec; stamp('mat|'+date); logAct('Material & staff', date);
  persist(); setSavedBy('matSavedBy', stampOf('mat|'+date));""")
rep("""document.getElementById('savePresetsBtn').addEventListener('click', ()=>{
  const rows = [];""", """document.getElementById('savePresetsBtn').addEventListener('click', ()=>{
  if(!need('base')) return;
  const rows = [];""")
rep("""  store.labourPresets = rows; persist();""", """  store.labourPresets = rows; touchBase(); logAct('Contractor presets', rows.length+' preset(s)'); persist();""")

# ---------------------------------------------------------------- JS: site logs (ids, who/when, removals)
rep("""function closedLogEdit(prev, rows, dateKey, label){
  const inClosed = r=> isClosedDate(r[dateKey]);
  const a=(prev||[]).filter(inClosed).map(r=>JSON.stringify(r)).sort(), b=rows.filter(inClosed).map(r=>JSON.stringify(r)).sort();""",
"""function closedLogEdit(prev, rows, dateKey, label){
  const inClosed = r=> isClosedDate(r[dateKey]);
  const a=(prev||[]).filter(inClosed).map(canonRow).sort(), b=rows.filter(inClosed).map(canonRow).sort();""")
for body in ['concreteBody','rainBody','hindranceBody','bbsBody']:
    rep(f"  {body}.appendChild(tr);\n", f"  {body}.appendChild(tr); decorateLogRow(tr, prefill);\n")
LOGS = [
  ('concrete', "rows.push({ date: tr.querySelector('.cDate').value,", "rows.push({ id: tr.dataset.id||'', date: tr.querySelector('.cDate').value,",
   "  const kept = rows.filter(r=> (+r.qty>0) || (r.structure||'').trim()); // an untouched starter row is not a real entry\n  if(closedLogEdit(store.concrete, kept, 'date', 'concrete')) return;\n  store.concrete = kept;",
   "Concrete log", "loadConcrete();"),
  ('rain', "rows.push({ date: tr.querySelector('.rDate').value,", "rows.push({ id: tr.dataset.id||'', date: tr.querySelector('.rDate').value,",
   "  const kept = rows.filter(r=> r.start || r.end || (r.affected||'').trim()); // an untouched starter row is not a real entry\n  if(closedLogEdit(store.rain, kept, 'date', 'rain register')) return;\n  store.rain = kept;",
   "Rain register", "loadRain();"),
  ('hindrance', "rows.push({ desc: tr.querySelector('.hDesc').value,", "rows.push({ id: tr.dataset.id||'', desc: tr.querySelector('.hDesc').value,",
   "  const kept = rows.filter(r=> (r.desc||'').trim()); // an untouched starter row is not a real entry\n  if(closedLogEdit(store.hindrance, kept, 'start', 'hindrance')) return;\n  store.hindrance = kept;",
   "Hindrance log", "loadHindrance();"),
  ('bbs', "rows.push({ date: tr.querySelector('.bDate').value,", "rows.push({ id: tr.dataset.id||'', date: tr.querySelector('.bDate').value,",
   "  const kept = rows.filter(r=> (+r.qty>0) || (r.staff||'').trim() || (r.remarks||'').trim()); // an untouched starter row is not a real entry\n  if(closedLogEdit(store.bbs, kept, 'date', 'BBS')) return;\n  store.bbs = kept;",
   "BBS log", "loadBbs();"),
]
for t, a, b, keep_old, label, reload in LOGS:
    rep(a, b)
    filt = keep_old.split('\n')[0].replace("  const kept = rows.filter(", "rows.filter(").split('); //')[0]+')'
    dk = 'start' if t=='hindrance' else 'date'
    lab = {'concrete':'concrete','rain':'rain register','hindrance':'hindrance','bbs':'BBS'}[t]
    rep(keep_old, f"""  const sl = stampLogRows(store.{t}, {filt}); // an untouched starter row is not a real entry
  const kept = sl.rows;
  if(closedLogEdit(store.{t}, kept, '{dk}', '{lab}')) return;
  sl.commit(); store.{t} = kept;
  logAct('{label}', kept.length+' row(s)');""")
# need('site') at the start of each log save, and redraw after saving so ids and initials show
for btn in ['saveConcreteBtn','saveRainBtn','saveHindranceBtn','saveBbsBtn']:
    rep(f"document.getElementById('{btn}').addEventListener('click', ()=>{{\n  const rows = [];",
        f"document.getElementById('{btn}').addEventListener('click', ()=>{{\n  if(!need('site')) return;\n  const rows = [];")
rep("  flash('Saved concrete log \\u2014 '+rows.length+' pour(s)');", "  loadConcrete(); flash('Saved concrete log \\u2014 '+kept.length+' pour(s)');")
rep("  logAct('Rain register', kept.length+' row(s)'); persist();\n  flash('Saved rain register \\u2014 '+rows.length+' event(s)');", "  logAct('Rain register', kept.length+' row(s)'); persist(); loadRain();\n  flash('Saved rain register \\u2014 '+kept.length+' event(s)');")
rep("  logAct('Hindrance log', kept.length+' row(s)'); persist();\n  flash('Saved hindrance log \\u2014 '+rows.length+' item(s)');", "  logAct('Hindrance log', kept.length+' row(s)'); persist(); loadHindrance();\n  flash('Saved hindrance log \\u2014 '+kept.length+' item(s)');")
rep("  logAct('BBS log', kept.length+' row(s)'); persist();\n  flash('Saved BBS checking log \\u2014 '+rows.length+' item(s)');", "  logAct('BBS log', kept.length+' row(s)'); persist(); loadBbs();\n  flash('Saved BBS checking log \\u2014 '+kept.length+' item(s)');")

# ---------------------------------------------------------------- JS: printable DPR lists who recorded the day
rep("""    <div class="dpr-sub">${CFG.project.contractor||''} &middot; ${CFG.project.name||''}${CFG.project.employer? ' &middot; Employer: '+CFG.project.employer : ''} &middot; Report date: ${date}</div>""",
    """    <div class="dpr-sub">${CFG.project.contractor||''} &middot; ${CFG.project.name||''}${CFG.project.employer? ' &middot; Employer: '+CFG.project.employer : ''} &middot; Report date: ${date}${(()=>{ const n = recordedByNames(date); return n.length? ' &middot; Recorded by '+escH(n.join(', ')) : ''; })()}</div>""")

# ---------------------------------------------------------------- JS: downloads through one helper
rep("""  const url = URL.createObjectURL(new Blob([lines.join('\\n')], {type:'text/csv'}));
  const a = document.createElement('a'); a.href=url; a.download=slugify(CFG.project.name||'project')+'_pour_status_'+todayStr()+'.csv'; document.body.appendChild(a); a.click(); a.remove(); URL.revokeObjectURL(url);""",
    """  saveFile(slugify(CFG.project.name||'project')+'_pour_status_'+todayStr()+'.csv', lines.join('\\n'), 'text/csv');""")
rep("""    const url = URL.createObjectURL(new Blob([[head,...body].map(r=>r.map(x=>q(String(x))).join(',')).join('\\n')], {type:'text/csv'}));
    const a=document.createElement('a'); a.href=url; a.download='floors_and_pours_template.csv'; document.body.appendChild(a); a.click(); a.remove(); URL.revokeObjectURL(url);""",
    """    saveFile('floors_and_pours_template.csv', [head,...body].map(r=>r.map(x=>q(String(x))).join(',')).join('\\n'), 'text/csv');""")
rep("""    try{ await ensureTemplate(); const b=await loadTemplateBytes(); const url=URL.createObjectURL(new Blob([b]));
      const a=document.createElement('a'); a.href=url; a.download=(CFG.template&&CFG.template.fileName||'workbook.xlsx').replace(/\\.xlsx$/i,'')+'_'+CFG.template.period+'_template.xlsx'; document.body.appendChild(a); a.click(); a.remove(); URL.revokeObjectURL(url);""",
    """    try{ await ensureTemplate(); const b=await loadTemplateBytes();
      await saveFile((CFG.template&&CFG.template.fileName||'workbook.xlsx').replace(/\\.xlsx$/i,'')+'_'+CFG.template.period+'_template.xlsx', new Blob([b]));""")
old_dl = between("      let downloads = null;\n", "      if(issues.length) uiAlert('Check these before sending it:")
rep(old_dl, """      const saved = await saveFile(fname, blob);
      if(saved!=='saved') return;
      flash('Exported '+fname);
""")
rep("""      if(T){
        const bytes=await loadTemplateBytes();
        const res=await DPRX.exportInto(bytes, T, portalData(date));
        blob = new Blob([res.bytes], {type:'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'});
        usedTemplate = true; issues = exportIssues(res.report, T.period);
      }""", """      if(T){
        let bytes = null;
        try{ bytes = await loadTemplateBytes(); }catch(e){ console.error(e); }
        if(bytes){
          const res=await DPRX.exportInto(bytes, T, portalData(date));
          blob = new Blob([res.bytes], {type:'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'});
          usedTemplate = true; issues = exportIssues(res.report, T.period);
        } else issues.push('The project workbook isn\\u2019t on this device, so this is the summary workbook instead. Ask the planning manager for a setup file that includes the workbook.');
      }""")

# ---------------------------------------------------------------- JS: periods, plan, wizard, pours record who and mark base data changed
rep("function logPeriod(action, period, note){ store.periodLog.push({ts:new Date().toISOString(), action, period, note:note||''}); }",
    "function logPeriod(action, period, note){ store.periodLog.push({ts:new Date().toISOString(), action, period, note:note||'', by: ME? ME.id : ''}); touchBase(); logAct('Period: '+action, fmtMonth(period)+(note? ' \\u00b7 '+note : '')); }")
rep("""<table><thead><tr><th>When</th><th>Action</th><th>Period</th><th>Note</th></tr></thead><tbody>""",
    """<table><thead><tr><th>When</th><th>By</th><th>Action</th><th>Period</th><th>Note</th></tr></thead><tbody>""")
rep("""map(r=>`<tr><td>${new Date(r.ts).toLocaleString()}</td><td>${r.action}</td><td>${fmtMonth(r.period)}</td>""",
    """map(r=>`<tr><td>${new Date(r.ts).toLocaleString()}</td><td>${r.by? escH(userName(r.by)) : '\\u2014'}</td><td>${r.action}</td><td>${fmtMonth(r.period)}</td>""")
rep("""|| '<tr><td colspan="4">Nothing logged yet.</td></tr>'}""", """|| '<tr><td colspan="5">Nothing logged yet.</td></tr>'}""")
rep("""          store.planAuditLog.push({ts, tower, date:dateStr, sno, item: it? it.short: sno, oldValue: oldVal, newValue: newVal});""",
    """          store.planAuditLog.push({ts, tower, date:dateStr, sno, item: it? it.short: sno, oldValue: oldVal, newValue: newVal, by: ME? ME.id : ''});""")
rep("""    if(changeCount){ persist(); renderAll(); }""",
    """    if(changeCount){ touchBase(); logAct('Monthly plan', `${tower} \\u00b7 ${fmtMonth(ym)} \\u00b7 ${changeCount} value(s)`); persist(); renderAll(); }""")
rep("""<table><thead><tr><th>When</th><th>Tower</th><th>Date</th><th>Item</th><th class="num">Old</th><th class="num">New</th></tr></thead>""",
    """<table><thead><tr><th>When</th><th>By</th><th>Tower</th><th>Date</th><th>Item</th><th class="num">Old</th><th class="num">New</th></tr></thead>""")
rep("""rows.map(r=>`<tr><td>${new Date(r.ts).toLocaleString()}</td><td>${r.tower}</td>""",
    """rows.map(r=>`<tr><td>${new Date(r.ts).toLocaleString()}</td><td>${r.by? escH(userName(r.by)) : '\\u2014'}</td><td>${r.tower}</td>""")
rep("""    : '<tr><td colspan="6">No plan changes yet.</td></tr>';""", """    : '<tr><td colspan="7">No plan changes yet.</td></tr>';""")
rep("""      CFG.template=T; logPeriod('import', T.period, 'workbook replaced: '+W.fileName);""",
    """      CFG.template=T; logPeriod('import', T.period, 'workbook replaced: '+W.fileName); touchBase();""")
rep("""      template:T, bakedThrough:''
    });""", """      template:T, bakedThrough:'',
      team: CFG.team, projectId: genId('prj-'), updatedAt: nowIso()
    });""")
rep("""      periods:{}, periodLog:[{ts:new Date().toISOString(), action:'import', period:T.period, note:'new project from '+W.fileName}], progressLoc:{}, pourCast:{} };
    persist(); location.reload();""", """      periods:{}, periodLog:[{ts:new Date().toISOString(), action:'import', period:T.period, note:'new project from '+W.fileName, by: ME? ME.id : ''}], progressLoc:{}, pourCast:{} };
    carrySession(cfg.projectId);
    persist(); location.reload();""")
rep("""    CFG.pours = next; store.config = CFG;""", """    CFG.pours = next; store.config = CFG; touchBase();""")

# ---------------------------------------------------------------- JS: settings shell (no shared password any more)
old_lock = between("/* =================== SETTINGS (password-gated project configuration) =================== */", "/* ---- generic editable string-list")
rep(old_lock, """/* =================== SETTINGS (planning managers) =================== */
if(!store.settingsAuth) store.settingsAuth = { hash: null };   // pre-v2.1 password; migrated into the team on first load

async function sha256Hex(str){
  const enc = new TextEncoder().encode(str);
  const buf = await crypto.subtle.digest('SHA-256', enc);
  return Array.from(new Uint8Array(buf)).map(b=>b.toString(16).padStart(2,'0')).join('');
}

const settingsOverlay = document.getElementById('settingsOverlay');
const settingsPanel = document.getElementById('settingsPanel');
document.getElementById('settingsGearBtn').addEventListener('click', openSettings);
settingsOverlay.addEventListener('click', (e)=>{ if(e.target===settingsOverlay) closeSettings(); });
document.addEventListener('keydown', e=>{ if(e.key==='Escape' && settingsOverlay.style.display==='flex' && !document.querySelector('.dlg-overlay')) closeSettings(); });
let settingsPane = 'team';
/* Planning managers get project settings; everyone else gets their own account. */
function openSettings(){
  if(!ME){ if(CFG.team) showSignIn(); else showWelcome(); return; }
  openSettingsOverlay();
  if(can('base')) renderSettingsEditor(); else renderMyAccount();
}
function closeSettings(){ settingsOverlay.style.display = 'none'; }

""")

# ---------------------------------------------------------------- JS: settings editor in tabs
old_set = between("function renderSettingsEditor(){", "  document.getElementById('closeSettingsX').addEventListener('click', closeSettings);\n  wireProjectSections();")
proj = between('    <div class="settings-section">\n      <h4>Project</h4>', '    <div class="settings-section">\n      <h4>BOQ items (Physical Progress)</h4>')
lists = between('    <div class="settings-section">\n      <h4>BOQ items (Physical Progress)</h4>', '    <div class="settings-section" style="display:flex; gap:10px; align-items:center;">')
pours = between('    <div class="settings-section">\n      <h4>Floors &amp; pours</h4>', '    <div class="settings-section">\n      <h4>Project</h4>')
wb = between('    <div class="settings-section">\n      <h4>Project workbook</h4>', '    <div class="settings-section">\n      <h4>Floors &amp; pours</h4>')
data = between('    <div class="danger-zone">\n      <h4>Move data between copies of this portal</h4>', '  `;\n  document.getElementById(\'closeSettingsX\')')
first = lambda t: t.replace('<div class="settings-section">', '<div class="settings-section first">', 1)
data2 = data.replace('      <button class="btn secondary" id="cfgChangePwBtn">Change settings password</button>\n', '')
data2 = data2.replace('The hosted link and any downloaded copy of this file each save to their own browser only &mdash; nothing syncs automatically. Export a backup here, then import it on the other copy to bring entries across.',
                      'A full backup holds everything on this device: setup, team, entries and history. To bring engineers&rsquo; entries in, use Team &amp; access instead.')
assert data2 != data
new_set = """function renderSettingsEditor(){
  const nextSno = () => Math.max(0, ...CFG.items.map(it=>it.sno)) + 1;
  const panes = [['team','Team & access'],['project','Project'],['lists','BOQ & lists'],['pours','Floors & pours'],['workbook','Workbook & periods'],['data','Data']];
  if(!panes.some(p=> p[0]===settingsPane)) settingsPane = 'team';
  settingsPanel.innerHTML = `
    <button class="close-x" id="closeSettingsX" aria-label="Close">&times;</button>
    <h2>Project settings</h2>
    <p class="hint" style="margin-top:0;">Base data for ${escH(CFG.project.name||'this project')}. Only planning managers can open this.</p>
    <div class="set-tabs" role="tablist">${panes.map(([k,l])=> `<button type="button" role="tab" data-pane="${k}">${l.replace('&','&amp;')}</button>`).join('')}</div>

    <div class="set-pane" data-pane="team"><div id="teamPane"></div></div>

    <div class="set-pane" data-pane="project">
""" + first(proj) + """    </div>

    <div class="set-pane" data-pane="lists">
""" + first(lists) + """    </div>

    <div class="set-pane" data-pane="pours">
""" + first(pours) + """    </div>

    <div class="set-pane" data-pane="workbook">
""" + first(wb) + """    </div>

    <div class="set-pane" data-pane="data">
""" + data2.replace('<div class="danger-zone">', '<div class="danger-zone" style="margin-top:6px;">', 1) + """    </div>

    <div class="set-savebar" id="setSaveBar">
      <button class="btn blue" id="cfgSaveBtn">Save changes &amp; reload</button>
      <button class="btn secondary" id="cfgCancelBtn">Cancel</button>
      <span class="hint" style="margin:0;">Saves the Project and BOQ &amp; lists tabs; the portal reloads so every tab picks up the change.</span>
    </div>
  `;
"""
rep(old_set, new_set)
rep("""  `;
  document.getElementById('closeSettingsX').addEventListener('click', closeSettings);
  wireProjectSections();""", """  `;
  document.getElementById('closeSettingsX').addEventListener('click', closeSettings);
  const showPane = k=>{
    settingsPane = k;
    settingsPanel.querySelectorAll('.set-tabs button').forEach(b=>{ b.classList.toggle('active', b.dataset.pane===k); b.setAttribute('aria-selected', b.dataset.pane===k); });
    settingsPanel.querySelectorAll('.set-pane').forEach(p=> p.classList.toggle('active', p.dataset.pane===k));
    document.getElementById('setSaveBar').hidden = !(k==='project' || k==='lists');
  };
  settingsPanel.querySelectorAll('.set-tabs button').forEach(b=> b.onclick = ()=> showPane(b.dataset.pane));
  showPane(settingsPane);
  renderTeamPane();
  wireProjectSections();""")
# old shape had the save bar inside the content; drop it (it's now the sticky bar)
old_bar = """    <div class="settings-section" style="display:flex; gap:10px; align-items:center;">
      <button class="btn blue" id="cfgSaveBtn">Save changes &amp; reload</button>
      <button class="btn secondary" id="cfgCancelBtn">Cancel</button>
      <span class="hint" style="margin:0;">Saving reloads the page so every tab picks up the new setup.</span>
    </div>
"""
assert old_bar not in s
# keep every config field the form doesn't edit (pours, workbook link, history, team, terms...)
rep("""    CFG = {
      project: { contractor: document.getElementById('cfgContractor').value""", """    CFG = Object.assign({}, CFG, {
      project: { contractor: document.getElementById('cfgContractor').value""")
rep("""      labour_presets_default: CFG.labour_presets_default
    };
    store.config = CFG;""", """      labour_presets_default: CFG.labour_presets_default
    });
    touchBase(); logAct('Project settings', 'Saved project details and lists');
    store.config = CFG;""")
# data tab: backups through saveFile, team kept on merge, sessions carried to new projects
rep("""    const blob = new Blob([JSON.stringify(out)], {type:'application/json'});
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a'); a.href=url; a.download=slugify(CFG.project.name||'project')+'_data_backup_'+todayStr()+'.json';
    document.body.appendChild(a); a.click(); document.body.removeChild(a); URL.revokeObjectURL(url);""",
    """    if(await saveFile(slugify(CFG.project.name||'project')+'_data_backup_'+todayStr()+'.json', JSON.stringify(out), 'application/json')==='saved'){ logAct('Data backup', 'Exported a full backup'); persist(); }""")
rep("""          store.pourCast = Object.assign({}, store.pourCast, imported.pourCast||{});
          store.config = imported.config;
        } else {
          store = imported;
        }""", """          store.pourCast = Object.assign({}, store.pourCast, imported.pourCast||{});
          store.stamps = Object.assign({}, store.stamps, imported.stamps||{});
          store.tomb = Object.assign({}, store.tomb, imported.tomb||{});
          store.activity = [...(store.activity||[]), ...(imported.activity||[])].sort((a,b)=> (a.at||'').localeCompare(b.at||''));
          store.config = Object.assign({}, imported.config, {team: CFG.team || imported.config.team, projectId: CFG.projectId});
        } else {
          const keepTeam = CFG.team;
          store = imported;
          if(!store.config.team && keepTeam) store.config.team = keepTeam;
          if(store.config.projectId) carrySession(store.config.projectId);
        }""")
rep("""    const blob = new Blob([JSON.stringify(CFG,null,2)], {type:'application/json'});
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a'); a.href=url; a.download=slugify(CFG.project.name||'project')+'_config.json';
    document.body.appendChild(a); a.click(); document.body.removeChild(a); URL.revokeObjectURL(url);""",
    """    const c = Object.assign({}, CFG); delete c.team;   // PIN and password hashes stay out of configuration files
    saveFile(slugify(CFG.project.name||'project')+'_config.json', JSON.stringify(c,null,2), 'application/json');""")
rep("""        store.config = imported; persist();""", """        store.config = Object.assign({}, imported, {team: CFG.team, projectId: CFG.projectId, updatedAt: nowIso()}); logAct('Project settings', 'Imported a configuration file'); persist();""")
rep("""      store = { progress:{}, labour:{}, labourCamp:{}, labourPresets:[], machinery:{}, material:{}, concrete:[], rain:[], hindrance:[], bbs:[], config: blankConfig(), settingsAuth: store.settingsAuth, plan:{}, planAuditLog:[], periods:{}, periodLog:[], progressLoc:{}, pourCast:{} };
      persist(); location.reload();""", """      const team = CFG.team;
      store = { progress:{}, labour:{}, labourCamp:{}, labourPresets:[], machinery:{}, material:{}, concrete:[], rain:[], hindrance:[], bbs:[], config: blankConfig(), settingsAuth: store.settingsAuth, plan:{}, planAuditLog:[], periods:{}, periodLog:[], progressLoc:{}, pourCast:{} };
      Object.assign(store.config, {team, projectId: genId('prj-'), updatedAt: nowIso()}); carrySession(store.config.projectId);
      persist(); location.reload();""")
rep("""      store = { progress:{}, labour:{}, labourCamp:{}, labourPresets:null, machinery:{}, material:{}, concrete:[], rain:[], hindrance:[], bbs:[], config: makeDefaultConfig(), settingsAuth: store.settingsAuth, plan:{}, planAuditLog:[], periods:{}, periodLog:[], progressLoc:{}, pourCast:{} };
      persist(); location.reload();""", """      const team = CFG.team;
      store = { progress:{}, labour:{}, labourCamp:{}, labourPresets:null, machinery:{}, material:{}, concrete:[], rain:[], hindrance:[], bbs:[], config: makeDefaultConfig(), settingsAuth: store.settingsAuth, plan:{}, planAuditLog:[], periods:{}, periodLog:[], progressLoc:{}, pourCast:{} };
      Object.assign(store.config, {team, projectId: genId('prj-'), updatedAt: nowIso()}); carrySession(store.config.projectId);
      persist(); location.reload();""")
old_pw = between("  document.getElementById('cfgChangePwBtn').addEventListener('click', async ()=>{", "}\n\n/* =================== INIT =================== */")
rep(old_pw, "")

# ---------------------------------------------------------------- JS: access + team modules, boot
acc = open(SP+'/v21/access.js', encoding='utf-8').read()
team = open(SP+'/v21/team.js', encoding='utf-8').read()
extra = """
function latestStamp(prefix){ let best = null; Object.keys(store.stamps).forEach(k=>{ if(k.startsWith(prefix)){ const s = store.stamps[k]; if(!best || (s.at||'') > (best.at||'')) best = s; } }); return best; }
function recordedByNames(date){
  const ids = new Set();
  Object.keys(store.stamps).forEach(k=>{ if(k.split('|').includes(date) && store.stamps[k].by) ids.add(store.stamps[k].by); });
  LOG_TYPES.forEach(t=> (store[t]||[]).forEach(r=>{ if(logDate(t, r)===date && r.by) ids.add(r.by); }));
  return [...ids].filter(id=> id!=='viewer').map(userName);
}
"""
rep("/* =================== INIT =================== */", acc + "\n" + team + extra + "\n/* =================== INIT =================== */")
rep("""  loadMaterialForDate(dateInput.value);
  if(document.getElementById('panel-overview')""", """  loadMaterialForDate(dateInput.value);
  setSavedBy('labourSavedBy', stampOf('labour|'+dateInput.value));
  setSavedBy('machSavedBy', stampOf('mach|'+dateInput.value));
  setSavedBy('matSavedBy', stampOf('mat|'+dateInput.value));
  const gear = document.getElementById('settingsGearBtn'); if(gear){ gear.title = can('base')? 'Settings' : 'My account'; gear.setAttribute('aria-label', gear.title); }
  if(document.getElementById('panel-overview')""")
rep("""loadConcrete();
refreshPourDatalist();
loadRain();""", """bootAccess();
loadConcrete();
refreshPourDatalist();
loadRain();""")
rep("""document.getElementById('versionBtn').addEventListener('click', openChangelog);""",
    """document.getElementById('versionBtn').addEventListener('click', openChangelog);
document.getElementById('userChip').addEventListener('click', openUserMenu);""")

open(DST, 'w', encoding='utf-8').write(s)
js = s[s.index('<script>\n', s.index('</head>'))+8 : s.rindex('</script>')]
open(SP+'/v21/js_v21.js', 'w', encoding='utf-8').write(js)
left = re.findall(r'(?<![A-Za-z_.])(alert|confirm|prompt)\(', js)
print('native dialogs left:', left, '| settingsUnlocked refs:', js.count('settingsUnlockedThisSession'), '| openLockedPanel refs:', js.count('openLockedPanel'))
print('size', len(s))
