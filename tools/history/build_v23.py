import re, sys
SP = '/tmp/claude-0/-home-claude/56db3af5-e95d-5731-bda3-4d43f7b29fb9/scratchpad'
SRC = '/mnt/user-data/outputs/dpr_portal_v2.2.html'
DST = '/mnt/user-data/outputs/dpr_portal_v2.3.html'
s = open(SRC, encoding='utf-8').read()
BS = '\\'
EM = BS + 'u2014'     # the text — as it appears inside the portal's script

def rep(old, new, cnt=1):
    global s
    n = s.count(old)
    assert n == cnt, (n, old[:160])
    s = s.replace(old, new)

def rep_between(start, end, new):
    global s
    assert s.count(start) == 1, ('start', s.count(start), start[:120])
    a = s.index(start); b = s.index(end, a)
    s = s[:a] + new + s[b:]

# ---------------------------------------------------------------- CSS
rep(".tower-row .name{width:62px; font-family:var(--mono); color:var(--ink-soft);}",
    ".tower-row .name{min-width:62px; max-width:150px; font-family:var(--mono); color:var(--ink-soft); white-space:nowrap; overflow:hidden; text-overflow:ellipsis;}")
rep(".tower-row .pct-num{width:56px;}", ".tower-row .pct-num{width:auto; min-width:56px; white-space:nowrap;}")

# ---------------------------------------------------------------- HTML: words, money, ids
rep('<label for="towerSelect">Tower</label>', '<label for="towerSelect" data-term="zone">Tower</label>')
rep('<label for="pgLevel">Level</label>', '<label for="pgLevel" data-term="level">Level</label>')
rep('<label for="stTower">Tower / Area</label>', '<label for="stTower" data-term="zone">Tower</label>')
rep('<span>Top floor first &middot; % = share of the pour&rsquo;s budget achieved, by value</span>',
    '<span id="stLegendNote">Top floor first &middot; % = share of the pour&rsquo;s budget achieved, by value</span>')
rep('<div class="hint" style="margin-top:-6px;">A contractor assigned to every tower can use the <b>ALL</b> tower option instead of one row per tower.</div>',
    '<div class="hint" id="presetHint" style="margin-top:-6px;">A contractor assigned to every tower can use the <b>ALL</b> tower option instead of one row per tower.</div>')
rep('<table><thead><tr><th style="width:26px;"></th><th>Contractor</th><th>Tower</th><th>Category</th></tr></thead>',
    '<table><thead><tr><th style="width:26px;"></th><th>Contractor</th><th data-term="zone">Tower</th><th>Category</th></tr></thead>')
rep('<th>Date</th><th>Tower</th><th>Structure</th><th>Grade</th><th class="num">Qty (CUM)</th></tr></thead>',
    '<th>Date</th><th data-term="zone">Tower</th><th>Structure</th><th>Grade</th><th class="num">Qty (CUM)</th></tr></thead>')
rep('<th class="num">Qty certified</th><th>UOM</th><th>Tower</th><th>Staff</th>',
    '<th class="num">Qty certified</th><th>UOM</th><th data-term="zone">Tower</th><th>Staff</th>')
rep('<h3>Progress by tower</h3>', '<h3 id="ovTowerTitle">Progress by tower</h3>')
rep('<th class="num">Rate (Rs.)</th>', '<th class="num" id="thRate">Rate (Rs.)</th>')
rep('<thead><tr><th>Date</th><th class="num">Planned (Cr)</th>', '<thead><tr id="finHead"><th>Date</th><th class="num">Planned (Cr)</th>')
a = s.index('    <div class="hint">Achieved-before-today = '); b = s.index('</div>', a) + len('</div>')
s = s[:a] + '    <div class="hint" id="entryHint"></div>' + s[b:]
rep('<datalist id="pourList"></datalist>', '<datalist id="pourList"></datalist>\n  <datalist id="zoneList"></datalist>')
rep('''<td><input type="text" class="cTower" style="width:70px;" value="${(prefill&&prefill.tower)||''}" placeholder="e.g. D"></td>''',
    '''<td><input type="text" class="cTower" list="zoneList" style="width:110px;" value="${escH((prefill&&prefill.tower)||'')}" placeholder="${escH(CFG.towers[0]||'')}"></td>''')

# ---------------------------------------------------------------- JS: words
rep("function T(k){ const t = (CFG.terms||{}); const d = {zone:'Tower', zones:'Towers', level:'Level', pour:'Pour'}; return t[k] || d[k] || k; }",
    """function T(k){
  const t = CFG.terms || {}, base = {zone:'Tower', level:'Level', pour:'Pour'};
  if(base[k]) return String(t[k]||'').trim() || base[k];
  if(k==='zones' || k==='levels' || k==='pours') return String(t[k]||'').trim() || plural(T(k.slice(0,-1)));
  return k;
}""")
rep("const locNorm = s => String(s||'').toLowerCase().replace(/^tower\\s*/,'').replace(/[^a-z0-9]+/g,'');",
    "const locNorm = s => String(s||'').toLowerCase().replace(new RegExp('^(tower|'+escRe(T('zone').toLowerCase())+')\\\\s*'),'').replace(/[^a-z0-9]+/g,'');")
