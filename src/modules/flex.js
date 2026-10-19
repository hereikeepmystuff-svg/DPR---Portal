/* =================== FITS ANY PROJECT (v2.3) =================== */
/* The project's own words, money and modules are part of its setup (CFG). The planning manager
   sets them in Settings → Project; they reach engineers with the setup file. Nothing already
   entered changes when they do. */
const TERM_PRESETS = [
  ['Tower','Level','Pour'], ['Block','Floor','Pour'], ['Building','Floor','Bay'], ['Wing','Floor','Pour'],
  ['Zone','Level','Segment'], ['Section','Stage','Segment'], ['Package','Stage','Element'], ['Area','Level','Bay']
];
const MONEY_PRESETS = {
  'inr-cr':   {sym:'Rs.', big:'Cr',   div:1e7, locale:'en-IN', label:'Indian rupees, in crore'},
  'inr-lakh': {sym:'Rs.', big:'Lakh', div:1e5, locale:'en-IN', label:'Indian rupees, in lakh'},
  'usd-m':    {sym:'$',   big:'M',    div:1e6, locale:'en-US', label:'US dollars, in millions'},
  'aed-m':    {sym:'AED', big:'M',    div:1e6, locale:'en-US', label:'UAE dirhams, in millions'},
  'sar-m':    {sym:'SAR', big:'M',    div:1e6, locale:'en-US', label:'Saudi riyals, in millions'},
  'qar-m':    {sym:'QAR', big:'M',    div:1e6, locale:'en-US', label:'Qatari riyals, in millions'},
  'gbp-m':    {sym:'£',   big:'M',    div:1e6, locale:'en-GB', label:'Pounds sterling, in millions'},
  'eur-m':    {sym:'€',   big:'M',    div:1e6, locale:'en-IE', label:'Euro, in millions'},
  'custom':   {sym:'',    big:'',     div:1,   locale:'en-US', label:'Other (set below)'}
};
function MONEY(){
  const m = CFG.money || {}, p = MONEY_PRESETS[m.preset] || MONEY_PRESETS['inr-cr'];
  return {preset: m.preset || 'inr-cr', sym: m.sym!=null? m.sym : p.sym, big: m.big!=null? m.big : p.big, div: +m.div || p.div, locale: m.locale || p.locale};
}
function numLocale(){ return (CFG && CFG.money && CFG.money.locale) || 'en-IN'; }
function moneyBig(v){ return fmt(v / MONEY().div); }
function moneyText(v){ const m = MONEY(); return [m.sym, fmt(v / m.div), m.big].filter(Boolean).join(' '); }
function bigLabel(){ const m = MONEY(); return m.big || m.sym || 'value'; }
function tl(k){ return T(k).toLowerCase(); }
function plural(w){ return /(s|x|z|ch|sh)$/i.test(w)? w+'es' : /[^aeiou]y$/i.test(w)? w.slice(0,-1)+'ies' : w+'s'; }
function escRe(s){ return String(s).replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); }
function shortZone(t){ return String(t).replace(new RegExp('^('+escRe(T('zone'))+'|tower)\\s+', 'i'), ''); }

/* ---------- modules ---------- */
const MODULES = [['structure','Floors & pours'], ['labour','Labour'], ['machinery','Machinery'], ['material','Material & staff'],
  ['concrete','Concrete pours log'], ['rain','Rain register'], ['hindrance','Hindrances'], ['bbs','BBS checking']];
function modOn(k){ return !(CFG.modules && CFG.modules[k]===false); }
function applyModules(){
  const tab = k=> document.querySelector(`.tab[data-tab="${k}"]`);
  ['structure','labour','machinery','material'].forEach(k=>{ const t = tab(k); if(t) t.hidden = !modOn(k); });
  tab('sitelogs').hidden = !LOGS.some(modOn);
  document.querySelectorAll('.subtab').forEach(st=> st.hidden = !modOn(st.dataset.sub));
  const actSub = document.querySelector('.subtab.active');
  if(actSub && actSub.hidden){ const f = document.querySelector('.subtab:not([hidden])'); if(f) f.click(); }
  const act = document.querySelector('.tab.active');
  if(act && act.hidden) tab('entry').click();
  [['ovLabour','labour'], ['ovMach','machinery'], ['ovMat','material']].forEach(([id,k])=>{ const c = document.getElementById(id); if(c) c.closest('.card').hidden = !modOn(k); });
}

