"""Regression run for the portal: sign-in, pour grid, plan editor, periods, wizard, export.
Usage: python3 regress.py <html file>"""
from playwright.sync_api import sync_playwright
import pathlib, sys, openpyxl, datetime
import os as _os, pathlib as _pl, sys as _sys
_HERE = _pl.Path(__file__).resolve().parent
if len(_sys.argv) < 2: _sys.exit('usage: python3 %s <portal built from your project seed>.html  (see tests/README.md)' % _pl.Path(__file__).name)
FILE = str(_pl.Path(_sys.argv[1]).resolve())
SP = str(_pl.Path(_os.environ.get('DPR_TEST_OUT', _HERE.parent / 'output'))); _pl.Path(SP).mkdir(parents=True, exist_ok=True)
FIXTURES = str(_HERE.parent / 'fixtures')
URL = pathlib.Path(FILE).resolve().as_uri()
errors = []
def log(*a): print(*a); sys.stdout.flush()
def dlg(pg, text, timeout=10000):
    pg.wait_for_selector('.dlg-overlay .dlg', timeout=timeout); pg.click(f'.dlg-overlay .dlg button:has-text("{text}")'); pg.wait_for_timeout(250)
def dtitle(pg): return pg.inner_text('.dlg-overlay .dlg-title') if pg.locator('.dlg-overlay .dlg-title').count() else None
def set_date(pg, d): pg.fill('#dateInput', d); pg.dispatch_event('#dateInput','change'); pg.wait_for_timeout(300)
def setup_pm(pg):
    pg.goto(URL, wait_until='load'); pg.wait_for_timeout(600)
    pg.click('#wcSetup'); pg.fill('#pmName','Plan Manager'); pg.fill('#pmPw','secret12'); pg.fill('#pmPw2','secret12'); dlg(pg,'Create account'); pg.wait_for_timeout(300)
    dlg(pg, 'I’ve saved it')
