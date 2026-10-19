"""Checks the web side of the Android app: android/bridge.js inside the packed portal.

Runs the app's index.html (made by android/prepare_assets.py) in Chromium with a stand-in for the
native DPRAndroid object, then checks saving files, printing, the back button, the lock screen,
opening setup and entries files from other apps, and the layout at phone, tablet and landscape sizes.

  python3 tools/build.py --seed src/seeds/demo.json --out build/portal.html
  python3 android/prepare_assets.py build/portal.html android/app/src/main/assets/www
  python3 tests/android_bridge.py

DPR_SHOTS=<folder> also saves screenshots of the app at those sizes.
"""
from playwright.sync_api import sync_playwright
import base64, functools, http.server, json, mimetypes, os, pathlib, sys, threading

HERE = pathlib.Path(__file__).resolve().parent
APP = HERE.parent / 'android' / 'app' / 'src' / 'main' / 'assets' / 'www' / 'index.html'
SHOTS = pathlib.Path(os.environ['DPR_SHOTS']) if os.environ.get('DPR_SHOTS') else None
PHONE = dict(viewport={'width': 412, 'height': 915}, has_touch=True, is_mobile=True, device_scale_factor=2)
STUB = """
window.__calls = [];
window.DPRAndroid = {
  saveFile: function(name, b64, mime){ window.__calls.push({k:'save', name:name, mime:mime, b64:b64}); return 'saved'; },
  print: function(title){ window.__calls.push({k:'print', title:title}); },
  toast: function(msg){ window.__calls.push({k:'toast', msg:msg}); },
  version: function(){ return 'test'; }
};
"""
errors, checks = [], []


def log(*a):
    print(*a); sys.stdout.flush()


def check(name, ok, detail=''):
    checks.append((name, bool(ok)))
    log(('PASS ' if ok else 'FAIL ') + name + (f' — {detail}' if detail != '' else ''))


def watch(pg, tag):
    pg.on('pageerror', lambda e: errors.append(f'{tag} pageerror: {e}'))
    # the stand-in network has no fonts or SheetJS: those console errors are expected here
    pg.on('console', lambda m: errors.append(f'{tag} console: {m.text}') if m.type == 'error'
          and not any(s in m.text for s in ('fonts.g', 'ERR_', 'cdnjs', 'net::')) else None)
    pg.on('dialog', lambda d: d.accept() if d.type == 'beforeunload'
          else (errors.append(f'{tag} native dialog: {d.message[:60]}'), d.dismiss()))


def until(pg, js, timeout=15000):
    """Wait until the expression is true in the page; False if it never is."""
    try:
        pg.wait_for_function(js, timeout=timeout)
        return True
    except Exception:  # noqa: BLE001 - a timeout is reported as a failed check
        return False


def dlg(pg, text):
    pg.click(f'.dlg-overlay .dlg button:has-text("{text}")'); pg.wait_for_timeout(200)


def dtitle(pg, wait=True):
    if wait:
        until(pg, "!!document.querySelector('.dlg-overlay .dlg-title')", 10000)
    return pg.inner_text('.dlg-overlay .dlg-title') if pg.locator('.dlg-overlay .dlg-title').count() else None


def calls(pg, kind):
    return [c for c in pg.evaluate('window.__calls') if c['k'] == kind]


def back(pg):
    return pg.evaluate('window.__dprBack()')


def open_file(pg, name, b64):
    pg.evaluate(f'window.__dprOpenFile({json.dumps(name)}, {json.dumps(b64)})')


def b64json(obj):
    return base64.b64encode(json.dumps(obj).encode()).decode()


def overflow(pg):
    return pg.evaluate('document.documentElement.scrollWidth - document.documentElement.clientWidth')


def shot(pg, name):
    if SHOTS:
        SHOTS.mkdir(parents=True, exist_ok=True); pg.screenshot(path=str(SHOTS / name))


if not APP.exists():
    sys.exit(f'{APP} is missing: run android/prepare_assets.py first (see the docstring).')


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