/* ---------- words on the page ---------- */
function applyTerms(){
  document.querySelectorAll('[data-term]').forEach(el=> el.textContent = T(el.dataset.term));
  const em = document.getElementById('entryMode');
  if(em){ em.options[0].textContent = T('pours')+' (table)'; em.options[1].textContent = 'Whole '+tl('zone')+' (item list)'; }
  const sh = document.getElementById('pgShow');
  if(sh){ sh.options[0].textContent = 'Active '+tl('pours'); sh.options[1].textContent = 'All '+tl('pours'); }
  const set = (id, html)=>{ const el = document.getElementById(id); if(el) el.innerHTML = html; };
  set('footLabel', `Selected ${escH(tl('zone'))} &mdash; totals`);
  set('stLegendNote', `Top ${escH(tl('level'))} first &middot; % = share of the ${escH(tl('pour'))}&rsquo;s budget achieved, by value`);
  set('presetHint', `A contractor assigned to every ${escH(tl('zone'))} can use the <b>ALL</b> option instead of one row per ${escH(tl('zone'))}.`);
  set('ovTowerTitle', `Progress by ${escH(tl('zone'))}`);
  const M = MONEY();
  set('thRate', `Rate${M.sym? ' ('+escH(M.sym)+')' : ''}`);
  const big = escH(bigLabel());
  set('finHead', `<th>Date</th><th class="num">Planned (${big})</th><th class="num">Achieved (${big})</th><th class="num">Cum. planned (${big})</th><th class="num">Cum. achieved (${big})</th><th class="num">Variance (${big})</th>`);
  const base = CFG.baseline_as_of;
  set('entryHint', `Before today = ${base? `the cumulative quantity recorded in the project workbook (to ${escH(dayLabel(base))}) plus ` : ''}every entry saved here for earlier dates. Financial progress = the sum of cumulative quantity &times; rate over all items and ${escH(tl('zones'))}. &middot; Planned is fixed for the month: only a planning manager changes it, through <b>Edit monthly plan</b>, and every change is logged. &middot; Keys: <kbd>Enter</kbd> or <kbd>&darr;</kbd> moves down the list, <kbd>Ctrl</kbd>+<kbd>S</kbd> saves, <kbd>/</kbd> jumps to the item search.`);
  const fw = document.getElementById('footWb');
  if(fw) fw.textContent = 'Baseline from '+((CFG.template && CFG.template.fileName)? CFG.template.fileName : 'the project workbook');
  const zl = document.getElementById('zoneList');
  if(zl) zl.innerHTML = CFG.towers.map(t=> `<option value="${escH(t)}">`).join('');
}

