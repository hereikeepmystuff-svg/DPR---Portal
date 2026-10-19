"""Checks android/prepare_assets.py without a network connection.

A stand-in for the network serves a stylesheet shaped like Google Fonts' (several subsets, variable
fonts that serve every weight from one file) and a SheetJS file. The packed page must then use only
local copies, download each font file once, and load the app bridge. With no network at all the
page must keep working from the online copies, and --strict must stop the build instead.

  python3 tools/build.py --seed src/seeds/demo.json --out build/portal.html
  python3 tests/android_assets.py
"""
import importlib.util, pathlib, re, shutil, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
PORTAL = ROOT / 'build' / 'portal.html'
if not PORTAL.exists():
    sys.exit(f'{PORTAL} is missing: build the portal first (see the docstring).')
spec = importlib.util.spec_from_file_location('prepare_assets', ROOT / 'android' / 'prepare_assets.py')
pa = importlib.util.module_from_spec(spec); spec.loader.exec_module(pa)
pa.IN_CI = False   # the offline cases below warn on purpose; keep that out of CI annotations
checks = []


def check(name, ok, detail=''):
    checks.append((name, bool(ok)))
    print(('PASS ' if ok else 'FAIL ') + name + (f' — {detail}' if detail != '' else ''))


def face(fam, weight, subset, url):
    return (f"/* {subset} */\n@font-face {{\n  font-family: '{fam}';\n  font-style: normal;\n  font-weight: {weight};\n"
            f"  font-display: swap;\n  src: url({url}) format('woff2');\n  unicode-range: U+0000-00FF;\n}}\n")


CSS = ''
for subset in ['cyrillic-ext', 'vietnamese', 'latin-ext', 'latin']:
    for w in (400, 500):
        CSS += face('DM Mono', w, subset, f'https://fonts.gstatic.com/s/dmmono/v14/{w}-{subset}.woff2')
    for w in (400, 600, 700, 800):
        CSS += face('Nunito Sans', w, subset, f'https://fonts.gstatic.com/s/nunitosans/v15/var-{subset}.woff2')
    for w in (800, 900):
        CSS += face('Nunito', w, subset, f'https://fonts.gstatic.com/s/nunito/v26/var-{subset}.woff2')


def run(fetch, *extra):
    calls = []
    def logged(url):
        calls.append(url)
        return fetch(url)
    pa.fetch = logged
    out = pathlib.Path(tempfile.mkdtemp()) / 'www'
    sys.argv = ['prepare_assets.py', str(PORTAL), str(out), *extra]
    try:
        pa.main()
        code = 0
    except SystemExit as e:
        code = e.code or 0
    return out, calls, code


def online(url):
    if 'fonts.googleapis.com' in url:
        assert '&amp;' not in url, 'the stylesheet address still has &amp; in it'
        return CSS.encode()
    if 'cdnjs' in url:
        return b'/* sheetjs */' + b'x' * 200_000
    return b'wOF2' + url.encode()


def offline(url):
    raise OSError('no network')


# 1. with a network: everything local
out, calls, code = run(online, '--strict')
html = (out / 'index.html').read_text(encoding='utf-8')
fonts = sorted(p.name for p in (out / 'fonts').iterdir())
fcss = (out / 'fonts' / 'fonts.css').read_text(encoding='utf-8')
check('online: builds', code == 0)
check('online: 8 font files for latin and latin-ext, plus fonts.css', len(fonts) == 9, fonts)
check('online: each font file downloaded once', sum('gstatic' in c for c in calls) == 8)
check('online: 16 font faces kept', fcss.count('@font-face') == 16)
check('online: the font stylesheet points at local files only', 'https://' not in fcss
      and all((out / 'fonts' / n).exists() for n in re.findall(r'url\(([^)]+)\)', fcss)))
check('online: the page loads its fonts locally', '<link href="fonts/fonts.css" rel="stylesheet">' in html
      and 'fonts.googleapis' not in html and 'fonts.gstatic' not in html)
check('online: the page loads SheetJS locally', '<script src="vendor/xlsx.full.min.js"></script>' in html
      and '<script src="https://cdnjs' not in html and (out / 'vendor' / 'xlsx.full.min.js').exists())
check('online: the bridge is loaded once, at the end of the page', html.count('<script src="app-bridge.js"></script>') == 1
      and html.rindex('app-bridge.js') < html.rindex('</body>') and (out / 'app-bridge.js').exists())
shutil.rmtree(out.parent, ignore_errors=True)

# 2. without a network: the online copies stay, the app still gets the bridge
out, calls, code = run(offline)
html = (out / 'index.html').read_text(encoding='utf-8')
check('offline: builds with warnings', code == 0)
check('offline: keeps the online fonts and SheetJS', 'https://fonts.googleapis.com/css2' in html
      and '<script src="https://cdnjs' in html and not (out / 'fonts').exists())
check('offline: the bridge is still loaded', '<script src="app-bridge.js"></script>' in html)
shutil.rmtree(out.parent, ignore_errors=True)

# 3. without a network, --strict: the build stops
out, calls, code = run(offline, '--strict')
check('offline --strict: stops with an error', code not in (0, None), code)
shutil.rmtree(out.parent, ignore_errors=True)

failed = [n for n, ok in checks if not ok]
print(f'\n{len(checks) - len(failed)}/{len(checks)} checks passed' + (f' · failed: {failed}' if failed else ''))
sys.exit(1 if failed else 0)