# The app serves its folder from one web address (WebViewAssetLoader); so does this test.
mimetypes.add_type('font/woff2', '.woff2')
server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Quiet, directory=str(APP.parent)))
threading.Thread(target=server.serve_forever, daemon=True).start()
URL = f'http://127.0.0.1:{server.server_address[1]}/index.html'

with sync_playwright() as p:
    br = p.chromium.launch()
    ctx = br.new_context(**PHONE)
    ctx.add_init_script(STUB)
    a = ctx.new_page(); watch(a, 'PM')
    a.goto(URL, wait_until="load")
    check('bridge active in the app', until(a, "document.documentElement.classList.contains('in-app') && !!document.getElementById('appStyle')"))
    until(a, "!!document.getElementById('wcSetup')")
    a.click('#wcSetup'); a.fill('#pmName', 'Priya Planner'); a.fill('#pmPw', 'secret12'); a.fill('#pmPw2', 'secret12')
    dlg(a, 'Create account')
    dlg(a, 'I’ve saved it')
    until(a, "document.getElementById('authOverlay').hidden && !document.querySelector('.dlg-overlay')")
    shot(a, 'android-phone.png')

    # saving a file hands it to the phone, and the portal carries on as after a download
    a.click('#settingsGearBtn'); a.click('.set-tabs button[data-pane="team"]')
    a.click('#tmExportSetup')
    until(a, "window.__calls.some(c => c.k === 'save')")
    saved = calls(a, 'save')
    check('setup file handed to the phone', len(saved) == 1 and saved[0]['name'].endswith('.json')
          and saved[0]['mime'] == 'application/json', saved and saved[0]['name'])
    setup_b64 = saved[0]['b64'] if saved else ''
    check('the saved file is the setup file', json.loads(base64.b64decode(setup_b64) or b'{}').get('kind') == 'dpr-setup')
    check('portal confirms the save', dtitle(a) == 'Setup file saved', dtitle(a, False)); dlg(a, 'OK')

    # the back button: dialogs, menus and settings first, then Progress, then the top, then leave
    check('back closes settings', back(a) == 'handled' and a.evaluate("document.getElementById('settingsOverlay').style.display") == 'none')
    a.click('#versionBtn'); until(a, "!!document.querySelector('.dlg-overlay')")
    check('back closes a dialog', back(a) == 'handled' and until(a, "!document.querySelector('.dlg-overlay')", 3000))
    a.click('#userChip'); until(a, "!!document.getElementById('userMenu')")
    check('back closes the user menu', back(a) == 'handled' and a.locator('#userMenu').count() == 0)
    a.click('.tab[data-tab="overview"]')
    check('back returns to Progress', back(a) == 'handled' and a.evaluate("document.querySelector('.tab.active').dataset.tab") == 'entry')
    a.evaluate('window.scrollTo(0, 1500)')
    check('back scrolls to the top first', a.evaluate('window.scrollY') > 200 and back(a) == 'handled')
    until(a, 'window.scrollY < 50', 5000)
    check('back then leaves the app', back(a) == 'exit')

    # the lock screen sits above everything: back leaves, a file waits for the unlock
    a.evaluate('lockScreen()')
    check('back on the lock screen leaves the app', a.locator('#authOverlay.lock').count() == 1 and back(a) == 'exit')
    open_file(a, 'demo_setup.json', setup_b64)
    until(a, "window.__calls.some(c => c.k === 'toast')", 3000)
    toasts = calls(a, 'toast')
    check('a file opened while locked asks to unlock first', len(toasts) == 1 and a.locator('.dlg-overlay').count() == 0, toasts and toasts[0]['msg'])
    a.fill('#lockSecret', 'secret12'); a.click('#lockForm button[type=submit]')
    check('unlocks again', until(a, "document.getElementById('authOverlay').hidden"))

    # an entries file from an engineer, opened by the planning manager
    pid = a.evaluate('CFG.projectId')
    open_file(a, 'entries_ravi.json', b64json({'kind': 'dpr-entries', 'format': 1, 'projectId': pid, 'projectName': 'Riverside',
                                               'from': {'id': 'u-x', 'name': 'Ravi', 'role': 'engineer'}, 'exportedAt': '2026-10-20T10:00:00Z',
                                               'range': {'from': '2026-10-20', 'to': '2026-10-20'}, 'data': {}}))
    check('an entries file opens the import for a planning manager', dtitle(a) == 'Import these entries?', dtitle(a, False)); dlg(a, 'Cancel')
    check('a file that is not the portal\'s is turned away', (open_file(a, 'notes.json', b64json({'hello': 1})) or dtitle(a)) == 'Can’t open this file', dtitle(a, False)); dlg(a, 'OK')
    check('a full backup points to Settings, Data', (open_file(a, 'backup.json', b64json({'config': {'items': []}, 'progress': {}})) or dtitle(a)) == 'Data backup', dtitle(a, False)); dlg(a, 'OK')

    # printing goes to Android's print service
    a.click('.tab[data-tab="dpr"]')
    a.click('#printDprBtn')
    prints = calls(a, 'print')
    check('print goes to Android printing', len(prints) == 1 and 'DPR' in prints[0]['title'], prints and prints[0]['title'])
    a.click('.tab[data-tab="entry"]')

    # a new phone: an entries file is explained, then the setup file joins the project
    ctx2 = br.new_context(**PHONE)
    ctx2.add_init_script(STUB)
    e = ctx2.new_page(); watch(e, 'ENG')
    e.goto(URL, wait_until="load"); until(e, "!!document.getElementById('wcSetup')")
    open_file(e, 'entries.json', b64json({'kind': 'dpr-entries', 'format': 1, 'projectId': 'x', 'data': {}}))
    check('an entries file needs a planning manager', dtitle(e) == 'Entries file', dtitle(e, False)); dlg(e, 'OK')
    open_file(e, 'demo_setup.json', setup_b64)
    check('a setup file opened from another app joins the project', dtitle(e) == 'Project ready', dtitle(e, False))
    dlg(e, 'OK')
    check('sign-in then shows the team', until(e, "!!document.querySelector('#authOverlay .user-tile') && document.getElementById('authOverlay').innerText.includes('Priya Planner')"))
    ctx2.close()

    # every screen size: nothing scrolls sideways, on any tab or in settings
    for w, h, name in [(360, 780, 'small phone'), (412, 915, 'phone'), (780, 360, 'phone sideways'),
                       (800, 1280, 'tablet'), (1280, 800, 'tablet sideways')]:
        a.set_viewport_size({'width': w, 'height': h}); a.wait_for_timeout(200)
        worst, where = 0, ''
        for t in ['entry', 'structure', 'labour', 'machinery', 'material', 'sitelogs', 'dpr', 'overview']:
            if not a.locator(f'.tab[data-tab="{t}"]').count():
                continue
            a.click(f'.tab[data-tab="{t}"]'); a.wait_for_timeout(120)
            if overflow(a) > worst: worst, where = overflow(a), t
        a.click('.tab[data-tab="entry"]')
        a.click('#settingsGearBtn'); a.wait_for_timeout(200)
        for pane in ['project', 'lists', 'pours', 'team', 'workbook', 'data']:
            a.click(f'.set-tabs button[data-pane="{pane}"]'); a.wait_for_timeout(80)
            if overflow(a) > worst: worst, where = overflow(a), 'settings/' + pane
        if name == 'small phone': shot(a, 'android-settings-small.png')
        back(a); a.wait_for_timeout(150)
        check(f'{name} {w}x{h}: nothing scrolls sideways', worst == 0, f'{worst}px on {where}' if worst else '')
        if name in ('phone sideways', 'tablet'): shot(a, f"android-{name.replace(' ', '-')}.png")
    br.close()
server.shutdown()

failed = [n for n, ok in checks if not ok]
log(f'\n{len(checks) - len(failed)}/{len(checks)} checks passed' + (f' · failed: {failed}' if failed else ''))
log('page errors:', errors or 'none')
sys.exit(1 if failed or errors else 0)