/* ---------- renaming a tower / area, with everything recorded against it ---------- */
function moveKeys(obj, fromPrefix, toPrefix){
  if(!obj) return 0; let n = 0;
  Object.keys(obj).forEach(k=>{ if(k.startsWith(fromPrefix)){ obj[toPrefix + k.slice(fromPrefix.length)] = obj[k]; delete obj[k]; n++; } });
  return n;
}
function renameZoneInData(x, from, to){
  ['progress','progressLoc','plan'].forEach(k=> moveKeys(x[k], from+'|', to+'|'));
  moveKeys(x.stamps, 'p|'+from+'|', 'p|'+to+'|');
  moveKeys(x.pourCast, from+'|', to+'|');
  moveKeys(x.tomb, 'cast|'+from+'|', 'cast|'+to+'|');
  if(x.pourGridExtra && x.pourGridExtra[from]){ x.pourGridExtra[to] = x.pourGridExtra[from]; delete x.pourGridExtra[from]; }
  Object.values(x.labour||{}).forEach(rows=> (rows||[]).forEach(r=>{ if(r && r.tower===from) r.tower = to; }));
  (x.labourPresets||[]).forEach(p=>{ if(p.tower===from) p.tower = to; });
  (x.concrete||[]).forEach(r=>{ if(r.tower && locNorm(r.tower)===locNorm(from)) r.tower = to; });
  const sf = from.replace(/^Tower /,''), st = to.replace(/^Tower /,'');
  (x.bbs||[]).forEach(r=>{ if(r.tower===sf || r.tower===from) r.tower = st; });
  Object.values(x.periods||{}).forEach(p=>{ if(p && p.closing && p.closing[from]){ p.closing[to] = p.closing[from]; delete p.closing[from]; } });
}
function renameZone(from, to){
  const at = nowIso();
  renameZoneInData(store, from, to);
  if(CFG.achieved && CFG.achieved[from]){ CFG.achieved[to] = CFG.achieved[from]; delete CFG.achieved[from]; }
  moveKeys(CFG.tower_daily_history, from+'|', to+'|');
  (CFG.pours||[]).forEach(p=>{ if(p.tower===from) p.tower = to; });
  (CFG.labour_presets_default||[]).forEach(p=>{ if(p.tower===from) p.tower = to; });
  ((CFG.team||{}).users||[]).forEach(u=>{ if(u.towers) u.towers = u.towers.map(t=> t===from? to : t); });
  /* the project workbook keeps its own labels: exports translate back to them */
  const A = CFG.zoneAlias = CFG.zoneAlias || {};
  const wbZones = Object.keys(((CFG.template||{}).progress||{}).rowMap||{});
  const wb = A[from] || (wbZones.includes(from)? from : '');
  delete A[from]; if(wb && wb!==to) A[to] = wb;
  CFG.renames = (CFG.renames||[]).concat([{from, to, at}]);
  store.renamesAppliedAt = at;
  logAct('Project settings', `Renamed ${from} to ${to}`);
}
/* A device that gets a newer setup applies renames it hasn't seen to its own entries. */
function applyPendingRenames(){
  const since = store.renamesAppliedAt || '';
  const todo = (CFG.renames||[]).filter(r=> (r.at||'') > since);
  todo.forEach(r=> renameZoneInData(store, r.from, r.to));
  if(todo.length) store.renamesAppliedAt = todo[todo.length-1].at;
  return todo.length;
}
/* Entries files made before a rename reached the engineer: translate them on the way in. */
function renamedEntries(d, since){
  const rs = (CFG.renames||[]).filter(r=> (r.at||'') > (since||''));
  if(!rs.length) return d;
  const x = JSON.parse(JSON.stringify(d));
  rs.forEach(r=> renameZoneInData(x, r.from, r.to));
  return x;
}
function aliasZoneKeys(obj){
  const A = CFG.zoneAlias || {}; if(!obj || !Object.keys(A).length) return obj;
  const out = {}; Object.keys(obj).forEach(k=>{ const i = k.indexOf('|'), z = i<0? k : k.slice(0,i); out[(A[z]||z)+(i<0? '' : k.slice(i))] = obj[k]; }); return out;
}
function aliasZoneObj(obj){
  const A = CFG.zoneAlias || {}; if(!obj || !Object.keys(A).length) return obj;
  const out = {}; Object.keys(obj).forEach(z=> out[A[z]||z] = obj[z]); return out;
}
function aliasLabour(lab){
  const A = CFG.zoneAlias || {}; if(!lab || !Object.keys(A).length) return lab;
  const out = {}; Object.keys(lab).forEach(d=> out[d] = (lab[d]||[]).map(r=> A[r.tower]? Object.assign({}, r, {tower: A[r.tower]}) : r)); return out;
}
function isProjectZone(z){ return CFG.towers.includes(z) || Object.values(CFG.zoneAlias||{}).includes(z); }

