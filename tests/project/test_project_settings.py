"""v2.3 checks: words, money, modules, BOQ paste, tower rename (with export alias and stale entries files)."""
from playwright.sync_api import sync_playwright
import pathlib, sys, json, openpyxl, datetime
import os as _os, pathlib as _pl, sys as _sys
_HERE = _pl.Path(__file__).resolve().parent
if len(_sys.argv) < 2: _sys.exit('usage: python3 %s <portal built from your project seed>.html  (see tests/README.md)' % _pl.Path(__file__).name)
FILE = str(_pl.Path(_sys.argv[1]).resolve())
SP = str(_pl.Path(_os.environ.get('DPR_TEST_OUT', _HERE.parent / 'output'))); _pl.Path(SP).mkdir(parents=True, exist_ok=True)
FIXTURES = str(_HERE.parent / 'fixtures')
URL = pathlib.Path(FILE).resolve().as_uri()
errors = []
def log(*a): print(*a); sys.stdout.flush()
def watch(pg, tag):
    pg.on('pageerror', lambda e: errors.append(f'{tag} pageerror: {e}'))
    pg.on('console', lambda m: errors.append(f'{tag} console: {m.text}') if m.type=='error' and 'fonts.g' not in m.text and 'ERR_' not in m.text else None)
    pg.on('dialog', lambda d: d.accept() if d.type=='beforeunload' else (errors.append(f'{tag} NATIVE: {d.message[:60]}'), d.dismiss()))
def dlg(pg, text, timeout=8000):
    pg.wait_for_selector('.dlg-overlay .dlg', timeout=timeout); pg.click(f'.dlg-overlay .dlg button:has-text("{text}")'); pg.wait_for_timeout(300)
def dtitle(pg): return pg.inner_text('.dlg-overlay .dlg-title') if pg.locator('.dlg-overlay .dlg-title').count() else None
def set_date(pg, d): pg.fill('#dateInput', d); pg.dispatch_event('#dateInput','change'); pg.wait_for_timeout(350)
def ev(pg, js): return pg.evaluate(js)
def settings(pg, pane):
    pg.click('#settingsGearBtn'); pg.wait_for_timeout(400); pg.click(f'.set-tabs button[data-pane="{pane}"]'); pg.wait_for_timeout(200)
def save_settings(pg):
    pg.click('#cfgSaveBtn'); pg.wait_for_load_state('load'); pg.wait_for_timeout(1200)