rep("function fmt(n){ if(n===null||n===undefined||isNaN(n)) return '0'; return Number(n).toLocaleString('en-IN',{maximumFractionDigits:2}); }",
    "function fmt(n){ if(n===null||n===undefined||isNaN(n)) return '0'; return Number(n).toLocaleString(numLocale(),{maximumFractionDigits:2}); }")
rep("  let ti = find(/tower|block|area|building|wing/i), li = find(/level|floor|storey|story/i);\n  let pi = hdr.findIndex((h,i)=> i!==ti && /pour|segment|section|zone|part/i.test(h));",
    "  let ti = find(new RegExp('tower|block|area|building|wing|zone|package|'+escRe(T('zone')), 'i')), li = find(new RegExp('level|floor|storey|story|stage|'+escRe(T('level')), 'i'));\n  let pi = hdr.findIndex((h,i)=> i!==ti && i!==li && new RegExp('pour|segment|section|zone|part|bay|element|'+escRe(T('pour')), 'i').test(h));")
rep("res.errors.push('No header row found ", "res.errors.push(`No header row found ")
rep("reading columns as Tower, Level, Pour, Planned date.'); }", "reading columns as ${T('zone')}, ${T('level')}, ${T('pour')}, planned date.`); }")
rep("return LABOUR_TOWER_OPTIONS.map(t=>`<option value=\"${t}\" ${selected===t?'selected':''}>${t==='ALL'?'ALL':t.replace('Tower ','')}</option>`).join('');",
    "return LABOUR_TOWER_OPTIONS.map(t=>`<option value=\"${escH(t)}\" ${selected===t?'selected':''}>${t==='ALL'?'ALL':escH(shortZone(t))}</option>`).join('');")
rep("${p.tower==='ALL'?'ALL':p.tower.replace('Tower ','')}", "${p.tower==='ALL'?'ALL':escH(shortZone(p.tower))}")
# pour grid
rep("`${hiddenN} pour(s) hidden (already cast, or planned after ${horizon}) ", "`${hiddenN} ${escH(tl('pour'))}(s) hidden (already cast, or planned after ${horizon}) ")
rep("choose <b>All pours</b> to see them.`", "choose <b>All ${escH(tl('pours'))}</b> to see them.`")
rep("> cast today</label>`);", "> cast today</label>`);")   # wording kept: casting applies to any part built at a time
rep("class=\"hint\">No active pours${lvSel.value? ' on '+escH(lvSel.value) : ''} ", "class=\"hint\">No active ${escH(tl('pours'))}${lvSel.value? ' on '+escH(lvSel.value) : ''} ")
rep("choose <b>All pours</b> to see every pour.</td></tr>`;", "choose <b>All ${escH(tl('pours'))}</b> to see every ${escH(tl('pour'))}.</td></tr>`;")
rep('<table class="pg-table"><thead><tr><th class="pg-s1">Level</th><th class="pg-s2">Pour</th>', '<table class="pg-table"><thead><tr><th class="pg-s1">${escH(T(\'level\'))}</th><th class="pg-s2">${escH(T(\'pour\'))}</th>')
rep('<td colspan="4" class="pg-s1">Today at these pours</td>', '<td colspan="4" class="pg-s1">Today at these ${escH(tl(\'pours\'))}</td>')
# structure tab
rep("""'<div class="warn-banner">No floors or pours are set up yet. In <b>Settings &rarr; Floors &amp; pours</b>, paste a table from Excel with one row per pour (Tower, Level, Pour, Planned pour date, and optional budget quantities per BOQ item).</div>'""",
    """`<div class="warn-banner">No ${escH(tl('levels'))} or ${escH(tl('pours'))} are set up yet. In <b>Settings &rarr; Floors &amp; pours</b>, paste a table from Excel with one row per ${escH(tl('pour'))} (${escH(T('zone'))}, ${escH(T('level'))}, ${escH(T('pour'))}, planned date, and optional budget quantities per BOQ item).</div>`""")
rep("${[['Pours cast', `", "${[[T('pours')+' cast', `")
rep("['Levels complete', `", "[T('levels')+' complete', `")
rep("`<table class=\"st-table\"><thead><tr><th>Level</th>${Array.from({length:maxP},(_,i)=>`<th>Pour ${i+1}</th>`).join('')}<th class=\"num\">Level cast</th>",
    "`<table class=\"st-table\"><thead><tr><th>${escH(T('level'))}</th>${Array.from({length:maxP},(_,i)=>`<th>${escH(T('pour'))} ${i+1}</th>`).join('')}<th class=\"num\">${escH(T('level'))} cast</th>")
