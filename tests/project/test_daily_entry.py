"""v2.2 faster-entry checks: day status, date stepper, unsaved guards, item filter, keyboard, copy/prefill, lock."""
from playwright.sync_api import sync_playwright
import pathlib, sys, json
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
def dmsg(pg): return pg.inner_text('.dlg-overlay .dlg-msg') if pg.locator('.dlg-overlay .dlg-msg').count() else None
def set_date(pg, d): pg.fill('#dateInput', d); pg.dispatch_event('#dateInput','change'); pg.wait_for_timeout(350)
def chips(pg): return [c.replace('\n',' ') for c in pg.locator('#dayCheck .dchip').all_inner_texts()]
def chip_cls(pg, k): return pg.get_attribute(f'#dayCheck .dchip[data-k="{k}"]', 'class')
def ev(pg, js): return pg.evaluate(js)
def tab(pg, t): pg.click(f'.tab[data-tab="{t}"]'); pg.wait_for_timeout(200)

with sync_playwright() as p:
    br = p.chromium.launch()
    ctx = br.new_context(accept_downloads=True, viewport={'width':1300,'height':900})
    a = ctx.new_page(); watch(a, 'A')
    a.goto(URL, wait_until='load'); a.wait_for_timeout(700)
    a.click('#wcSetup'); a.fill('#pmName','Plan Manager'); a.fill('#pmPw','secret12'); a.fill('#pmPw2','secret12'); dlg(a,'Create account'); a.wait_for_timeout(300); dlg(a,'I’ve saved it')
    a.wait_for_timeout(400)
    log('1 strip today:', chips(a), '| today btn disabled:', a.is_disabled('#dateToday'))
    a.screenshot(path=SP+'/e1_top.png', clip={'x':0,'y':0,'width':1300,'height':330})

    set_date(a, '2026-09-22'); a.select_option('#towerSelect', label='Tower E'); a.wait_for_timeout(400)
    pills = a.locator('#itemFilter button').all_inner_texts()
    log('2 pills:', [x.replace('\n',' ') for x in pills], '| active:', a.get_attribute('#itemFilter button.active','data-f'), '| info:', a.inner_text('#itemFilterInfo'))
    vis = ev(a, "[...entryBody.querySelectorAll('tr[data-sno]')].filter(t=>!t.hidden).length"); total = ev(a, "entryBody.querySelectorAll('tr[data-sno]').length")
    log('   visible rows', vis, 'of', total)
    a.fill('#itemSearch', 'shutter'); a.wait_for_timeout(150)
    log('3 search shutter:', a.inner_text('#itemFilterInfo'), '| rows:', ev(a, "[...entryBody.querySelectorAll('tr[data-sno]')].filter(t=>!t.hidden).map(t=>t.dataset.sno).join(',')"))
    a.press('#itemSearch', 'Escape'); a.wait_for_timeout(100)
    log('   after Esc:', repr(a.input_value('#itemSearch')), a.inner_text('#itemFilterInfo'))
    a.click('#itemFilter button[data-f="all"]'); a.wait_for_timeout(150)
    log('4 all pill:', a.get_attribute('#itemFilter button.active','data-f'), '| visible:', ev(a, "[...entryBody.querySelectorAll('tr[data-sno]')].filter(t=>!t.hidden).length"))
    a.screenshot(path=SP+'/e2_items.png')

    # keyboard: type, Enter moves down
    first = a.locator('#entryBody tr[data-sno]:not([hidden]) .today-input').first
    sno1 = first.get_attribute('data-sno'); first.click(); a.keyboard.type('7'); a.keyboard.press('Enter'); a.wait_for_timeout(100)
    sno2 = ev(a, "document.activeElement.dataset.sno")
    a.keyboard.press('ArrowDown'); a.wait_for_timeout(50); sno3 = ev(a, "document.activeElement.dataset.sno")
    a.keyboard.press('ArrowUp'); a.wait_for_timeout(50); sno4 = ev(a, "document.activeElement.dataset.sno")
    log('5 enter/arrows:', sno1, '->', sno2, '->', sno3, '->', sno4, '| value of first:', ev(a, f"entryBody.querySelector('.today-input[data-sno=\"{sno1}\"]').value"))
    a.wait_for_timeout(300)
    log('6 tab unsaved:', 'unsaved' in a.get_attribute('.tab[data-tab="entry"]','class'), '| chip:', chip_cls(a,'progress'), '| save pulse:', 'pulse' in a.get_attribute('#saveBtn','class'))
    # date change with unsaved: keep editing
    a.click('#datePrev'); a.wait_for_timeout(300)
    log('7 guard:', dtitle(a), '|', (dmsg(a) or '').replace('\n',' / '))
    a.screenshot(path=SP+'/e3_guard.png')
    dlg(a, 'Keep editing')
    log('   kept: date', a.input_value('#dateInput'), '| value', ev(a, f"entryBody.querySelector('.today-input[data-sno=\"{sno1}\"]').value"))
    a.click('#datePrev'); a.wait_for_timeout(300); dlg(a, 'Save and continue'); a.wait_for_timeout(400)
    log('8 saved & moved: date', a.input_value('#dateInput'), '| saved 22 Sep:', ev(a, f"JSON.stringify(store.progress['Tower E|2026-09-22'][{sno1}])"), '| unsaved now:', 'unsaved' in a.get_attribute('.tab[data-tab="entry"]','class'))

    # over-BOQ soft check on 21 Sep
    it = ev(a, "(()=>{ const it = CFG.items.find(i=> i.total_qty>50 && [...entryBody.querySelectorAll('tr[data-sno]')].some(t=> +t.dataset.sno===i.sno && !t.hidden)); return {sno:it.sno, total:it.total_qty}; })()")
    inp = f'#entryBody .today-input[data-sno="{it["sno"]}"]'
    a.fill(inp, str(int(it['total']*3))); a.wait_for_timeout(100)
    log('9 over class:', 'over' in a.get_attribute(inp,'class'), '| title:', a.get_attribute(inp,'title')[:70])
    a.keyboard.press('Control+s'); a.wait_for_timeout(300)
    log('   check dialog:', dtitle(a), '|', (dmsg(a) or '')[:110].replace('\n',' / '))
    dlg(a, 'Go back')
    log('   not saved:', ev(a, f"!(store.progress['Tower E|2026-09-21']||{{}})[{it['sno']}]"))
    a.keyboard.press('Control+s'); a.wait_for_timeout(300); dlg(a, 'Save anyway'); a.wait_for_timeout(300)
    log('   saved anyway:', ev(a, f"JSON.stringify((store.progress['Tower E|2026-09-21']||{{}})[{it['sno']}])"))
    # re-save without changes: no prompt
    a.keyboard.press('Control+s'); a.wait_for_timeout(300)
    log('   resave prompt:', dtitle(a))

    # labour on 21 Sep
    tab(a, 'labour')
    a.fill('#labourBody tr:first-child .contractorInput', 'ABC Infra'); a.fill('#labourBody tr:first-child .categoryInput', 'Shuttering')
    a.fill('#labourBody tr:first-child .labourCount >> nth=0', '12'); a.fill('#labourBody tr:first-child .labourCount >> nth=1', '3')
    a.click('#addLabourRow'); a.wait_for_timeout(200)
    a.keyboard.press('Control+s'); a.wait_for_timeout(300)
    log('10 labour saved rows:', ev(a, "JSON.stringify(store.labour['2026-09-21'])"))
    a.click('#dateNext'); a.wait_for_timeout(400)
    log('11 date:', a.input_value('#dateInput'), '| labour note:', a.inner_text('#labourNote') if a.is_visible('#labourNote') else None)
    a.screenshot(path=SP+'/e4_labour_note.png')
    a.click('#labourCopyLink'); a.wait_for_timeout(200); log('   copy dialog:', dtitle(a)); dlg(a, 'Crews and counts'); a.wait_for_timeout(300)
    log('   copied:', a.input_value('#labourBody tr:first-child .contractorInput'), a.input_value('#labourBody tr:first-child .labourCount >> nth=0'), '| tab unsaved:', 'unsaved' in a.get_attribute('.tab[data-tab="labour"]','class'))
    # Enter in labour moves down the column; first add a second row
    a.click('#addLabourRow'); a.click('#labourBody tr:first-child .labourCount >> nth=2'); a.keyboard.type('5'); a.keyboard.press('Enter'); a.wait_for_timeout(80)
    log('   labour enter -> row', ev(a, "[...labourBody.querySelectorAll('tr')].indexOf(document.activeElement.closest('tr'))"), 'field', ev(a, "document.activeElement.dataset.field"))
    a.click('#saveLabourBtn'); a.wait_for_timeout(300)
    log('   saved 22 Sep:', ev(a, "store.labour['2026-09-22'].length"), '| note hidden:', not a.is_visible('#labourNote'), '| unsaved:', 'unsaved' in a.get_attribute('.tab[data-tab="labour"]','class'))

    # machinery: save on 22 Sep, prefill on 23 Sep, zero stays zero
    tab(a, 'machinery')
    log('12 mach note 22:', a.inner_text('#machNote') if a.is_visible('#machNote') else None)
    m = a.locator('#machineryBody .machineryCount')
    m.nth(0).fill('3'); m.nth(1).fill(''); a.keyboard.press('Control+s'); a.wait_for_timeout(300)
    log('   saved:', ev(a, "JSON.stringify(store.machinery['2026-09-22'])"))
    set_date(a, '2026-09-22')
    log('   reload 22: first', m.nth(0).input_value(), '| second', repr(m.nth(1).input_value()))
    a.click('#dateNext'); a.wait_for_timeout(400)
    log('   23 prefill: first', m.nth(0).input_value(), '| second', repr(m.nth(1).input_value()), '| note:', a.inner_text('#machNote') if a.is_visible('#machNote') else None, '| unsaved:', 'unsaved' in a.get_attribute('.tab[data-tab="machinery"]','class'))
    # material & staff
    tab(a, 'material')
    s0 = a.locator('#staffRows .staffInput').nth(0)
    s0.fill('4'); a.locator('#materialRows .materialInput').nth(0).fill('25'); a.click('#saveMaterialBtn'); a.wait_for_timeout(300)
    a.click('#dateNext'); a.wait_for_timeout(400)
    log('13 staff 24:', s0.input_value(), '| material:', repr(a.locator('#materialRows .materialInput').nth(0).input_value()), '| note:', a.inner_text('#matNote') if a.is_visible('#matNote') else None)

    # day status for 22 Sep and tower menu
    set_date(a, '2026-09-22'); a.wait_for_timeout(300)
    log('14 strip 22 Sep:', chips(a), '| progress chip:', chip_cls(a,'progress'))
    a.click('#dayCheck .dchip[data-k="progress"]'); a.wait_for_timeout(200)
    log('   tower menu:', [x.replace('\n',' ') for x in a.locator('#popMenu button').all_inner_texts()][:4])
    a.screenshot(path=SP+'/e5_menu.png', clip={'x':0,'y':0,'width':1300,'height':520})
    a.click('#popMenu button:has-text("Tower D")'); a.wait_for_timeout(300)
    log('   tower now:', a.input_value('#towerSelect'), '| entry active:', 'active' in a.get_attribute('.tab[data-tab="entry"]','class'))
    a.click('#dayCheck .dchip[data-k="labour"]'); a.wait_for_timeout(200)
    log('   labour chip -> tab:', a.get_attribute('.tab.active','data-tab'))

    # export with unsaved changes
    tab(a, 'entry')
    a.locator('#entryBody tr[data-sno]:not([hidden]) .today-input').first.fill('2'); a.wait_for_timeout(200)
    a.click('#exportBtn'); a.wait_for_timeout(300)
    log('15 export guard:', dtitle(a), '|', (dmsg(a) or '').replace('\n',' / ')[:90])
    with a.expect_download(timeout=40000) as dl: dlg(a, 'Continue without them')
    log('   export file:', dl.value.suggested_filename)
    a.wait_for_timeout(500)
    if a.locator('.dlg-overlay').count(): log('   after export dialog:', dtitle(a)); dlg(a, 'OK')
    # tower change guard -> discard
    a.select_option('#towerSelect', label='Tower C'); a.wait_for_timeout(300)
    log('16 tower guard:', dtitle(a)); dlg(a, 'Discard'); a.wait_for_timeout(200)
    log('   tower:', a.input_value('#towerSelect'), '| D entry discarded:', ev(a, "!store.progress['Tower D|2026-09-22']"))

    # sign out with unsaved labour -> save and sign out
    tab(a, 'labour'); a.fill('#labourBody tr:first-child .categoryInput', 'Shuttering crew'); a.wait_for_timeout(200)
    a.click('#userChip'); a.click('#userMenu button:has-text("Sign out")'); a.wait_for_timeout(300)
    log('17 signout guard:', dtitle(a)); dlg(a, 'Save and sign out'); a.wait_for_timeout(400)
    log('   saved category:', ev(a, "store.labour['2026-09-22'][0].category"), '| sign-in shown:', a.is_visible('#authOverlay'))
    a.click('.user-tile:has-text("Plan Manager")'); a.fill('#authSecret','secret12'); a.click('#authGo'); a.wait_for_timeout(500)

    # screen lock
    a.click('#settingsGearBtn'); a.wait_for_timeout(300)
    a.select_option('#tmLock', '5'); a.wait_for_timeout(200)
    log('18 autoLock:', ev(a, 'CFG.team.autoLock'))
    a.click('#closeSettingsX'); a.wait_for_timeout(200)
    tab(a, 'machinery'); a.locator('#machineryBody .machineryCount').nth(2).fill('9'); a.wait_for_timeout(200)
    ev(a, 'lastActivity = Date.now() - 6*60000')
    a.wait_for_timeout(11000)
    log('   locked:', a.is_visible('#lockForm'), '| overlay class:', a.get_attribute('#authOverlay','class'))
    a.screenshot(path=SP+'/e6_lock.png')
    a.fill('#lockSecret', 'wrongpass'); a.press('#lockSecret','Enter'); a.wait_for_timeout(300)
    log('   wrong:', a.inner_text('#lockErr'))
    a.fill('#lockSecret', 'secret12'); a.press('#lockSecret','Enter'); a.wait_for_timeout(400)
    log('   unlocked:', not a.is_visible('#authOverlay'), '| typed kept:', a.locator('#machineryBody .machineryCount').nth(2).input_value())
    ev(a, 'lockScreen()'); a.wait_for_timeout(200)
    a.reload(wait_until='load'); a.wait_for_timeout(800)
    log('19 after reload locked:', a.is_visible('#lockForm'))
    a.fill('#lockSecret', 'secret12'); a.press('#lockSecret','Enter'); a.wait_for_timeout(400)
    log('   unlocked after reload:', not a.is_visible('#authOverlay'), '| ME:', ev(a, 'ME && ME.name'))

    # site logs: new rows start on the entry date
    set_date(a, '2026-09-20'); tab(a, 'sitelogs'); a.click('#addConcreteRow'); a.wait_for_timeout(100)
    log('20 new concrete row date:', a.locator('#concreteBody .cDate').last.input_value())
    a.locator('#concreteBody .cQty').last.fill('42'); a.wait_for_timeout(250)
    log('   sitelogs unsaved:', 'unsaved' in a.get_attribute('.tab[data-tab="sitelogs"]','class'), '| subtab:', 'unsaved' in a.get_attribute('.subtab[data-sub="concrete"]','class'))
    a.keyboard.press('Control+s'); a.wait_for_timeout(300)
    log('   saved concrete:', ev(a, "store.concrete.length"), '| strip:', chips(a))

    # phone
    ph = ctx.new_page(); watch(ph, 'P'); ph.set_viewport_size({'width':400,'height':860}); ph.goto(URL, wait_until='load'); ph.wait_for_timeout(700)
    if ph.is_visible('#authOverlay'):
        if ph.locator('#lockForm').count(): ph.fill('#lockSecret','secret12'); ph.press('#lockSecret','Enter')
        else: ph.click('.user-tile:has-text("Plan Manager")'); ph.fill('#authSecret','secret12'); ph.click('#authGo')
        ph.wait_for_timeout(500)
    ph.fill('#dateInput','2026-09-22'); ph.dispatch_event('#dateInput','change'); ph.wait_for_timeout(400)
    ph.select_option('#towerSelect', label='Tower E'); ph.wait_for_timeout(400)
    log('21 phone overflow:', ph.evaluate('document.documentElement.scrollWidth - document.documentElement.clientWidth'))
    ph.screenshot(path=SP+'/e7_phone_top.png')
    ph.evaluate("document.getElementById('itemTools').scrollIntoView()"); ph.wait_for_timeout(100)
    ph.screenshot(path=SP+'/e8_phone_items.png')
    ph.click('.tab[data-tab="labour"]'); ph.wait_for_timeout(300)
    ph.evaluate("document.getElementById('labourTable').scrollIntoView()"); ph.wait_for_timeout(100)
    ph.screenshot(path=SP+'/e9_phone_labour.png')
    log('   phone overflow labour:', ph.evaluate('document.documentElement.scrollWidth - document.documentElement.clientWidth'))
    log('ERRORS:', errors)
    br.close()