/* ---------- BOQ from Excel ---------- */
function shortName(desc){
  let s = String(desc||'').replace(/\s+/g,' ').trim();
  const cut = s.search(/[.;:(]|,\s/); if(cut>12) s = s.slice(0, cut).trim();
  return s.length>48? s.slice(0,46).trim()+'…' : s;
}
function parseBoqPaste(text){
  const res = {rows:[], errors:[], headings:0, guessed:false};
  const lines = String(text||'').replace(/\r/g,'').split('\n').filter(l=> l.trim());
  if(!lines.length) return res;
  const split = l=> l.includes('\t')? l.split('\t') : l.split(/,(?=(?:[^"]*"[^"]*")*[^"]*$)/).map(c=> c.replace(/^"|"$/g,''));
  const num = s=>{ const v = parseFloat(String(s==null? '' : s).replace(/[,\s]/g,'').replace(/[^\d.\-]/g,'')); return isNaN(v)? 0 : v; };
  const hdr = split(lines[0]).map(h=> h.trim().toLowerCase());
  const find = (re, not)=> hdr.findIndex((h,i)=> re.test(h) && !(not||[]).includes(i));
  let c = {};
  c.desc = find(/desc|particular|item\s*name|name of (the )?work|activity|work item/);
  c.qty = find(/qty|quantity/);
  c.rate = find(/rate|price|unit\s*cost/, [c.qty]);
  c.uom = find(/^uom|unit|^u\.?o\.?m/, [c.qty, c.rate]);
  c.boq = find(/boq|item\s*(no|code|ref)|ref\.?\s*no|^s\.?\s*no|^sl\.?\s*no|^no\.?$|^item$/, [c.desc]);
  c.short = find(/short/, [c.desc]);
  let start = 1;
  if(c.desc<0 || (c.qty<0 && c.rate<0)){
    const n = split(lines[0]).length;
    c = n>=5? {boq:0, desc:1, uom:2, qty:3, rate:4} : n===4? {boq:-1, desc:0, uom:1, qty:2, rate:3} : n===3? {boq:-1, desc:0, uom:1, qty:2, rate:-1} : {boq:-1, desc:0, uom:-1, qty:-1, rate:-1};
    c.short = -1; start = 0; res.guessed = true;
  }
  res.cols = c;
  for(let k=start; k<lines.length; k++){
    const cells = split(lines[k]).map(x=> String(x).trim());
    const get = i=> i>=0? (cells[i]||'') : '';
    const desc = get(c.desc), boq = get(c.boq);
    if(!desc && !boq) continue;
    const qty = num(get(c.qty)), rate = num(get(c.rate)), uom = get(c.uom);
    if(!uom && !qty && !rate){ res.headings++; continue; }           // section headings such as "EARTHWORK"
    res.rows.push({boq_id: boq, desc: desc || boq, short: get(c.short) || shortName(desc || boq), uom, total_qty: qty, rate});
  }
  return res;
}
async function boqPasteDialog(existingIds){
  const node = document.createElement('div');
  node.innerHTML = `<p class="hint" style="margin:0 0 8px;">In Excel, select the BOQ rows (with their heading row if there is one), copy, and paste here. With headings the columns can be in any order: BOQ no., Description, Unit, Quantity, Rate. Rows without a unit, quantity or rate are read as section headings and left out.</p>
    <textarea id="bqText" rows="8" style="width:100%; font-family:var(--mono); font-size:12px;" placeholder="BOQ No&#9;Description&#9;Unit&#9;Qty&#9;Rate"></textarea>
    <div class="seg" style="margin-top:10px;"><label><input type="radio" name="bqMode" value="merge" checked> Add new items, update ones with the same BOQ no.</label><label><input type="radio" name="bqMode" value="replace"> Replace the whole list</label></div>
    <div id="bqPreview" style="margin-top:10px;"></div>`;
  const ta = node.querySelector('#bqText'), pv = node.querySelector('#bqPreview');
  let parsed = {rows:[]};
  const upd = ()=>{
    parsed = parseBoqPaste(ta.value);
    if(!parsed.rows.length){ pv.innerHTML = ta.value.trim()? '<div class="hint">No item rows found yet. Each row needs a description and a unit, quantity or rate.</div>' : ''; return; }
    const match = parsed.rows.filter(r=> r.boq_id && existingIds.includes(r.boq_id.trim().toLowerCase())).length;
    pv.innerHTML = `<div class="hint" style="margin:0 0 6px;"><b>${parsed.rows.length}</b> item(s) read${match? ` &middot; ${match} match existing BOQ numbers` : ''}${parsed.headings? ` &middot; ${parsed.headings} heading row(s) left out` : ''}${parsed.guessed? ' &middot; no heading row, so columns are read in the usual order' : ''}</div>
      <div class="table-scroll" style="max-height:26vh;"><table style="min-width:560px;"><thead><tr><th>BOQ no.</th><th>Short name</th><th>Unit</th><th class="num">Quantity</th><th class="num">Rate</th></tr></thead><tbody>
      ${parsed.rows.slice(0,30).map(r=> `<tr><td>${escH(r.boq_id)}</td><td>${escH(r.short)}</td><td>${escH(r.uom)}</td><td class="num">${fmt(r.total_qty)}</td><td class="num">${fmt(r.rate)}</td></tr>`).join('')}
      </tbody></table></div>${parsed.rows.length>30? `<div class="hint">…and ${parsed.rows.length-30} more</div>` : ''}`;
  };
  ta.addEventListener('input', upd);
  const r = await uiDialog({title:'Paste BOQ items from Excel', node, wide:true, focusEl: ta, cancelValue:false,
    buttons:[{label:'Cancel', value:false}, {label:'Use these items', value:true, primary:true, validate:()=> parsed.rows.length? '' : 'Paste at least one item row.'}]});
  if(r.value!==true) return null;
  return {mode: node.querySelector('input[name="bqMode"]:checked').value, rows: parsed.rows};
}

/* ---------- settings: words, money, modules ---------- */
function projectSettingsHtml(){
  const M = MONEY(), cur = [T('zone'), T('level'), T('pour')].join('|');
  return `
    <div class="settings-section">
      <h4>Words used in this project</h4>
      <div class="hint">What the project calls its main areas, their floors or stages, and the parts built one at a time. Labels change everywhere in the portal; nothing already entered changes.</div>
      <div class="controls">
        <div class="field"><label for="cfgTermPreset">Quick choice</label><select id="cfgTermPreset"><option value="">Custom</option>${TERM_PRESETS.map(p=> `<option value="${escH(p.join('|'))}" ${p.join('|')===cur? 'selected' : ''}>${escH(p.join(' › '))}</option>`).join('')}</select></div>
        <div class="field"><label for="cfgTermZone">Area</label><input type="text" id="cfgTermZone" value="${escH(T('zone'))}" style="width:130px;"></div>
        <div class="field"><label for="cfgTermLevel">Floor or stage</label><input type="text" id="cfgTermLevel" value="${escH(T('level'))}" style="width:130px;"></div>
        <div class="field"><label for="cfgTermPour">Part built at a time</label><input type="text" id="cfgTermPour" value="${escH(T('pour'))}" style="width:130px;"></div>
      </div>
    </div>
    <div class="settings-section">
      <h4>Money and numbers</h4>
      <div class="hint">Financial progress, the S-curve and the summary export use these. BOQ rates are in this currency.</div>
      <div class="controls">
        <div class="field"><label for="cfgMoneyPreset">Currency</label><select id="cfgMoneyPreset">${Object.entries(MONEY_PRESETS).map(([k,p])=> `<option value="${k}" ${k===M.preset? 'selected' : ''}>${escH(p.label)}</option>`).join('')}</select></div>
        <div class="field"><label for="cfgMoneySym">Symbol</label><input type="text" id="cfgMoneySym" value="${escH(M.sym)}" style="width:80px;"></div>
        <div class="field"><label for="cfgMoneyBig">Large amounts in</label><input type="text" id="cfgMoneyBig" value="${escH(M.big)}" style="width:90px;" placeholder="M"></div>
        <div class="field"><label for="cfgMoneyDiv">Which is</label><input type="number" id="cfgMoneyDiv" value="${M.div}" min="1" step="any" style="width:150px;"></div>
        <div class="field"><label for="cfgNumLocale">Digit grouping</label><select id="cfgNumLocale"><option value="en-IN" ${M.locale==='en-IN'? 'selected' : ''}>1,23,45,678 (Indian)</option><option value="en-US" ${M.locale!=='en-IN'? 'selected' : ''}>12,345,678 (international)</option></select></div>
      </div>
      <div class="hint" id="cfgMoneyExample" style="margin:0;"></div>
    </div>
    <div class="settings-section">
      <h4>Modules in use</h4>
      <div class="hint">Switch off what this project doesn&rsquo;t report. A switched-off module leaves the tabs, the day status and the printable DPR, here and on engineers&rsquo; copies. Anything already saved is kept and comes back when it&rsquo;s switched on again.</div>
      <div class="chips">${MODULES.map(([k,l])=> `<label class="chip"><input type="checkbox" class="cfgMod" value="${k}" ${modOn(k)? 'checked' : ''}> ${escH(l)}</label>`).join('')}</div>
    </div>`;
}
function wireProjectSettings(){
  const $ = id=> document.getElementById(id);
  const preset = $('cfgTermPreset');
  preset.onchange = ()=>{ if(!preset.value) return; const [z,l,p] = preset.value.split('|'); $('cfgTermZone').value = z; $('cfgTermLevel').value = l; $('cfgTermPour').value = p; };
  ['cfgTermZone','cfgTermLevel','cfgTermPour'].forEach(id=> $(id).addEventListener('input', ()=>{ const v = [$('cfgTermZone').value.trim(), $('cfgTermLevel').value.trim(), $('cfgTermPour').value.trim()].join('|'); preset.value = TERM_PRESETS.some(p=> p.join('|')===v)? v : ''; }));
  const ex = ()=>{
    const sym = $('cfgMoneySym').value.trim(), big = $('cfgMoneyBig').value.trim(), div = +$('cfgMoneyDiv').value || 1, loc = $('cfgNumLocale').value;
    const v = 123456789.5, f = n=> Number(n).toLocaleString(loc, {maximumFractionDigits:2});
    $('cfgMoneyExample').textContent = `Example: a value of ${[sym, f(v)].filter(Boolean).join(' ')} shows as ${[sym, f(v/div), big].filter(Boolean).join(' ')}.`;
  };
  $('cfgMoneyPreset').onchange = ()=>{ const p = MONEY_PRESETS[$('cfgMoneyPreset').value]; if(p && $('cfgMoneyPreset').value!=='custom'){ $('cfgMoneySym').value = p.sym; $('cfgMoneyBig').value = p.big; $('cfgMoneyDiv').value = p.div; $('cfgNumLocale').value = p.locale==='en-IN'? 'en-IN' : 'en-US'; } ex(); };
  ['cfgMoneySym','cfgMoneyBig','cfgMoneyDiv','cfgNumLocale'].forEach(id=> $(id).addEventListener('input', ex));
  $('cfgNumLocale').addEventListener('change', ex);
  ex();
  document.querySelectorAll('#cfgTowers input').forEach((inp,i)=>{ inp.dataset.orig = CFG.towers[i] || ''; });
}
function readProjectSettings(){
  const $ = id=> document.getElementById(id);
  const z = $('cfgTermZone').value.trim() || 'Tower', l = $('cfgTermLevel').value.trim() || 'Level', p = $('cfgTermPour').value.trim() || 'Pour';
  const modules = {}; document.querySelectorAll('.cfgMod').forEach(c=>{ if(!c.checked) modules[c.value] = false; });
  return {
    terms: {zone:z, level:l, pour:p},
    money: {preset: $('cfgMoneyPreset').value, sym: $('cfgMoneySym').value.trim(), big: $('cfgMoneyBig').value.trim(), div: +$('cfgMoneyDiv').value || 1, locale: $('cfgNumLocale').value},
    modules
  };
}
function readTowerRenames(){
  return [...document.querySelectorAll('#cfgTowers input')].map(i=> ({from: i.dataset.orig||'', to: i.value.trim()}))
    .filter(r=> r.from && r.to && r.from!==r.to && CFG.towers.includes(r.from));
}