rep("""box.innerHTML = '<div class="hint">Click a pour or a level to see budget vs achieved.</div>';""",
    """box.innerHTML = `<div class="hint">Click a ${escH(tl('pour'))} or a ${escH(tl('level'))} to see budget vs achieved.</div>`;""")
rep('id="stOpenEntry">Enter progress for this pour</button>', 'id="stOpenEntry">Enter progress for this ${escH(tl(\'pour\'))}</button>')
rep("if(P.tower!==towerSelect.value && !(await pgGuard(()=>{}))) return;", "if(!(await leaveGuard('tower'))) return;")
rep("const lines = [['Tower','Level','Pour','Planned pour date',", "const lines = [[T('zone'),T('level'),T('pour'),'Planned date',")
# plan editor + settings text
rep('<div class="field"><label>Tower</label><select id="planTower"></select></div>', '<div class="field"><label>${escH(T(\'zone\'))}</label><select id="planTower"></select></div>')
rep('<th>When</th><th>By</th><th>Tower</th><th>Date</th><th>Item</th>', '<th>When</th><th>By</th><th>${escH(T(\'zone\'))}</th><th>Date</th><th>Item</th>')
rep('''<div class="hint">Paste from Excel, one row per pour, with a header row: <b>Tower | Level | Pour | Planned pour date</b>, then optional budget columns headed by BOQ item number (e.g. <i>13</i> or <i>13 Shuttering</i>) or BOQ ID. List levels bottom to top &mdash; that order drives the slab-cycle calculation.''',
    '''<div class="hint">Paste from Excel, one row per ${escH(tl('pour'))}, with a header row: <b>${escH(T('zone'))} | ${escH(T('level'))} | ${escH(T('pour'))} | Planned date</b>, then optional budget columns headed by BOQ item number (e.g. <i>13</i> or <i>13 Shuttering</i>) or BOQ ID. List ${escH(tl('levels'))} bottom to top &mdash; that order drives the cycle-time calculation.''')
rep('placeholder="Tower&#9;Level&#9;Pour&#9;Planned pour date&#9;13&#9;28&#10;Tower E&#9;L1&#9;P1&#9;05-10-2026&#9;120&#9;14"',
    'placeholder="${escH(T(\'zone\'))}&#9;${escH(T(\'level\'))}&#9;${escH(T(\'pour\'))}&#9;Planned date&#9;13&#9;28&#10;${escH(CFG.towers[0]||T(\'zone\')+\' 1\')}&#9;L1&#9;P1&#9;05-10-2026&#9;120&#9;14"')

# ---------------------------------------------------------------- JS: modules
rep("function entryMode(){ return (poursOf(towerSelect.value).length && entryModeSel.value==='pours') ? 'pours' : 'tower'; }",
    "function entryMode(){ return (modOn('structure') && poursOf(towerSelect.value).length && entryModeSel.value==='pours') ? 'pours' : 'tower'; }")
rep("  const hasPours = poursOf(tower).length>0;\n  document.getElementById('entryModeField')", "  const hasPours = modOn('structure') && poursOf(tower).length>0;\n  document.getElementById('entryModeField')")
rep("""'mat|']]
      .forEach(""", """'mat|']].filter(x=> modOn(x[0]))
      .forEach(""")
rep("    if(nC) chips.push(", "    if(nC && modOn('concrete')) chips.push(")
rep("    if(nR) chips.push(", "    if(nR && modOn('rain')) chips.push(")

# ---------------------------------------------------------------- JS: money (overview, S-curve, export)
rep("document.getElementById('ovBigSub').textContent = 'Rs. '+fmt(achievedValue/10000000)+' Cr of Rs. '+fmt(totalValue/10000000)+' Cr, as of '+date",
    "document.getElementById('ovBigSub').textContent = moneyText(achievedValue)+' of '+moneyText(totalValue)+', as of '+date")
rep("row.innerHTML = `<div class=\"name\">${t.replace('Tower ','T-')}</div><div class=\"bar-track\"><div class=\"bar-fill\" style=\"width:${width}%\"></div></div><div class=\"pct-num\">${fmt(av/10000000)} Cr</div>`;",
    "row.innerHTML = `<div class=\"name\" title=\"${escH(t)}\">${escH(t)}</div><div class=\"bar-track\"><div class=\"bar-fill\" style=\"width:${width}%\"></div></div><div class=\"pct-num\">${moneyBig(av)} ${escH(MONEY().big)}</div>`;")
