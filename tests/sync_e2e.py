"""End-to-end test of SharePoint sync, against a stand-in for Microsoft sign-in and SharePoint.

A planning manager connects the demo project to a SharePoint folder and invites an engineer; the
engineer joins with the invite link and signs in with Microsoft; entries, removals and setup changes
travel both ways; then offline use, expired sign-ins, silent renewal, refused access, a shared site
account, a second planning manager's conflicting setup change, and moving a project whose portal file
has its DPR workbook built in onto sync with a full data backup.

  python3 tools/build.py --seed src/seeds/demo.json --out build/portal.html
  python3 tests/sync_e2e.py [build/portal.html]

DPR_SHOTS=<folder> also saves screenshots.
"""
from playwright.sync_api import sync_playwright
import base64, functools, http.server, json, os, pathlib, shutil, subprocess, sys, tempfile, threading, urllib.request

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from mock_microsoft import MockMicrosoft  # noqa: E402

FILE = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else HERE.parent / 'build' / 'portal.html').resolve()
SHOTS = pathlib.Path(os.environ['DPR_SHOTS']) if os.environ.get('DPR_SHOTS') else None
errors, checks = [], []


def log(*a):
    print(*a); sys.stdout.flush()


def check(name, ok, detail=''):
    checks.append((name, bool(ok)))
    log(('PASS ' if ok else 'FAIL ') + name + (f' — {detail}' if detail != '' else ''))


def watch(pg, tag):
    pg.on('pageerror', lambda e: errors.append(f'{tag} pageerror: {e}'))
    pg.on('console', lambda m: errors.append(f'{tag} console: {m.text}') if m.type == 'error'
          and not any(s in m.text for s in ('fonts.g', 'ERR_', 'cdnjs', 'net::', 'Failed to load resource')) else None)
    pg.on('dialog', lambda d: d.accept() if d.type == 'beforeunload' else (errors.append(f'{tag} native dialog: {d.message[:60]}'), d.dismiss()))


def until(pg, js, timeout=20000):
    try:
        pg.wait_for_function(js, timeout=timeout); return True
    except Exception:  # noqa: BLE001
        return False


def dlg(pg, text, timeout=10000):
    pg.wait_for_selector('.dlg-overlay .dlg', timeout=timeout)
    pg.click(f'.dlg-overlay .dlg button:has-text("{text}")'); pg.wait_for_timeout(250)


def dtitle(pg):
    until(pg, "!!document.querySelector('.dlg-overlay .dlg-title')", 8000)
    return pg.inner_text('.dlg-overlay .dlg-title') if pg.locator('.dlg-overlay .dlg-title').count() else None


def ev(pg, js):
    return pg.evaluate(js)


def set_date(pg, d):
    pg.fill('#dateInput', d); pg.dispatch_event('#dateInput', 'change'); pg.wait_for_timeout(300)


def tab(pg, t):
    pg.click(f'.tab[data-tab="{t}"]'); pg.wait_for_timeout(200)


def settings(pg, pane):
    pg.click('#settingsGearBtn'); pg.wait_for_timeout(300); pg.click(f'.set-tabs button[data-pane="{pane}"]'); pg.wait_for_timeout(150)


def sync_now(pg):
    """Runs a sync on the page and returns whether it succeeded (a reload it triggers counts as done)."""
    try:
        return pg.evaluate('syncNow()')
    except Exception:  # noqa: BLE001 - the page reloaded to apply a new setup
        pg.wait_for_load_state('load'); pg.wait_for_timeout(800)
        return None


def settled(pg, timeout=20000):
    return until(pg, "typeof syncRun!=='undefined' && !syncRun && !document.getElementById('syncBusy')", timeout)


def quiet(pg, timeout=25000):
    """Waits until the page has finished syncing and applying a new setup (which reloads it)."""
    for _ in range(3):
        try:
            pg.wait_for_load_state('load')
            if until(pg, "typeof syncRun!=='undefined' && !syncRun && !SYNC_NEEDS_RELOAD && !document.getElementById('syncBusy')", timeout):
                pg.wait_for_timeout(300)
                if pg.evaluate("typeof syncRun!=='undefined' && !syncRun && !SYNC_NEEDS_RELOAD"):
                    return True
        except Exception:  # noqa: BLE001 - reloading
            pg.wait_for_timeout(500)
    return False