rows=[(1,1,'20-09-2026',True),(1,2,'22-09-2026',True),(2,1,'28-09-2026',True),(2,2,'30-09-2026',False),(3,1,'20-10-2026',True),(3,2,'22-10-2026',True)]
paste="Tower\tLevel\tPour\tPlanned pour date\t13\t28\t34\n"+"\n".join(f"Tower E\tL{l}\tP{p}\t{d}\t120\t15\t{40 if b else ''}" for l,p,d,b in rows)
with sync_playwright() as p:
    br = p.chromium.launch()
    ctx = br.new_context(accept_downloads=True, viewport={'width':1280,'height':900}, permissions=['clipboard-read','clipboard-write'])
    pg = ctx.new_page()
    pg.on('pageerror', lambda e: errors.append('pageerror: '+str(e)))
    pg.on('console', lambda m: errors.append('console: '+m.text) if m.type=='error' and 'fonts.g' not in m.text and 'ERR_' not in m.text else None)
    pg.on('dialog', lambda d: (errors.append('NATIVE: '+d.message[:60]), d.dismiss()))
    setup_pm(pg)
    for t in ['entry','structure','labour','machinery','material','sitelogs','dpr','overview']:
        pg.click(f'.tab[data-tab="{t}"]'); pg.wait_for_timeout(150)
    log('overview pct:', pg.inner_text('#ovBigPct'))
    # pours
    pg.click('#settingsGearBtn'); pg.wait_for_timeout(400); pg.click('.set-tabs button[data-pane="pours"]')
    pg.fill('#pourPaste', paste); pg.click('#pourPreviewBtn'); pg.wait_for_timeout(200); pg.click('#pourApplyBtn')
    pg.wait_for_load_state('load'); pg.wait_for_timeout(900)
    log('signed in after reload:', not pg.is_visible('#authOverlay'), '| pours:', pg.evaluate('CFG.pours.length'))
    pg.click('.tab[data-tab="entry"]'); set_date(pg, '2026-09-22'); pg.select_option('#towerSelect', label='Tower E'); pg.wait_for_timeout(400)
    cell = lambda lid,c: f'#pourGridBody tr[data-lid="{lid}"] td[data-c="{c}"]'
    pg.click(cell('L1|P1',0)); pg.keyboard.type('50'); pg.keyboard.press('Enter'); pg.keyboard.type('130'); pg.keyboard.press('Tab'); pg.keyboard.type('12'); pg.keyboard.press('Enter')
    pg.evaluate("navigator.clipboard.writeText('10\\t2\\t5\\r\\n11\\t3\\t99\\r\\n')"); pg.click(cell('L2|P1',0)); pg.keyboard.press('Control+V'); pg.wait_for_timeout(200)
    log('pour grid unsaved:', pg.evaluate('pgUnsaved()'))
    pg.check('#pourGridBody tr[data-lid="L1|P1"] .pg-cast'); pg.click('#saveBtn'); pg.wait_for_timeout(400)
    log('saved agg 13/28/34:', [pg.evaluate(f"(store.progress['Tower E|2026-09-22'][{s}]||{{}}).a") for s in (13,28,34)], '| cast by:', pg.evaluate("userName(store.pourCast['Tower E|L1|P1'].by)"), '| by-chip:', pg.inner_text('#pourGridBody tr[data-lid="L1|P1"] .by-chip'))
    # plan editor
    pg.click('#editPlanBtn'); pg.wait_for_timeout(400)
    pg.select_option('#planTower', label='Tower D'); pg.wait_for_timeout(300)
    pc = pg.locator('#planGridHolder tbody tr:nth-child(13) td:nth-child(24) .planCell')
    log('plan cell before:', pc.input_value()); pc.fill('99'); pg.click('#planSaveBtn'); pg.wait_for_timeout(300)
    log('plan audit row:', pg.inner_text('#planAuditBody tr:first-child').replace('\t',' | '))
    pg.click('#closePlanX')
    # export
    with pg.expect_download(timeout=30000) as dl: pg.click('#exportBtn')
    xf = SP+'/regress_export.xlsx'; dl.value.save_as(xf)
    dv = openpyxl.load_workbook(xf, data_only=True)['Data']; d = openpyxl.load_workbook(xf)['Data']
    col = {dv.cell(row=6,column=c).value.strftime('%Y-%m-%d'): c for c in range(14,90) if isinstance(dv.cell(row=6,column=c).value, datetime.datetime)}
    c22 = col['2026-09-22']
    log('export Tower E item13 Sep22 A:', d.cell(row=59,column=c22+1).value, '| Tower D item13 Sep22 P:', d.cell(row=97,column=c22).value)
    pg.wait_for_timeout(300)
    if pg.locator('.dlg-overlay').count(): dlg(pg,'OK')
    # periods
    pg.click('#settingsGearBtn'); pg.wait_for_timeout(300); pg.click('.set-tabs button[data-pane="workbook"]'); pg.wait_for_timeout(1500)
    pg.click('#perClose'); pg.wait_for_timeout(250); log('close dialog:', dtitle(pg)); dlg(pg,'Close period'); pg.wait_for_timeout(500)
    log('badge closed:', pg.inner_text('#periodBadge').replace('\n',' '))
    pg.click('#perReopen'); pg.wait_for_timeout(200); dlg(pg,'Reopen period'); log('reason required:', pg.inner_text('.dlg-err'))
    pg.fill('#dlgInput0','Late entries'); dlg(pg,'Reopen period'); pg.wait_for_timeout(400)
    log('period log top:', pg.inner_text('#periodPanel tbody tr:first-child').replace('\t',' | '))
    pg.click('#perClose'); pg.wait_for_timeout(200); dlg(pg,'Close period'); pg.wait_for_timeout(400)
    pg.click('#perRoll'); pg.wait_for_timeout(200); dlg(pg,'Roll over')
    pg.wait_for_selector('.dlg-title:has-text("Rolled over")', timeout=40000); dlg(pg,'OK'); pg.wait_for_load_state('load'); pg.wait_for_timeout(900)
    log('after rollover: signed in:', not pg.is_visible('#authOverlay'), '| badge:', pg.inner_text('#periodBadge').replace('\n',' '))
    # wizard: new project from the Harbour View workbook
    pg.click('#settingsGearBtn'); pg.wait_for_timeout(300); pg.click('.set-tabs button[data-pane="workbook"]'); pg.wait_for_timeout(300)
    pg.click('#openWizardBtn'); pg.wait_for_timeout(200)
    pg.set_input_files('#wzFile', FIXTURES+'/Harbour_View_DPR.xlsx'); pg.wait_for_timeout(1500)
    log('wizard preview:', pg.inner_text('#wzPreview').split('\n')[0])
    pg.fill('#wzContractor','ACME Builders'); pg.click('#wzImport'); pg.wait_for_timeout(300); dlg(pg,'Set up project')
    pg.wait_for_load_state('load'); pg.wait_for_timeout(1000)
    log('new project: signed in:', not pg.is_visible('#authOverlay'), '| brand:', pg.inner_text('#brandLine'), '| towers:', pg.evaluate('CFG.towers'), '| team kept:', pg.evaluate('CFG.team.users.length'))
    pg.click('.tab[data-tab="entry"]'); set_date(pg,'2026-11-10'); pg.select_option('#towerSelect', label='Block 1'); pg.wait_for_timeout(300)
    pg.fill('#entryBody tr[data-sno="4"] .today-input','33'); pg.click('#saveBtn'); pg.wait_for_timeout(300)
    with pg.expect_download(timeout=30000) as dl: pg.click('#exportBtn')
    hf = SP+'/regress_harbour.xlsx'; dl.value.save_as(hf)
    ws = openpyxl.load_workbook(hf)['Site Progress']
    rcc = [r for r in range(11,22) if ws.cell(row=r,column=2).value=='RCC M40' and ws.cell(row=r,column=7).value=='Block 1'][0]
    c10 = [c for c in range(8,38) if ws.cell(row=4,column=c).value==datetime.datetime(2026,11,10)][0]
    log('harbour export RCC Block1 Nov10:', ws.cell(row=rcc,column=c10).value)
    ph = ctx.new_page(); ph.set_viewport_size({'width':400,'height':860}); ph.goto(URL, wait_until='load'); ph.wait_for_timeout(700)
    log('phone overflow:', ph.evaluate('document.documentElement.scrollWidth - document.documentElement.clientWidth'))
    log('ERRORS:', errors)
    br.close()