rep("    const variance = (dayA-dayP)/1e7;", "    const DIV = MONEY().div, variance = (dayA-dayP)/DIV;")
rep("<td class=\"num\">${fmt(dayP/1e7)}</td><td class=\"num\">${fmt(dayA/1e7)}</td>", "<td class=\"num\">${fmt(dayP/DIV)}</td><td class=\"num\">${fmt(dayA/DIV)}</td>")
rep("<td class=\"num\">${fmt(cumP/1e7)}</td><td class=\"num\">${fmt(cumA/1e7)}</td>", "<td class=\"num\">${fmt(cumP/DIV)}</td><td class=\"num\">${fmt(cumA/DIV)}</td>")
rep("  const maxVal = Math.max(1, ...points.map(pt=> Math.max(pt.cumP, pt.cumA)))/1e7;", "  const DIV = MONEY().div, maxVal = Math.max(1, ...points.map(pt=> Math.max(pt.cumP, pt.cumA)))/DIV;")
rep("  const lineFor = key => points.map((pt,i)=> `${x(i)},${y(pt[key]/1e7)}`).join(' ');", "  const lineFor = key => points.map((pt,i)=> `${x(i)},${y(pt[key]/DIV)}`).join(' ');")
rep("const planAuditRows = [['When','Tower','Date','Item','S.No','Old Value','New Value']];", "const planAuditRows = [['When',T('zone'),'Date','Item','S.No','Old Value','New Value']];")
rep("const progressLogHeader = ['Tower','Date','S.No','BOQ ID','Item','UOM','Planned Qty','Achieved Qty'];", "const progressLogHeader = [T('zone'),'Date','S.No','BOQ ID','Item','UOM','Planned Qty','Achieved Qty'];")
rep("const finDayHeader = ['Date','Planned (Cr)','Achieved (Cr)','Cumulative Planned (Cr)','Cumulative Achieved (Cr)','Variance (Cr)'];",
    "const BIG = bigLabel(), DIVX = MONEY().div;\n  const finDayHeader = ['Date',`Planned (${BIG})`,`Achieved (${BIG})`,`Cumulative Planned (${BIG})`,`Cumulative Achieved (${BIG})`,`Variance (${BIG})`];")
rep("finDayRows.push([d, Number((dayP/1e7).toFixed(4)), Number((dayA/1e7).toFixed(4)), Number((fCumP/1e7).toFixed(4)), Number((fCumA/1e7).toFixed(4)), Number(((dayA-dayP)/1e7).toFixed(4))]);",
    "finDayRows.push([d, Number((dayP/DIVX).toFixed(4)), Number((dayA/DIVX).toFixed(4)), Number((fCumP/DIVX).toFixed(4)), Number((fCumA/DIVX).toFixed(4)), Number(((dayA-dayP)/DIVX).toFixed(4))]);")
rep("const labourHeader = ['Date','Contractor','Tower','Category', ...labourFields, 'Total'];", "const labourHeader = ['Date','Contractor',T('zone'),'Category', ...labourFields, 'Total'];")
rep("const concreteRows = [['Date','Tower','Structure','Grade','Qty (CUM)']];", "const concreteRows = [['Date',T('zone'),'Structure','Grade','Qty (CUM)']];")
rep("const bbsRows = [['Date','Start','End','Duration','Qty Certified','UOM','Tower','Staff','Remarks']];", "const bbsRows = [['Date','Start','End','Duration','Qty Certified','UOM',T('zone'),'Staff','Remarks']];")

