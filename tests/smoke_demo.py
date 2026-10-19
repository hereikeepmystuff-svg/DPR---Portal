"""End-to-end smoke test of the public demo build (dist/dpr-portal.html).

Walks through what a planning manager and a site engineer do in a normal week: first-run setup,
daily progress, labour, machinery, settings (words, money, modules, BOQ paste, renaming an area),
floors & pours, sharing setup and entries files between two devices, the printable DPR, the
screen lock and the phone layout. Any page error, console error or native browser dialog fails it.

Usage:  python3 tests/smoke_demo.py [path/to/portal.html]
        DPR_SHOTS=docs/screenshots python3 tests/smoke_demo.py   # also refresh the documentation screenshots
"""
from playwright.sync_api import sync_playwright
import json, os, pathlib, sys

HERE = pathlib.Path(__file__).resolve().parent
FILE = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else HERE.parent / 'dist' / 'dpr-portal.html').resolve()
URL = FILE.as_uri()
OUT = pathlib.Path(os.environ.get('DPR_TEST_OUT', HERE / 'output')); OUT.mkdir(parents=True, exist_ok=True)
SHOTS = pathlib.Path(os.environ['DPR_SHOTS']) if os.environ.get('DPR_SHOTS') else None
errors, checks = [], []

def log(*a): print(*a); sys.stdout.flush()
def check(name, ok, detail=''):
    checks.append((name, bool(ok)))
    log(('PASS ' if ok else 'FAIL ') + name + (f' — {detail}' if detail != '' else ''))
def watch(pg, tag):
    pg.on('pageerror', lambda e: errors.append(f'{tag} pageerror: {e}'))
    pg.on('console', lambda m: errors.append(f'{tag} console: {m.text}') if m.type == 'error' and 'fonts.g' not in m.text and 'ERR_' not in m.text and 'cdnjs' not in m.text else None)
    pg.on('dialog', lambda d: d.accept() if d.type == 'beforeunload' else (errors.append(f'{tag} native dialog: {d.message[:60]}'), d.dismiss()))
def dlg(pg, text, timeout=8000):
    pg.wait_for_selector('.dlg-overlay .dlg', timeout=timeout); pg.click(f'.dlg-overlay .dlg button:has-text("{text}")'); pg.wait_for_timeout(300)
def dtitle(pg): return pg.inner_text('.dlg-overlay .dlg-title') if pg.locator('.dlg-overlay .dlg-title').count() else None
def set_date(pg, d): pg.fill('#dateInput', d); pg.dispatch_event('#dateInput', 'change'); pg.wait_for_timeout(350)
def ev(pg, js): return pg.evaluate(js)
def strip_text(pg): return ' '.join(pg.inner_text('#dayCheck').split())
def tab(pg, t): pg.click(f'.tab[data-tab="{t}"]'); pg.wait_for_timeout(250)
def settings(pg, pane): pg.click('#settingsGearBtn'); pg.wait_for_timeout(400); pg.click(f'.set-tabs button[data-pane="{pane}"]'); pg.wait_for_timeout(200)
def save_settings(pg): pg.click('#cfgSaveBtn'); pg.wait_for_load_state('load'); pg.wait_for_timeout(1000)
def shot(pg, name, **kw):
    if SHOTS: SHOTS.mkdir(parents=True, exist_ok=True); pg.screenshot(path=str(SHOTS / name), **kw)