with sync_playwright() as p:
    br = p.chromium.launch()
    ctx = br.new_context(accept_downloads=True, viewport={'width':1300,'height':900})
    a = ctx.new_page(); watch(a, 'A')
    a.goto(URL, wait_until='load'); a.wait_for_timeout(700)
    a.click('#wcSetup'); a.fill('#pmName','Plan Manager'); a.fill('#pmPw','secret12'); a.fill('#pmPw2','secret12'); dlg(a,'Create account'); a.wait_for_timeout(300); dlg(a,'I’ve saved it')
    a.wait_for_timeout(1200)   # let the workbook layout be derived (CFG.template)
    log('0 template zones:', ev(a, "CFG.template && Object.keys(CFG.template.progress.rowMap).length"), '| entry hint:', a.inner_text('#entryHint')[:90])
    # an entry for Tower E before renaming
    set_date(a, '2026-09-22'); a.select_option('#towerSelect', label='Tower E'); a.wait_for_timeout(300)
    a.fill('#entryBody .today-input[data-sno="13"]', '44'); a.click('#saveBtn'); a.wait_for_timeout(400)
    if dtitle(a): dlg(a, 'Save anyway')
    log('1 saved E 13:', ev(a, "JSON.stringify(store.progress['Tower E|2026-09-22'][13])"))

    # ---- words, money, modules
    settings(a, 'project')
    a.select_option('#cfgTermPreset', label='Block › Floor › Pour'); a.wait_for_timeout(100)
    log('2 term inputs:', a.input_value('#cfgTermZone'), a.input_value('#cfgTermLevel'), a.input_value('#cfgTermPour'))
    a.select_option('#cfgMoneyPreset', 'usd-m'); a.wait_for_timeout(100)
    log('   money example:', a.inner_text('#cfgMoneyExample'))
    a.uncheck('.cfgMod[value="machinery"]'); a.uncheck('.cfgMod[value="bbs"]')
    a.screenshot(path=SP+'/g1_settings_project.png', full_page=False)
    save_settings(a)
    log('3 after save: label', a.inner_text('label[for="towerSelect"]'), '| foot', a.inner_text('#footLabel'), '| rate', a.inner_text('#thRate'))
    log('   tabs visible:', [t for t in a.locator('.tab:not([hidden])').all_inner_texts()])
    log('   subtabs visible:', [t for t in a.locator('.subtab:not([hidden])').all_inner_texts()])
    log('   strip:', [c.replace('\n',' ') for c in a.locator('#dayCheck .dchip').all_inner_texts()])
    log('   labour head:', a.locator('#labourHeadRow th').nth(2).inner_text())
    a.click('.tab[data-tab="overview"]'); a.wait_for_timeout(500)
    log('4 overview:', a.inner_text('#ovTowerTitle'), '|', a.inner_text('#ovBigSub')[:80], '| fin head:', a.inner_text('#finHead').replace('\n',' ')[:80])
    log('   machinery card hidden:', a.locator('#ovMach').evaluate("e=> e.closest('.card').hidden"), '| tower row:', a.locator('#towerBars .tower-row').first.inner_text().replace('\n',' | '))
    a.click('.tab[data-tab="dpr"]'); a.wait_for_timeout(400)
    log('5 dpr sections:', [h for h in a.locator('#dprSheet .dpr-section h4').all_inner_texts()])
    log('   dpr kv:', a.locator('#dprSheet .dpr-kv div').nth(1).inner_text().replace('\n',': '))
    a.screenshot(path=SP+'/g2_dpr.png')
    a.click('.tab[data-tab="entry"]'); a.wait_for_timeout(200)

    # ---- BOQ paste
    settings(a, 'lists')
    n0 = ev(a, "document.querySelectorAll('#cfgItemsBody tr').length")
    a.click('#cfgPasteItems'); a.wait_for_timeout(200)
    boq1 = ev(a, "CFG.items[0].boq_id")
    paste = "Item No\tDescription of work\tUnit\tQty\tRate\n" \
            "EARTHWORK\t\t\t\t\n" \
            f"{boq1}\tBackfilling with approved material, compacted in layers\tCUM\t12,500\t690\n" \
            "9.1\tWaterproofing of basement raft with \"APP\" membrane, 4mm\tSQM\t8,200\t455.5\n" \
            "9.2\tGranite cladding to lobby walls\tSQM\t1,150\t3,250"
    a.fill('#bqText', paste); a.wait_for_timeout(200)
    log('6 paste preview:', a.locator('#bqPreview .hint').first.inner_text())
    a.screenshot(path=SP+'/g3_boq_paste.png')
    dlg(a, 'Use these items'); a.wait_for_timeout(200)
    n1 = ev(a, "document.querySelectorAll('#cfgItemsBody tr').length")
    log('   rows before/after:', n0, n1, '| snos of new:', ev(a, "[...document.querySelectorAll('#cfgItemsBody tr')].slice(-2).map(tr=>tr.dataset.sno).join(',')"))
    save_settings(a)
    log('7 items saved:', ev(a, "CFG.items.length"), '| updated first:', ev(a, "JSON.stringify([CFG.items[0].total_qty, CFG.items[0].rate])"), '| new:', ev(a, "JSON.stringify(CFG.items.slice(-2).map(i=>[i.sno,i.boq_id,i.short,i.uom,i.total_qty,i.rate]))"))

    # ---- rename Tower E -> Tower Echo (labels now say Block)
    settings(a, 'project')
    inp = a.locator('#cfgTowers input').nth(ev(a, "CFG.towers.indexOf('Tower E')"))
    inp.fill('Tower Echo')
    save_settings(a)
    log('8 towers:', ev(a, "CFG.towers.join(',')"), '| alias:', ev(a, "JSON.stringify(CFG.zoneAlias)"), '| renames:', ev(a, "CFG.renames.length"))
    log('   progress moved:', ev(a, "JSON.stringify(store.progress['Tower Echo|2026-09-22'] && store.progress['Tower Echo|2026-09-22'][13])"), '| old gone:', ev(a, "!store.progress['Tower E|2026-09-22']"),
        '| achieved moved:', ev(a, "!!CFG.achieved['Tower Echo'] && !CFG.achieved['Tower E']"), '| stamps:', ev(a, "Object.keys(store.stamps).filter(k=>k.includes('Tower Echo')).length"))
    # export still writes Tower E's workbook row
    with a.expect_download(timeout=40000) as dl: a.click('#exportBtn')
    xf = SP+'/flex_export.xlsx'; dl.value.save_as(xf)
    a.wait_for_timeout(400)
    if a.locator('.dlg-overlay').count(): log('   export note:', dtitle(a)); dlg(a, 'OK')
    d = openpyxl.load_workbook(xf)['Data']; dv = openpyxl.load_workbook(xf, data_only=True)['Data']
    col = {dv.cell(row=6,column=c).value.strftime('%Y-%m-%d'): c for c in range(14,90) if isinstance(dv.cell(row=6,column=c).value, datetime.datetime)}
    log('9 export Tower E item13 Sep22 A (alias):', d.cell(row=59, column=col['2026-09-22']+1).value)

    # stale entries file from an engineer still using "Tower E"
    stale = {"kind":"dpr-entries","format":1,"projectId": ev(a,"CFG.projectId"),"projectName":"x","setupUpdatedAt":"2026-01-01T00:00:00.000Z",
             "from":{"id":"u-x","name":"Old Copy","role":"engineer"},"exportedAt":"2026-10-19T08:00:00.000Z","range":{"from":"2026-09-23","to":"2026-09-23"},
             "data":{"progressLoc":{"Tower E|2026-09-23":{"":{"13":7}}},"labour":{},"labourCamp":{},"machinery":{},"material":{},"concrete":[],"rain":[],"hindrance":[],"bbs":[],"pourCast":{},
                     "stamps":{"p|Tower E|2026-09-23|":{"by":"u-x","at":"2026-10-19T07:59:00.000Z"}},"tomb":{}}}
    sf = SP+'/stale_entries.json'; open(sf,'w').write(json.dumps(stale))
    settings(a, 'team')
    with a.expect_file_chooser() as fc: a.click('#tmImportEntries')
    fc.value.set_files(sf); a.wait_for_timeout(600)
    log('10 import preview:', (dtitle(a) or ''), '|', a.locator('.merge-file .hint').first.inner_text()[:80] if a.locator('.merge-file').count() else None)
    dlg(a, 'Import'); a.wait_for_timeout(400)
    log('   landed:', ev(a, "JSON.stringify(store.progress['Tower Echo|2026-09-23'] && store.progress['Tower Echo|2026-09-23'][13])"), '| orphan:', ev(a, "!!store.progress['Tower E|2026-09-23']"))
    a.click('#closeSettingsX'); a.wait_for_timeout(200)
    # structure tab words (pours exist? none) and pour paste header with custom words
    a.click('.tab[data-tab="structure"]'); a.wait_for_timeout(300)
    log('11 structure banner:', a.inner_text('#stSummary')[:90])
    settings(a, 'pours')
    a.fill('#pourPaste', "Block\tFloor\tPour\tPlanned date\t13\nTower Echo\tL1\tP1\t20-10-2026\t50\nTower Echo\tL2\tP1\t30-10-2026\t50")
    a.click('#pourPreviewBtn'); a.wait_for_timeout(200)
    log('12 pour paste preview:', a.inner_text('#pourPreview')[:120].replace('\n',' '))
    a.click('#pourApplyBtn'); a.wait_for_load_state('load'); a.wait_for_timeout(1000)
    log('   pours:', ev(a, "CFG.pours.length"), '| grid head:', ev(a, "(document.querySelector('.pg-table thead tr')||{innerText:''}).innerText.slice(0,40)"))
    a.select_option('#towerSelect', label='Tower Echo'); a.wait_for_timeout(300)
    log('   mode field:', a.is_visible('#entryModeField'), '| mode option:', a.locator('#entryMode option').first.inner_text(), '| grid head:', ev(a, "(document.querySelector('.pg-table thead tr')||{innerText:''}).innerText.replace(/\\n/g,' ').slice(0,40)"))
    # turn floors & pours off: no pour mode
    settings(a, 'project'); a.uncheck('.cfgMod[value="structure"]'); save_settings(a)
    a.select_option('#towerSelect', label='Tower Echo'); a.wait_for_timeout(300)
    log('13 structure off: tab hidden', a.locator('.tab[data-tab="structure"]').evaluate('e=>e.hidden'), '| mode field visible', a.is_visible('#entryModeField'), '| item list visible', a.is_visible('#towerTableWrap'))
    a.screenshot(path=SP+'/g4_entry.png')
    log('ERRORS:', errors)
    br.close()