# ---------------------------------------------------------------- JS: printable DPR, aware of modules and words
rep_between("function renderDprSheet(){", "document.getElementById('printDprBtn')", r"""function renderDprSheet(){
  const date = dateInput.value;
  const box = document.getElementById('dprSheet');
  let totalValue=0, achievedValue=0;
  const progRows = CFG.items.map(it=>{
    const achievedAll = achievedThroughAllTowers(it.sno, date);
    let todaySum = 0, todayPlanSum = 0;
    CFG.towers.forEach(t=>{ const rec = store.progress[t+'|'+date]; if(rec && rec[it.sno]!==undefined){ todaySum += entryAch(rec, it.sno); todayPlanSum += entryPlan(rec, it.sno); } });
    totalValue += it.total_qty*it.rate;
    if(isQuantifiable(it)) achievedValue += achievedAll*it.rate;
    return {it, achievedAll, todaySum, todayPlanSum, pct: it.total_qty>0? achievedAll/it.total_qty*100:0};
  }).filter(r=> r.todaySum>0 || r.todayPlanSum>0 || r.achievedAll>0);
  const overallPct = totalValue>0 ? (achievedValue/totalValue*100) : 0;
  const none = (n, text)=> `<tr><td colspan="${n}">${text}</td></tr>`;
  const kv = [['Financial progress', overallPct.toFixed(1)+'%'], ['Value done to date', moneyText(achievedValue)]];
  const sections = [['Physical progress (items with activity to date)', `<table><thead><tr><th>Item</th><th>UOM</th><th class="num">Today planned</th><th class="num">Today achieved</th><th class="num">Cum. achieved</th><th class="num">Total BOQ</th><th class="num">%</th></tr></thead>
      <tbody>${progRows.length? progRows.map(r=>`<tr><td>${escH(r.it.short)}</td><td>${escH(r.it.uom)}</td><td class="num">${fmt(r.todayPlanSum)}</td><td class="num">${fmt(r.todaySum)}</td><td class="num">${fmt(r.achievedAll)}</td><td class="num">${fmt(r.it.total_qty)}</td><td class="num">${r.pct.toFixed(0)}%</td></tr>`).join('') : none(7, 'No progress recorded')}</tbody></table>`]];
  if(modOn('labour')){
    const rows = store.labour[date] || [], camp = store.labourCamp[date] || [];
    let lt = 0; rows.forEach(r=> Object.values(r.counts||{}).forEach(v=> lt += (v||0)));
    let ct = 0; camp.forEach(r=> ct += (r.count||0));
    kv.push(['Labour on site', fmt(lt)], ['Labour on leave (camp)', fmt(ct)]);
    sections.push(['Labour strength', `<table><thead><tr><th>Contractor</th><th>${escH(T('zone'))}</th><th>Category</th><th class="num">Total</th></tr></thead>
      <tbody>${rows.length? rows.map(r=>{ let t=0; Object.values(r.counts||{}).forEach(v=> t+=(v||0)); return `<tr><td>${escH(r.contractor||'—')}</td><td>${escH(r.tower||'—')}</td><td>${escH(r.category||'—')}</td><td class="num">${fmt(t)}</td></tr>`; }).join('') : none(4, 'No labour recorded')}</tbody></table>
      ${camp.length? `<table style="margin-top:10px;"><thead><tr><th>On leave (camp)</th><th>Category</th><th class="num">Count</th><th>Remark</th></tr></thead><tbody>${camp.map(r=> `<tr><td>${escH(r.contractor||'—')}</td><td>${escH(r.category||'—')}</td><td class="num">${fmt(r.count)}</td><td>${escH(r.remark||'—')}</td></tr>`).join('')}</tbody></table>` : ''}`]);
  }
  if(modOn('machinery')){
    const rec = store.machinery[date] || {}, list = CFG.machinery.filter(m=> rec[m.sno]).map(m=> ({label:m.label, count:rec[m.sno]}));
    kv.push(['Machinery units', fmt(list.reduce((s,m)=> s+m.count, 0))]);
    sections.push(['Machinery on site', `<table><thead><tr><th>Equipment</th><th class="num">Count</th></tr></thead><tbody>${list.length? list.map(m=> `<tr><td>${escH(m.label)}</td><td class="num">${fmt(m.count)}</td></tr>`).join('') : none(2, 'No machinery recorded')}</tbody></table>`]);
  }
  if(modOn('material')){
    const rec = store.material[date] || {};
    CFG.material_items.forEach(mi=> kv.push([mi.label+' received', fmt(rec[mi.key]||0)+' '+mi.uom]));
    const staff = CFG.staff_roles.map(sr=> ({label:sr.label, count: rec[staffKey(sr)]!==undefined? rec[staffKey(sr)] : sr.default}));
    sections.push(['Staff on site', `<table><thead><tr><th>Role</th><th class="num">Count</th></tr></thead><tbody>${staff.length? staff.map(x=> `<tr><td>${escH(x.label)}</td><td class="num">${fmt(x.count||0)}</td></tr>`).join('') : none(2, 'No staff roles set up')}</tbody></table>${rec.remark? `<p class="hint">Material remark: ${escH(rec.remark)}</p>` : ''}`]);
  }
  if(modOn('concrete')){
    const today = (store.concrete||[]).filter(r=> r.date===date); let q = 0; today.forEach(r=> q += (r.qty||0));
    kv.push(['Concrete poured', fmt(q)+' CUM']);
    sections.push(['Concrete pours', `<table><thead><tr><th>${escH(T('zone'))}</th><th>Structure</th><th>Grade</th><th class="num">Qty (CUM)</th></tr></thead><tbody>${today.length? today.map(c=> `<tr><td>${escH(c.tower)}</td><td>${escH(c.structure)}</td><td>${escH(c.grade)}</td><td class="num">${fmt(c.qty)}</td></tr>`).join('') : none(4, 'No pours logged')}</tbody></table>`]);
  }
  if(modOn('rain')){
    const today = (store.rain||[]).filter(r=> r.date===date);
    sections.push(['Rain', `<table><thead><tr><th>Start</th><th>End</th><th>Intensity</th><th>Work affected</th></tr></thead><tbody>${today.length? today.map(r=> `<tr><td>${escH(r.start||'—')}</td><td>${escH(r.end||'—')}</td><td>${escH(r.intensity)}</td><td>${escH(r.affected||'—')}</td></tr>`).join('') : none(4, 'No rain logged')}</tbody></table>`]);
  }
  if(modOn('hindrance')){
    const open = (store.hindrance||[]).filter(h=> h.start && h.start<=date && (h.ongoing || !h.end || h.end>=date));
    sections.push(['Hindrances in force', `<table><thead><tr><th>Description</th><th>Since</th><th>Until</th></tr></thead><tbody>${open.length? open.map(h=> `<tr><td>${escH(h.desc)}</td><td>${escH(h.start)}</td><td>${h.ongoing || !h.end? 'Ongoing' : escH(h.end)}</td></tr>`).join('') : none(3, 'No hindrances on this day')}</tbody></table>`]);
  }
  if(modOn('bbs')){
    const today = (store.bbs||[]).filter(r=> r.date===date);
    if(today.length) sections.push(['BBS checks', `<table><thead><tr><th>${escH(T('zone'))}</th><th class="num">Qty certified</th><th>UOM</th><th>Staff</th><th>Remarks</th></tr></thead><tbody>${today.map(r=> `<tr><td>${escH(r.tower)}</td><td class="num">${fmt(r.qty)}</td><td>${escH(r.uom)}</td><td>${escH(r.staff)}</td><td>${escH(r.remarks)}</td></tr>`).join('')}</tbody></table>`]);
  }
  const names = recordedByNames(date);
  box.innerHTML = `
    <h2>Daily Progress Report</h2>
    <div class="dpr-sub">${escH(CFG.project.contractor||'')} &middot; ${escH(CFG.project.name||'')}${CFG.project.employer? ' &middot; Employer: '+escH(CFG.project.employer) : ''} &middot; Report date: ${date}${names.length? ' &middot; Recorded by '+escH(names.join(', ')) : ''}</div>
    <div class="dpr-kv">${kv.map(([k,v])=> `<div>${escH(k)}<br><b>${escH(v)}</b></div>`).join('')}</div>
    ${sections.map(([title, html], i)=> `<div class="dpr-section"><h4>${String.fromCharCode(65+i)}. ${escH(title)}</h4>${html}</div>`).join('')}
  `;
}
""")