def microsoft(pg, user, portal):
    """At the stand-in sign-in page, pick an account and come back to the portal."""
    pg.wait_for_selector(f'a.acct[data-user="{user}"]', timeout=15000)
    pg.click(f'a.acct[data-user="{user}"]')
    pg.wait_for_url(portal + '**', timeout=15000); pg.wait_for_load_state('load')


def shot(pg, name):
    if SHOTS:
        SHOTS.mkdir(parents=True, exist_ok=True); pg.screenshot(path=str(SHOTS / name))


def ctl(mock, what):
    urllib.request.urlopen(urllib.request.Request(mock.url + '/__ctl/' + what, data=b'', method='POST')).read()


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


if not FILE.exists():
    sys.exit(f'{FILE} is missing: build it first (see the docstring).')
site_dir = pathlib.Path(tempfile.mkdtemp())
shutil.copyfile(FILE, site_dir / 'index.html')
site = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Quiet, directory=str(site_dir)))
threading.Thread(target=site.serve_forever, daemon=True).start()
PORTAL = f'http://localhost:{site.server_address[1]}/'
mock = MockMicrosoft().start()
INIT = f'window.__dprEndpoints = {json.dumps(mock.endpoints)};'

with sync_playwright() as p:
    br = p.chromium.launch()

    def context():
        c = br.new_context(viewport={'width': 1300, 'height': 900})
        c.add_init_script(INIT)
        return c

    # ------------------------------------------------------------ planning manager sets up and connects
    A = context(); a = A.new_page(); watch(a, 'PM')
    a.goto(PORTAL, wait_until='load')
    a.click('#wcSetup'); a.fill('#pmName', 'Priya Planner'); a.fill('#pmPw', 'secret12'); a.fill('#pmPw2', 'secret12')
    dlg(a, 'Create account'); dlg(a, 'I’ve saved it')
    check('sync light hidden before connecting', ev(a, "document.getElementById('syncChip').hidden"))
    set_date(a, '2026-10-15'); a.select_option('#towerSelect', label='Tower A'); a.wait_for_timeout(250)
    a.fill('#entryBody .today-input[data-sno="6"]', '42'); a.click('#saveBtn'); a.wait_for_timeout(300)
    settings(a, 'team')
    check('SharePoint section offered to the planning manager', a.is_visible('#spConnect'))
    a.click('#tmAdd'); a.fill('#pfName', 'Ravi Kumar'); a.fill('#pfEmail', 'Ravi@DEMO.test'); a.fill('#pfSecret', '2468')
    dlg(a, 'Add person'); dlg(a, 'OK')
    check('work email kept in lower case', ev(a, "teamUsers().find(u=> u.name==='Ravi Kumar').email") == 'ravi@demo.test')
    a.fill('#spLink', mock.folder_link()); a.fill('#spClient', 'test-client')
    shot(a, 'sync-connect.png')
    a.click('#spConnect')
    microsoft(a, 'pm@demo.test', PORTAL)
    a.wait_for_selector('.dlg-overlay .dlg-title:has-text("Connected to SharePoint")', timeout=30000)
    invite = a.input_value('#ivLink')
    shot(a, 'sync-invite.png')
    dlg(a, 'Done')
    pm_project = mock.file_json('dpr-project.json')
    check('setup sent to SharePoint', pm_project and pm_project['projectId'] == ev(a, 'CFG.projectId') and pm_project['config']['sync']['folderId'])
    files = mock.files()
    check('existing entries sent, one file per month and device', any(n.startswith('entries/2026-10__') for n in files), sorted(files))
    check('a note about the files is left in the folder', 'About these files.txt' in files)
    check('the entries folder exists from the start', 'entries/About this folder.txt' in files)
    check('planning manager’s work email taken from Microsoft', ev(a, 'userById(ME.id).email') == 'pm@demo.test')
    check('sync light shows in step', 'Synced' in a.inner_text('#syncChip'), a.inner_text('#syncChip'))
    check('invite link points at this portal', invite.startswith(PORTAL + '#join='), invite[:60])
    check('connect address in the address bar is cleaned up', '#' not in a.url, a.url)

    # ------------------------------------------------------------ engineer joins with the invite link
    B = context(); b = B.new_page(); watch(b, 'ENG')
    b.goto(invite, wait_until='load')
    b.wait_for_selector('#jnGo')
    check('join screen names the project', 'Riverside' in b.inner_text('#authOverlay'))
    b.click('#jnGo')
    microsoft(b, 'ravi@demo.test', PORTAL)
    joined = until(b, "typeof ME!=='undefined' && ME && ME.name==='Ravi Kumar' && document.getElementById('authOverlay').hidden", 30000)
    check('engineer recognised by work email, no PIN', joined, ev(b, 'ME && ME.name'))
    check('same project on both devices', ev(b, 'CFG.projectId') == ev(a, 'CFG.projectId'))
    check('engineer received the planning manager’s progress', ev(b, "JSON.stringify((store.progress['Tower A|2026-10-15']||{})[6])") == '{"a":42,"p":0}')
    settled(b)
    check('engineer’s device sends nothing it received', not any(n.endswith(ev(b, 'deviceId()') + '.json') for n in mock.files()))

    set_date(b, '2026-10-16'); b.select_option('#towerSelect', label='Tower A'); b.wait_for_timeout(250)
    b.fill('#entryBody .today-input[data-sno="7"]', '15'); b.click('#saveBtn'); b.wait_for_timeout(300)
    check('engineer’s save syncs', sync_now(b) is True)
    dev_b = ev(b, 'deviceId()')
    fb = mock.file_json(f'entries/2026-10__{dev_b}.json')
    check('engineer’s entry is in SharePoint', fb and any(k.startswith('p|Tower A|2026-10-16|') for k in fb['data']['stamps']))
    check('engineer never writes the setup', not any(m == 'PUT' and 'dpr-project.json' in pth and u == 'ravi@demo.test' for m, pth, u in mock.state.log))
    check('planning manager receives it', sync_now(a) is True and ev(a, "JSON.stringify((store.progress['Tower A|2026-10-16']||{})[7])") == '{"a":15,"p":0}')

    # ------------------------------------------------------------ removals travel
    tab(b, 'sitelogs'); b.click('.subtab[data-sub="rain"]'); b.wait_for_timeout(150)
    b.fill('#rainBody tr:first-child .rStart', '14:00'); b.fill('#rainBody tr:first-child .rEnd', '15:30'); b.fill('#rainBody tr:first-child .rAffected', 'Pour delayed')
    b.click('#saveRainBtn'); b.wait_for_timeout(300); sync_now(b)
    sync_now(a)
    check('rain event reaches the planning manager', ev(a, "store.rain.some(r=> r.affected==='Pour delayed')"))
    tab(a, 'sitelogs'); a.click('.subtab[data-sub="rain"]'); a.wait_for_timeout(150)
    a.click('#rainBody tr:has(.rAffected[value="Pour delayed"]) [data-remove-row]'); a.click('#saveRainBtn'); a.wait_for_timeout(300)
    check('removal syncs', sync_now(a) is True)
    sync_now(b)
    check('removal reaches the engineer', ev(b, "!store.rain.some(r=> r.affected==='Pour delayed')"))
    tab(a, 'entry'); tab(b, 'entry')

    # ------------------------------------------------------------ a setup change reaches the engineer
    settings(a, 'project'); a.fill('#cfgName', 'Riverside Residences II')
    a.click('#cfgSaveBtn'); a.wait_for_load_state('load'); a.wait_for_timeout(800)
    settled(a)
    check('new setup in SharePoint', (mock.file_json('dpr-project.json') or {}).get('projectName') == 'Riverside Residences II')
    set_date(b, '2026-10-16'); tab(b, 'labour')
    sync_now(b)
    applied = until(b, "typeof CFG!=='undefined' && CFG.project.name==='Riverside Residences II' && !!document.getElementById('brandLine')", 20000)
    check('engineer’s portal picks up the new setup', applied)
    check('and comes back to the same tab and day', until(b, "document.querySelector('.tab.active').dataset.tab==='labour' && dateInput.value==='2026-10-16'", 8000))

    # ------------------------------------------------------------ offline, then back
    tab(b, 'labour')
    b.fill('#labourBody tr:first-child .contractorInput', 'Alpha Formwork Co.'); b.fill('#labourBody tr:first-child .categoryInput', 'Formwork')
    b.fill('#labourBody tr:first-child .labourCount >> nth=0', '12'); B.set_offline(True)
    b.click('#saveLabourBtn'); b.wait_for_timeout(300)
    check('offline save stays on the device', sync_now(b) is False and 'Offline' in b.inner_text('#syncChip'), b.inner_text('#syncChip'))
    shot(b, 'sync-offline.png')
    B.set_offline(False)
    check('back online it is sent', sync_now(b) is True)
    sync_now(a)
    check('planning manager has the labour', ev(a, "(store.labour['2026-10-16']||[]).some(r=> r.contractor==='Alpha Formwork Co.')"))
    tab(b, 'entry')

    # ------------------------------------------------------------ sign-in renewal
    ctl(mock, 'expire-access')
    check('expired access token is renewed', sync_now(b) is True)
    ctl(mock, 'expire-refresh')
    check('expired sign-in renewed silently', sync_now(b) is True)
    ctl(mock, 'logout?u=ravi%40demo.test'); ctl(mock, 'expire-refresh')
    check('without a Microsoft session it asks to sign in', sync_now(b) is False and 'Sign in' in b.inner_text('#syncChip'), b.inner_text('#syncChip'))
    b.click('#syncChip'); b.wait_for_timeout(200)
    check('sync panel explains', dtitle(b) == 'SharePoint sync')
    dlg(b, 'Sign in with Microsoft')
    microsoft(b, 'ravi@demo.test', PORTAL)
    check('signed in again, syncing resumes', until(b, "typeof syncRun!=='undefined' && !syncRun && syncState().lastOk && !syncState().error", 20000))

    # ------------------------------------------------------------ refused access
    ctl(mock, 'deny?u=ravi%40demo.test&path=DPR/Riverside/entries')
    set_date(b, '2026-10-18'); b.fill('#entryBody .today-input[data-sno="8"]', '3'); b.click('#saveBtn'); b.wait_for_timeout(300)
    check('refused access is shown', sync_now(b) is False and 'No access' in b.inner_text('#syncChip'), b.inner_text('#syncChip'))
    ctl(mock, 'allow?u=ravi%40demo.test')
    ok = sync_now(b)
    check('and clears once access is given', ok is True and 'Synced' in b.inner_text('#syncChip'), f"{ok} · {b.inner_text('#syncChip')} · {ev(b, 'JSON.stringify(syncState().error)')}")

    # ------------------------------------------------------------ a shared site account: name and PIN
    C = context(); c = C.new_page(); watch(c, 'SITE')
    c.goto(invite, wait_until='load'); c.wait_for_selector('#jnGo'); c.click('#jnGo')
    microsoft(c, 'site@demo.test', PORTAL)
    c.wait_for_selector('.user-tile', timeout=30000)
    check('shared account: pick a name', 'site@demo.test' in c.inner_text('#authOverlay'))
    c.click('.user-tile:has-text("Ravi Kumar")'); c.fill('#authSecret', '2468'); c.click('#authGo')
    check('signed in with the PIN', until(c, "ME && ME.name==='Ravi Kumar'", 8000))
    check('and the site device syncs', sync_now(c) is True)

    # ------------------------------------------------------------ two planning managers: the newer setup wins
    D = context(); d = D.new_page(); watch(d, 'PM2')
    d.goto(invite, wait_until='load'); d.wait_for_selector('#jnGo'); d.click('#jnGo')
    microsoft(d, 'pm@demo.test', PORTAL)
    ok = until(d, "typeof ME!=='undefined' && ME && ME.role==='pm'", 30000)
    check('second device for the planning manager', ok)
    quiet(a); quiet(d)
    ev(a, "CFG.project.contractor = 'Demo Constructions (A)'; touchBase();")
    a.wait_for_timeout(30)
    ev(d, "CFG.project.contractor = 'Demo Constructions (D)'; touchBase();")
    sync_now(a)
    check('first change sent', (mock.file_json('dpr-project.json') or {}).get('config', {}).get('project', {}).get('contractor') == 'Demo Constructions (A)')
    sync_now(d); quiet(d)
    check('the later change wins in SharePoint', (mock.file_json('dpr-project.json') or {}).get('config', {}).get('project', {}).get('contractor') == 'Demo Constructions (D)')
    sync_now(a); quiet(a)
    check('and reaches the first device', until(a, "typeof CFG!=='undefined' && CFG.project.contractor==='Demo Constructions (D)'", 15000))
    # an upload against an out-of-date version of the setup: SharePoint refuses it, the newer setup still wins
    res = ev(d, """(async ()=>{ const st = syncState(); st.setupETag = '"{stale},1"';
        CFG.project.employer = 'Riverside Developers (D)'; touchBase(); await syncPush(st, {}); return st.setupETag; })()""")
    check('a refused out-of-date upload is redone', (mock.file_json('dpr-project.json') or {}).get('config', {}).get('project', {}).get('employer') == 'Riverside Developers (D)', res)
    check('SharePoint refused the out-of-date upload first', any(pth.endswith('dpr-project.json') for u, pth in mock.state.refused), mock.state.refused)

    # ------------------------------------------------------------ the Android app passes on dprportal://join links
    E = context(); e = E.new_page(); watch(e, 'APP')
    e.goto(PORTAL, wait_until='load')
    app_link = 'dprportal://join?p=' + invite.split('#join=')[1]
    ev(e, f"window.__dprJoin({json.dumps(app_link)})")
    check('an app invite link opens the join screen', until(e, "!!document.getElementById('jnGo') && document.getElementById('authOverlay').innerText.includes('Riverside')", 5000))
    check('a plain SharePoint folder link is understood too', ev(e, f"JSON.stringify(parseInvite({json.dumps(mock.folder_link())}))") == json.dumps({'link': mock.folder_link()}, separators=(',', ':')))
    E.close()

    # ------------------------------------------------------------ stopping sync reaches everyone
    quiet(a)
    settings(a, 'team'); a.click('#spStop'); dlg(a, 'Stop syncing')
    check('stopped on the planning manager’s device', until(a, "document.getElementById('syncChip').hidden", 5000))
    check('SharePoint knows sync is off', ((mock.file_json('dpr-project.json') or {}).get('config', {}).get('sync') or {}).get('off') is True)
    a.click('#closeSettingsX')
    sync_now(c); quiet(c)
    check('and the other devices stop too', until(c, "typeof syncOn==='function' && !syncOn() && document.getElementById('syncChip').hidden", 15000))

    # ------------------------------------------------------------ phone width
    b.set_viewport_size({'width': 360, 'height': 780}); b.wait_for_timeout(300)
    check('sync light fits a small phone', ev(b, 'document.documentElement.scrollWidth - document.documentElement.clientWidth') == 0)
    shot(b, 'sync-phone.png')

    # ------------------------------------------------------------ moving a project with its built-in workbook onto sync
    # The project's own portal file has its DPR workbook built in (tools/build.py --workbook). The planning manager moves
    # it to the website with a full data backup; the workbook comes along and reaches the engineers through SharePoint.
    wb_file = HERE / 'fixtures' / 'Harbour_View_DPR.xlsx'
    wb_bytes = wb_file.read_bytes()
    made = subprocess.run([sys.executable, str(HERE.parent / 'tools' / 'build.py'), '--seed', str(HERE.parent / 'src' / 'seeds' / 'demo.json'),
                           '--workbook', str(wb_file), '--out', str(site_dir / 'file.html')], capture_output=True, text=True)
    check('a portal file with a built-in workbook', made.returncode == 0, made.stderr[-300:])
    F = context(); f = F.new_page(); watch(f, 'FILE')
    f.goto(PORTAL + 'file.html', wait_until='load')
    f.click('#wcSetup'); f.fill('#pmName', 'Priya Planner'); f.fill('#pmPw', 'secret12'); f.fill('#pmPw2', 'secret12')
    dlg(f, 'Create account'); dlg(f, 'I’ve saved it')
    until(f, "!!(CFG.template && CFG.template.source==='seed')", 10000)
    settings(f, 'data')
    with f.expect_download() as dl:
        f.click('#dataExportBtn')
    backup_path = dl.value.path()
    backup = json.loads(pathlib.Path(backup_path).read_text(encoding='utf-8'))
    check('its full backup carries the built-in workbook', base64.b64decode(backup.get('templateB64') or '') == wb_bytes)

    G = context(); g = G.new_page(); watch(g, 'PM-WEB')
    g.goto(PORTAL, wait_until='load')
    g.click('#wcSetup'); g.fill('#pmName', 'Temporary'); g.fill('#pmPw', 'temp1234'); g.fill('#pmPw2', 'temp1234')
    dlg(g, 'Create account'); dlg(g, 'I’ve saved it')
    settings(g, 'data')
    g.set_input_files('#dataImportFile', backup_path)
    dlg(g, 'Replace everything'); dlg(g, 'OK')
    g.wait_for_load_state('load')
    g.wait_for_selector('.user-tile:has-text("Priya Planner")', timeout=15000)
    g.click('.user-tile:has-text("Priya Planner")'); g.fill('#authSecret', 'secret12'); g.click('#authGo')
    until(g, "typeof ME!=='undefined' && ME && ME.name==='Priya Planner'", 8000)
    check('restored on the website, the workbook is kept in its storage',
          ev(g, 'CFG.template.source') == 'idb' and ev(g, 'loadTemplateBytes().then(b=> b.length)') == len(wb_bytes))
    settings(g, 'project'); g.fill('#cfgName', 'Harbour View Towers')
    g.click('#cfgSaveBtn'); g.wait_for_load_state('load'); g.wait_for_timeout(800)
    settings(g, 'team')
    g.click('#tmAdd'); g.fill('#pfName', 'Ravi Kumar'); g.fill('#pfEmail', 'ravi@demo.test'); g.fill('#pfSecret', '2468')
    dlg(g, 'Add person'); dlg(g, 'OK')
    g.fill('#spLink', mock.folder_link('DPR/Other project')); g.fill('#spClient', 'test-client')
    g.click('#spConnect')
    microsoft(g, 'pm@demo.test', PORTAL)
    g.wait_for_selector('.dlg-overlay .dlg-title:has-text("Connected to SharePoint")', timeout=30000)
    invite2 = g.input_value('#ivLink'); dlg(g, 'Done')
    sent = mock.files('DPR/Other project').get('dpr-workbook.xlsx')
    check('the workbook is sent to SharePoint', bool(sent) and bytes(sent['content']) == wb_bytes)

    H = context(); h = H.new_page(); watch(h, 'ENG-WEB')
    h.goto(invite2, wait_until='load'); h.wait_for_selector('#jnGo')
    check('the join screen names the invited project, not the one on the device so far',
          h.inner_text('#authOverlay .auth-head .sub').strip() == 'Harbour View Towers', h.inner_text('#authOverlay .auth-head .sub'))
    h.click('#jnGo')
    microsoft(h, 'ravi@demo.test', PORTAL)
    until(h, "typeof ME!=='undefined' && ME && ME.name==='Ravi Kumar'", 30000); quiet(h)
    check('and reaches the engineer', ev(h, "loadTemplateBytes().then(b=> b.length).catch(e=> e.message)") == len(wb_bytes))
    ev(h, "TPL_DB.put('template', null)")
    check('a workbook not yet received is explained to the engineer', 'hasn’t reached this device' in ev(h, "loadTemplateBytes().then(()=> 'ok').catch(e=> e.message)"))

    # a workbook file missing from the planning manager's device (say, restored from an older backup) can be chosen again
    ev(g, "TPL_DB.put('template', null)")
    settings(g, 'workbook')
    shown = until(g, "!!document.getElementById('tplAgainBtn')", 8000)
    check('a missing workbook file is pointed out, with a way to choose it again',
          shown and 'Choose the same workbook again' in g.inner_text('#tplSummary'))
    shot(g, 'sync-workbook-missing.png')
    if shown:
        g.click('#tplAgainBtn')
        check('which keeps the project and its entries', until(g, "!!document.getElementById('wzFile') && W.mode==='replace'", 5000))
    br.close()

mock.stop(); site.shutdown()
failed = [n for n, ok in checks if not ok]
log(f'\n{len(checks) - len(failed)}/{len(checks)} checks passed' + (f' · failed: {failed}' if failed else ''))
log('page errors:', errors or 'none')
sys.exit(1 if failed or errors else 0)
