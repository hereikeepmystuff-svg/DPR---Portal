from playwright.sync_api import sync_playwright
import pathlib, sys
import os as _os, pathlib as _pl, sys as _sys
_HERE = _pl.Path(__file__).resolve().parent
if len(_sys.argv) < 2: _sys.exit('usage: python3 %s <portal built from your project seed>.html  (see tests/README.md)' % _pl.Path(__file__).name)
FILE = str(_pl.Path(_sys.argv[1]).resolve())
SP = str(_pl.Path(_os.environ.get('DPR_TEST_OUT', _HERE.parent / 'output'))); _pl.Path(SP).mkdir(parents=True, exist_ok=True)
FIXTURES = str(_HERE.parent / 'fixtures')
URL = pathlib.Path(FILE).resolve().as_uri()
errs=[]
def dlg(pg, text):
    pg.wait_for_selector('.dlg-overlay .dlg', timeout=8000); pg.click(f'.dlg-overlay .dlg button:has-text("{text}")'); pg.wait_for_timeout(250)
def set_date(pg, d): pg.fill('#dateInput', d); pg.dispatch_event('#dateInput','change'); pg.wait_for_timeout(350)
def chips(pg): return [c.replace('\n',' ') for c in pg.locator('#dayCheck .dchip').all_inner_texts()]
with sync_playwright() as p:
    br = p.chromium.launch()
    ctx = br.new_context(viewport={'width':1300,'height':900})
    a = ctx.new_page(); a.on('pageerror', lambda e: errs.append(str(e))); a.on('dialog', lambda d: d.accept())
    a.goto(URL, wait_until='load'); a.wait_for_timeout(600)
    a.click('#wcSetup'); a.fill('#pmName','Plan Manager'); a.fill('#pmPw','secret12'); a.fill('#pmPw2','secret12'); dlg(a,'Create account'); a.wait_for_timeout(300); dlg(a,'I’ve saved it')
    # plan: Tower E, Oct 2026, item rows 13 and 14 on day 20
    a.click('#editPlanBtn'); a.wait_for_timeout(400)
    a.select_option('#planTower', label='Tower E'); a.fill('#planMonth', '2026-10'); a.dispatch_event('#planMonth','change'); a.wait_for_timeout(300)
    a.locator('#planGridHolder tbody tr:nth-child(13) td:nth-child(22) .planCell').fill('40')
    a.locator('#planGridHolder tbody tr:nth-child(14) td:nth-child(22) .planCell').fill('5')
    a.click('#planSaveBtn'); a.wait_for_timeout(300); a.click('#closePlanX'); a.wait_for_timeout(200)
    set_date(a, '2026-10-20'); a.select_option('#towerSelect', label='Tower E'); a.wait_for_timeout(400)
    print('pills:', [x.replace('\n',' ') for x in a.locator('#itemFilter button').all_inner_texts()], '| active:', a.get_attribute('#itemFilter button.active','data-f'), '| info:', a.inner_text('#itemFilterInfo'))
    print('visible snos:', a.evaluate("[...entryBody.querySelectorAll('tr[data-sno]')].filter(t=>!t.hidden).map(t=>t.dataset.sno+':'+t.querySelector('.c-plan').textContent.trim()).join(' ')"))
    # ten times the plan check
    a.fill('#entryBody .today-input[data-sno="14"]', '60'); a.click('#saveBtn'); a.wait_for_timeout(300)
    print('plan x10 dialog:', a.inner_text('.dlg-overlay .dlg-msg').replace('\n',' / ')[:160] if a.locator('.dlg-overlay').count() else None); dlg(a,'Save anyway')
    # focus kept after Ctrl+S
    a.click('#entryBody .today-input[data-sno="13"]'); a.keyboard.type('12'); a.keyboard.press('Control+s'); a.wait_for_timeout(400)
    print('focus after save:', a.evaluate("document.activeElement.dataset.sno"), '| saved:', a.evaluate("JSON.stringify(store.progress['Tower E|2026-10-20'])"))
    # / jumps to search
    a.click('h1'); a.keyboard.press('/'); a.wait_for_timeout(100)
    print('slash focus:', a.evaluate("document.activeElement.id"))
    a.keyboard.type('m40'); a.wait_for_timeout(100); a.keyboard.press('Enter'); a.wait_for_timeout(100)
    print('search m40 -> focus sno:', a.evaluate("document.activeElement.dataset.sno"), '| info:', a.inner_text('#itemFilterInfo'))
    # add engineer progress-only + viewer
    a.click('#settingsGearBtn'); a.wait_for_timeout(300)
    a.click('#tmAdd'); a.fill('#pfName','Asha Progress'); a.check('.pfZone[value="Tower F"]'); a.uncheck('#pfSite'); a.fill('#pfSecret','2468'); dlg(a,'Add person'); dlg(a,'OK')
    a.click('#closeSettingsX')
    a.click('#userChip'); a.click('#userMenu button:has-text("Switch user")'); a.wait_for_timeout(300)
    a.click('.user-tile:has-text("Asha Progress")'); a.fill('#authSecret','2468'); a.click('#authGo'); a.wait_for_timeout(500)
    print('engineer chips:', chips(a), '| tower:', a.input_value('#towerSelect'))
    print('engineer fab/copy hidden:', not a.is_visible('#copyLabourBtn'))
    a.click('#userChip'); a.click('#userMenu button:has-text("Sign out")'); a.wait_for_timeout(300)
    a.click('#authView'); a.wait_for_timeout(400)
    print('viewer chips:', chips(a))
    a.click('.tab[data-tab="labour"]'); a.wait_for_timeout(200)
    print('viewer labour note link:', a.locator('#labourCopyLink').count(), '| ctrl+s:'); a.keyboard.press('Control+s'); a.wait_for_timeout(300)
    print('   dialog:', a.inner_text('.dlg-overlay .dlg-title') if a.locator('.dlg-overlay').count() else None)
    print('errors', errs)
    br.close()