# ---------------------------------------------------------------- JS: workbook names after a rename
rep("""    plan: store.plan||{}, progress: store.progress||{}, machinery: store.machinery||{}, labour: store.labour||{},""",
    """    plan: aliasZoneKeys(store.plan||{}), progress: aliasZoneKeys(store.progress||{}), machinery: store.machinery||{}, labour: aliasLabour(store.labour||{}),""")
rep("const rolled=await DPRX.rollover(baked.bytes, T, store.periods[ym].closing, next);", "const rolled=await DPRX.rollover(baked.bytes, T, aliasZoneObj(store.periods[ym].closing), next);")
rep("if(X.items.length!==CFG.items.length || X.zones.some(z=>!CFG.towers.includes(z))){", "if(X.items.length!==CFG.items.length || X.zones.some(z=> !isProjectZone(z))){")
rep("      template:T, bakedThrough:'',", "      template:T, bakedThrough:'', terms: CFG.terms, money: CFG.money,")

# ---------------------------------------------------------------- JS: settings
rep("""      <h4>Towers / zones</h4>
      <div class="hint">Used across Progress, Labour, BBS checking. The Labour tab always also offers an "ALL" option for contractors assigned everywhere.</div>
      ${stringListEditorHtml('cfgTowers', CFG.towers)}
    </div>
""", """      <h4>${escH(T('zones'))}</h4>
      <div class="hint">Used across progress, labour and the site logs; the Labour tab also offers <b>ALL</b> for contractors working everywhere. To rename one, edit its name here: what was recorded against it (progress, plan, ${escH(tl('pours'))}, labour, engineers&rsquo; access) moves to the new name when you save.</div>
      ${stringListEditorHtml('cfgTowers', CFG.towers)}
    </div>
    ${projectSettingsHtml()}
""")
rep("""      <button class="btn ghost" id="cfgAddItem" style="margin-top:8px;">+ Add BOQ item</button>""",
    """      <button class="btn ghost" id="cfgAddItem" style="margin-top:8px;">+ Add BOQ item</button>
      <button class="btn ghost" id="cfgPasteItems" style="margin-top:8px;">Paste from Excel&hellip;</button>""")