with sync_playwright() as p:
    br = p.chromium.launch()
    A = br.new_context(accept_downloads=True, viewport={'width': 1300, 'height': 900}); a = A.new_page(); watch(a, 'PM')
    a.goto(URL, wait_until='load'); a.wait_for_timeout(600)
    shot(a, 'welcome.png')
    a.click('#wcSetup'); a.fill('#pmName', 'Priya Planner'); a.fill('#pmPw', 'secret12'); a.fill('#pmPw2', 'secret12'); dlg(a, 'Create account')
    a.wait_for_timeout(300); check('recovery code offered', dtitle(a) == 'Save your recovery code'); dlg(a, 'I’ve saved it')
    check('signed in as planning manager', a.inner_text('#userChip').startswith('PP'))

    # ---------------- progress: whole-area item list
    set_date(a, '2026-10-15'); a.select_option('#towerSelect', label='Tower A'); a.wait_for_timeout(300)
    check('day status shows four areas', 'Progress 0/4' in strip_text(a), strip_text(a))
    a.fill('#itemSearch', 'raft'); a.wait_for_timeout(150)
    check('item search finds the raft', a.inner_text('#itemFilterInfo') == '1 match')
    a.press('#itemSearch', 'Escape')
    a.click('#entryBody .today-input[data-sno="6"]'); a.keyboard.type('42'); a.keyboard.press('Enter')
    check('Enter moves down the list', ev(a, 'document.activeElement.dataset.sno') == '7')
    a.keyboard.type('55'); a.wait_for_timeout(250)
    check('unsaved changes marked on the tab', 'unsaved' in a.get_attribute('.tab[data-tab="entry"]', 'class'))
    shot(a, 'progress-entry.png')
    a.keyboard.press('Control+s'); a.wait_for_timeout(400)
    check('Ctrl+S saves progress', ev(a, "JSON.stringify(store.progress['Tower A|2026-10-15'][6])") == '{"a":42,"p":0}')
    a.fill('#entryBody .today-input[data-sno="1"]', '20000'); a.click('#saveBtn'); a.wait_for_timeout(300)
    check('entry past the BOQ quantity asks first', dtitle(a) == 'Check before saving'); dlg(a, 'Save anyway')
    a.click('#datePrev'); a.wait_for_timeout(300)
    check('date stepper moves a day back', a.input_value('#dateInput') == '2026-10-14')

    # ---------------- labour, machinery
    tab(a, 'labour')
    a.fill('#labourBody tr:first-child .contractorInput', 'Alpha Formwork Co.'); a.fill('#labourBody tr:first-child .categoryInput', 'Formwork')
    a.fill('#labourBody tr:first-child .labourCount >> nth=0', '18'); a.fill('#labourBody tr:first-child .labourCount >> nth=1', '9')
    a.click('#saveLabourBtn'); a.wait_for_timeout(300)
    a.click('#dateNext'); a.wait_for_timeout(400)
    check('labour offers to copy the last day', a.is_visible('#labourCopyLink'))
    a.click('#labourCopyLink'); dlg(a, 'Crews and counts'); a.wait_for_timeout(200)
    check('crews copied', a.input_value('#labourBody tr:first-child .labourCount >> nth=0') == '18')
    a.keyboard.press('Control+s'); a.wait_for_timeout(300)
    check('labour saved for 15 Oct', ev(a, "store.labour['2026-10-15'].length") == 1)
    tab(a, 'machinery')
    check('machinery starts from the usual counts', a.is_visible('#machNote'))
    a.locator('#machineryBody .machineryCount').nth(0).fill('2'); a.click('#saveMachineryBtn'); a.wait_for_timeout(300)
    a.click('#dateNext'); a.wait_for_timeout(300)
    check('next day copies machinery', a.locator('#machineryBody .machineryCount').nth(0).input_value() == '2')
    a.click('#datePrev'); a.wait_for_timeout(300)
    check('day status after saving', 'Progress 1/4' in strip_text(a) and a.locator('#dayCheck .dchip.done').count() >= 2, strip_text(a))

    # ---------------- settings: words, money, modules, BOQ paste, rename
    settings(a, 'project')
    a.select_option('#cfgTermPreset', label='Block › Floor › Pour'); a.select_option('#cfgMoneyPreset', 'usd-m')
    a.uncheck('.cfgMod[value="bbs"]')
    shot(a, 'settings-project.png')
    save_settings(a)
    check('own words used', a.inner_text('label[for="towerSelect"]').lower() == 'block')
    check('module switched off', a.locator('.subtab[data-sub="bbs"]').evaluate('e=> e.hidden'))
    tab(a, 'overview')
    check('money in the chosen currency', a.inner_text('#ovBigSub').startswith('$ '), a.inner_text('#ovBigSub')[:40])
    settings(a, 'lists'); a.click('#cfgPasteItems')
    a.fill('#bqText', "BOQ No\tDescription\tUnit\tQty\tRate\nFINISHES\t\t\t\t\n6.1\tFalse ceiling in gypsum board\tSQM\t6,400\t980\n6.2\tStone cladding to entrance lobby\tSQM\t850\t3,600")
    a.wait_for_timeout(150); dlg(a, 'Use these items'); save_settings(a)
    check('BOQ pasted from Excel', ev(a, 'CFG.items.length') == 22 and ev(a, 'CFG.items[21].short') == 'Stone cladding to entrance lobby')
    set_date(a, '2026-10-15'); a.select_option('#towerSelect', label='Tower C'); a.wait_for_timeout(300)
    a.fill('#entryBody .today-input[data-sno="7"]', '30'); a.click('#saveBtn'); a.wait_for_timeout(300)
    settings(a, 'project'); a.locator('#cfgTowers input').nth(2).fill('Tower Charlie'); save_settings(a)
    check('renamed area keeps its entries', ev(a, "JSON.stringify(store.progress['Tower Charlie|2026-10-15'][7])") == '{"a":30,"p":0}' and ev(a, "!store.progress['Tower C|2026-10-15']"))

    # ---------------- floors & pours, pour grid
    settings(a, 'pours')
    rows = [('L1', 'P1', '01-10-2026'), ('L1', 'P2', '03-10-2026'), ('L2', 'P1', '09-10-2026'), ('L2', 'P2', '11-10-2026'), ('L3', 'P1', '18-10-2026')]
    a.fill('#pourPaste', "Block\tFloor\tPour\tPlanned date\t6\t7\t9\n" + "\n".join(f"Tower A\t{l}\t{q}\t{d}\t60\t45\t900" for l, q, d in rows))
    a.click('#pourPreviewBtn'); a.wait_for_timeout(150); a.click('#pourApplyBtn'); a.wait_for_load_state('load'); a.wait_for_timeout(900)
    check('pours set up', ev(a, 'CFG.pours.length') == 5)
    set_date(a, '2026-10-16'); a.select_option('#towerSelect', label='Tower A'); a.wait_for_timeout(400)
    cell = lambda lid, c: f'#pourGridBody tr[data-lid="{lid}"] td[data-c="{c}"]'
    a.click(cell('L2|P1', 0)); a.keyboard.type('20'); a.keyboard.press('Tab'); a.keyboard.type('15'); a.keyboard.press('Enter')
    a.check('#pourGridBody tr[data-lid="L2|P1"] .pg-cast')
    shot(a, 'pour-grid.png')
    a.click('#saveBtn'); a.wait_for_timeout(400)
    check('pour grid saved with cast date', ev(a, "store.pourCast['Tower A|L2|P1'] && store.pourCast['Tower A|L2|P1'].date") == '2026-10-16')
    tab(a, 'structure'); check('structure tab drawn', a.locator('#stGrid .st-cell').count() == 5)
    tab(a, 'dpr'); check('printable DPR sections', a.locator('#dprSheet .dpr-section').count() >= 5)
    shot(a, 'printable-dpr.png')
    tab(a, 'entry')

    # ---------------- team, setup file, engineer copy, entries file
    settings(a, 'team')
    a.click('#tmAdd'); a.fill('#pfName', 'Ravi Site'); a.check('.pfZone[value="Tower A"]'); a.fill('#pfSecret', '1357'); dlg(a, 'Add person'); dlg(a, 'OK')
    with a.expect_download() as d1: a.click('#tmExportSetup')
    setup = OUT / 'demo_setup.json'; d1.value.save_as(setup); a.wait_for_timeout(300)
    if a.locator('.dlg-overlay').count(): dlg(a, 'OK')
    a.click('#closeSettingsX')
    B = br.new_context(accept_downloads=True, viewport={'width': 1300, 'height': 900}); b = B.new_page(); watch(b, 'ENG')
    b.goto(URL, wait_until='load'); b.wait_for_timeout(500)
    with b.expect_file_chooser() as fc: b.click('#wcJoin')
    fc.value.set_files(str(setup)); b.wait_for_timeout(500); dlg(b, 'OK'); b.wait_for_load_state('load'); b.wait_for_timeout(800)
    b.click('.user-tile:has-text("Ravi Site")'); b.fill('#authSecret', '1357'); b.click('#authGo'); b.wait_for_timeout(500)
    check('engineer signed in on own copy', 'Ravi Site' in b.inner_text('#userChip'))
    set_date(b, '2026-10-17'); b.select_option('#towerSelect', label='Tower A'); b.wait_for_timeout(300)
    b.select_option('#entryMode', 'tower'); b.wait_for_timeout(300)
    b.fill('#entryBody .today-input[data-sno="8"]', '12.5'); b.keyboard.press('Control+s'); b.wait_for_timeout(400)
    b.select_option('#towerSelect', label='Tower B'); b.wait_for_timeout(300)
    check('other areas are view only for the engineer', b.is_visible('#lockedDateNote'))
    b.click('#userChip'); b.click('#userMenu button:has-text("Send my entries")'); b.wait_for_timeout(200)
    b.fill('#seFrom', '2026-10-01'); b.fill('#seTo', '2026-10-31'); b.dispatch_event('#seTo', 'input')
    with b.expect_download() as d2: dlg(b, 'Save file')
    entries = OUT / 'demo_entries.json'; d2.value.save_as(entries)
    check('entries file holds the progress', 'p|Tower A|2026-10-17|' in json.loads(entries.read_text())['data']['stamps'])
    settings(a, 'team')
    with a.expect_file_chooser() as fc: a.click('#tmImportEntries')
    fc.value.set_files(str(entries)); a.wait_for_timeout(500); dlg(a, 'Import'); a.wait_for_timeout(300)
    check('planning manager imported the engineer’s entry', ev(a, "JSON.stringify(store.progress['Tower A|2026-10-17'][8])") == '{"a":12.5,"p":0}')

    # ---------------- screen lock
    a.select_option('#tmLock', '5'); a.click('#closeSettingsX'); a.wait_for_timeout(200)
    ev(a, 'lastActivity = Date.now() - 6*60000'); a.wait_for_timeout(11000)
    check('screen locks after inactivity', a.is_visible('#lockForm'))
    shot(a, 'screen-lock.png')
    a.fill('#lockSecret', 'secret12'); a.press('#lockSecret', 'Enter'); a.wait_for_timeout(400)
    check('unlocks with the password', not a.is_visible('#authOverlay'))

    # ---------------- phone
    ph = A.new_page(); watch(ph, 'PHONE'); ph.set_viewport_size({'width': 400, 'height': 860}); ph.goto(URL, wait_until='load'); ph.wait_for_timeout(600)
    if ph.locator('#lockForm').count(): ph.fill('#lockSecret', 'secret12'); ph.press('#lockSecret', 'Enter'); ph.wait_for_timeout(400)
    if ph.is_visible('#authOverlay'): ph.click('.user-tile:has-text("Priya Planner")'); ph.fill('#authSecret', 'secret12'); ph.click('#authGo'); ph.wait_for_timeout(500)
    ph.fill('#dateInput', '2026-10-15'); ph.dispatch_event('#dateInput', 'change'); ph.wait_for_timeout(300)
    ph.select_option('#towerSelect', label='Tower B'); ph.wait_for_timeout(300)
    check('no sideways scrolling on a phone', ph.evaluate('document.documentElement.scrollWidth - document.documentElement.clientWidth') == 0)
    ph.evaluate("document.getElementById('itemTools').scrollIntoView()"); shot(ph, 'phone-progress.png')
    br.close()

failed = [n for n, ok in checks if not ok]
log(f'\n{len(checks) - len(failed)}/{len(checks)} checks passed' + (f' · failed: {failed}' if failed else ''))
log('page errors:', errors or 'none')
sys.exit(1 if failed or errors else 0)