rep("  const nextSno = () => Math.max(0, ...CFG.items.map(it=>it.sno)) + 1;",
    "  const nextSno = () => Math.max(0, ...CFG.items.map(it=>it.sno), ...[...document.querySelectorAll('#cfgItemsBody tr')].map(tr=> +tr.dataset.sno||0)) + 1;")
rep("""      <td><input type="text" class="ciBoq" style="width:70px;" value="${(it&&it.boq_id)||''}"></td>
      <td><input type="text" class="ciShort" style="width:170px;" value="${(it&&it.short)||''}"></td>
      <td><input type="text" class="ciDesc" style="width:220px;" value="${(it&&it.desc)||''}"></td>
      <td><input type="text" class="ciUom" style="width:60px;" value="${(it&&it.uom)||''}"></td>""",
    """      <td><input type="text" class="ciBoq" style="width:70px;" value="${escH((it&&it.boq_id)||'')}"></td>
      <td><input type="text" class="ciShort" style="width:170px;" value="${escH((it&&it.short)||'')}"></td>
      <td><input type="text" class="ciDesc" style="width:220px;" value="${escH((it&&it.desc)||'')}"></td>
      <td><input type="text" class="ciUom" style="width:60px;" value="${escH((it&&it.uom)||'')}"></td>""")
rep("""      <td><input type="text" class="cmLabel" style="width:220px;" value="${(m&&m.label)||''}"></td>
      <td><input type="text" class="cmUom" style="width:70px;" value="${(m&&m.uom)||'No'}"></td>""",
    """      <td><input type="text" class="cmLabel" style="width:220px;" value="${escH((m&&m.label)||'')}"></td>
      <td><input type="text" class="cmUom" style="width:70px;" value="${escH((m&&m.uom)||'No')}"></td>""")
rep("""      <td><input type="text" class="cmatLabel" style="width:220px;" value="${(mi&&mi.label)||''}"></td>
      <td><input type="text" class="cmatUom" style="width:90px;" value="${(mi&&mi.uom)||''}"></td>""",
    """      <td><input type="text" class="cmatLabel" style="width:220px;" value="${escH((mi&&mi.label)||'')}"></td>
      <td><input type="text" class="cmatUom" style="width:90px;" value="${escH((mi&&mi.uom)||'')}"></td>""")
rep("""      <td><input type="text" class="csLabel" style="width:220px;" value="${(sr&&sr.label)||''}"></td>""",
    """      <td><input type="text" class="csLabel" style="width:220px;" value="${escH((sr&&sr.label)||'')}"></td>""")
rep("""  document.getElementById('cfgAddItem').addEventListener('click', ()=> addItemRow());""", """  document.getElementById('cfgAddItem').addEventListener('click', ()=> addItemRow());
  document.getElementById('cfgPasteItems').addEventListener('click', async ()=>{
    const rowsNow = ()=> [...itemsBody.querySelectorAll('tr')];
    const idOf = tr=> tr.querySelector('.ciBoq').value.trim().toLowerCase();
    const res = await boqPasteDialog(rowsNow().map(idOf).filter(Boolean));
    if(!res) return;
    const byId = new Map(rowsNow().filter(tr=> idOf(tr)).map(tr=> [idOf(tr), tr]));
    const keep = new Set(); let added = 0, updated = 0, removed = 0;
    res.rows.forEach(r=>{
      const tr = r.boq_id && byId.get(r.boq_id.trim().toLowerCase());
      if(tr){
        tr.querySelector('.ciDesc').value = r.desc; tr.querySelector('.ciShort').value = r.short; tr.querySelector('.ciUom').value = r.uom;
        tr.querySelector('.ciRate').value = r.rate; tr.querySelector('.ciQty').value = r.total_qty; keep.add(tr); updated++;
      } else {
        addItemRow({sno: nextSno(), boq_id: r.boq_id, short: r.short, desc: r.desc, uom: r.uom, rate: r.rate, total_qty: r.total_qty});
        keep.add(itemsBody.lastElementChild); added++;
      }
    });
    if(res.mode==='replace') rowsNow().forEach(tr=>{ if(!keep.has(tr)){ tr.remove(); removed++; } });
    flash(`${added} added, ${updated} updated${removed? ', '+removed+' removed' : ''} \\u2014 press Save changes to keep them`);
  });""")
rep("""  wireStringListEditor('cfgGrades');
""", """  wireStringListEditor('cfgGrades');
  wireProjectSettings();
""")
rep("""    const newTowers = readStringListEditor('cfgTowers');
""", """    const newTowers = readStringListEditor('cfgTowers');
    const dupT = newTowers.find((t,i)=> newTowers.findIndex(x=> x.toLowerCase()===t.toLowerCase())!==i);
    if(dupT){ uiAlert(`\\u201c${dupT}\\u201d is listed twice. Each ${tl('zone')} needs its own name.`, 'Duplicate name'); return; }
    if(!newTowers.length){ uiAlert(`Keep at least one ${tl('zone')}.`, 'Nothing listed'); return; }
    const renames = readTowerRenames();
    const clash = renames.find(r=> CFG.towers.includes(r.to));
    if(clash){ uiAlert(`\\u201c${clash.to}\\u201d is already the name of a ${tl('zone')}. Rename one at a time, saving in between, or pick a different name.`, 'Name already used'); return; }
    renames.forEach(r=> renameZone(r.from, r.to));
    const proj = readProjectSettings();
""")
rep("""      labour_presets_default: CFG.labour_presets_default
    });""", """      labour_presets_default: CFG.labour_presets_default,
      terms: proj.terms, money: proj.money, modules: proj.modules
    });""")

# ---------------------------------------------------------------- JS: files between devices
rep("""  const file = {kind:'dpr-entries', format:1, app:'DPR Portal v'+APP_VERSION, projectId: CFG.projectId, projectName: CFG.project.name||'',""",
    """  const file = {kind:'dpr-entries', format:1, app:'DPR Portal v'+APP_VERSION, projectId: CFG.projectId, projectName: CFG.project.name||'', setupUpdatedAt: CFG.updatedAt||'',""")
rep("const st = mergeEntries(x.j.data, {dryRun:true}), t = mergeTotals(st);", "const st = mergeEntries(renamedEntries(x.j.data, x.j.setupUpdatedAt), {dryRun:true}), t = mergeTotals(st);")
rep("const t = mergeTotals(mergeEntries(x.j.data, {}));", "const t = mergeTotals(mergeEntries(renamedEntries(x.j.data, x.j.setupUpdatedAt), {}));")
rep("""  store.config = pkg.config; CFG = store.config;""", """  store.config = pkg.config; CFG = store.config;
  if(same) applyPendingRenames(); else store.renamesAppliedAt = ((CFG.renames||[]).slice(-1)[0]||{}).at || '';""")

# ---------------------------------------------------------------- version
rep('title="What&rsquo;s new">v2.2</button>', 'title="What&rsquo;s new">v2.3</button>')
rep('<span class="ver">DPR Portal v2.2</span>', '<span class="ver">DPR Portal v2.3</span>')
rep(' &middot; Baseline from the project workbook (DPR_Format.xlsx for Linkbay); site-log history stays in that workbook',
    ' &middot; <span id="footWb">Baseline from the project workbook</span>; site-log history before the portal stays in that workbook')
rep("const APP_VERSION = '2.2';", "const APP_VERSION = '2.3';")
rep("""const CHANGELOG = [
  {v:'v2.2',""", """const CHANGELOG = [
  {v:'v2.3', date:'19 Oct 2026', items:[
    'Your project’s own words: call areas Towers, Blocks, Buildings, Zones or Sections, floors Levels, Floors or Stages, and pours Pours, Bays or Segments. Labels follow everywhere, including the printable DPR and exports (Settings, Project).',
    'Money and numbers: rupees in crore or lakh, dollars, dirhams, riyals, pounds or euro in millions, or your own unit, with Indian or international digit grouping.',
    'Modules: switch off what a project doesn’t report (floors & pours, labour, machinery, material & staff, or any site log). Tabs, day status and the printable DPR follow; saved data is kept.',
    'BOQ items can be pasted straight from Excel in Settings, BOQ & lists. Headings can be in any order; rows with a matching BOQ number are updated, section headings are left out.',
    'Renaming a tower (or block, zone…) in Settings now carries everything recorded against it to the new name: progress, plan, pours, cast dates, labour, engineers’ access. Exports still find it in the project workbook, and entries from engineers who haven’t had the new setup yet are translated on import.',
    'The printable DPR lists hindrances in force on the day and BBS checks, and shows the value of work done to date.',
    'Fixes: new BOQ rows added together in Settings no longer share a number; names with quotes no longer break the settings tables; opening a pour from the Structure tab offers to save unsaved progress first.']},
  {v:'v2.2',""")

# ---------------------------------------------------------------- module + init
mod = open(SP+'/v23/flex.js', encoding='utf-8').read()
rep("/* =================== INIT =================== */", mod + "\n/* =================== INIT =================== */")
rep("""  syncDateControls();
  updateDirtyUI();
}
bootAccess();""", """  syncDateControls();
  updateDirtyUI();
}
applyTerms();
applyModules();
bootAccess();""")

open(DST, 'w', encoding='utf-8').write(s)
js = s[s.index('<script>\n', s.index('</head>'))+8 : s.rindex('</script>')]
open(SP+'/v23/js_v23.js', 'w', encoding='utf-8').write(js)
print('size', len(s), '| 1e7 left:', js.count('/1e7'), '| Rs. left:', js.count("'Rs. '"))
