#!/usr/bin/env python3
"""Pack a portal file into the Android app's assets, ready to work offline.

  python3 tools/build.py --seed src/seeds/demo.json --out build/portal.html
  python3 android/prepare_assets.py build/portal.html android/app/src/main/assets/www

What it does to the copy that goes into the app (the portal file itself is left as it is):
  - downloads the SheetJS library the summary export uses and points the page at the local copy;
  - downloads the portal's web fonts (Latin subsets) and points the page at the local copies;
  - adds android/bridge.js, which connects the page to the app (saving files, printing, back button,
    opening setup and entries files, touch and screen-size tuning).

Without internet access the downloads are skipped with a warning: the app still works, using the
phone's own fonts, and the summary export needs a connection. --strict turns that into an error.
"""
import argparse, hashlib, os, pathlib, re, shutil, sys, urllib.request

HERE = pathlib.Path(__file__).resolve().parent
UA = ('Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) '
      'Chrome/126.0.0.0 Mobile Safari/537.36')   # a current browser, so Google Fonts serves woff2
KEEP_SUBSETS = ('latin', 'latin-ext')
IN_CI = os.environ.get('GITHUB_ACTIONS') == 'true'


def fetch(url):
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def warn(msg, strict):
    if strict:
        sys.exit('error: ' + msg)
    print(('::warning::' if IN_CI else 'warning: ') + msg)


def bundle_sheetjs(html, out, strict):
    m = re.search(r'<script src="(https://cdnjs\.cloudflare\.com/ajax/libs/xlsx/[^"]+)"></script>', html)
    if not m:
        return html, 'not referenced'
    try:
        js = fetch(m.group(1))
        if len(js) < 100_000:
            raise ValueError('unexpectedly small download')
    except Exception as e:  # noqa: BLE001 - any failure leaves the online copy in place
        warn(f'SheetJS not bundled ({e}); the summary export will need a connection', strict)
        return html, 'online'
    (out / 'vendor').mkdir(parents=True, exist_ok=True)
    (out / 'vendor' / 'xlsx.full.min.js').write_bytes(js)
    return html.replace(m.group(0), '<script src="vendor/xlsx.full.min.js"></script>'), f'bundled ({len(js) // 1024} KB)'


def bundle_fonts(html, out, strict):
    m = re.search(r'<link href="(https://fonts\.googleapis\.com/css2\?[^"]+)" rel="stylesheet">', html)
    if not m:
        return html, 'not referenced'
    try:
        css = fetch(m.group(1).replace('&amp;', '&')).decode('utf-8')
        blocks = re.findall(r'/\*\s*([\w-]+)\s*\*/\s*(@font-face\s*\{[^}]*\})', css)
        kept, names = [], {}   # names: font file address -> local file name
        (out / 'fonts').mkdir(parents=True, exist_ok=True)
        for subset, block in blocks:
            if subset not in KEEP_SUBSETS:
                continue
            url = re.search(r'url\(\s*[\'"]?(https://[^)\'"\s]+)', block).group(1)
            if url not in names:   # variable fonts serve every weight from one file
                fam = re.search(r'font-family:\s*[\'"]?([^;\'"]+)', block).group(1)
                names[url] = (f"{re.sub(r'[^A-Za-z0-9]+', '', fam)}-{subset}-"
                              f"{hashlib.sha1(url.encode()).hexdigest()[:8]}.woff2")
                (out / 'fonts' / names[url]).write_bytes(fetch(url))
            kept.append(f'/* {subset} */\n' + block.replace(url, names[url]))
        if not names:
            raise ValueError('no font files in the stylesheet')
        (out / 'fonts' / 'fonts.css').write_text('\n'.join(kept) + '\n', encoding='utf-8')
    except Exception as e:  # noqa: BLE001
        shutil.rmtree(out / 'fonts', ignore_errors=True)
        warn(f'fonts not bundled ({e}); the app will use the phone\'s fonts when offline', strict)
        return html, 'online'
    html = html.replace(m.group(0), '<link href="fonts/fonts.css" rel="stylesheet">')
    html = re.sub(r'<link rel="preconnect" href="https://fonts\.(googleapis|gstatic)\.com"[^>]*>\n?', '', html)
    return html, f'bundled ({len(names)} files)'


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('portal', help='a portal file built with tools/build.py')
    ap.add_argument('out', help='the app\'s web folder, normally android/app/src/main/assets/www')
    ap.add_argument('--strict', action='store_true', help='fail instead of warning when a download fails')
    a = ap.parse_args()

    out = pathlib.Path(a.out)
    if out.name != 'www':
        sys.exit('The output folder must be called "www" (it is emptied first).')
    shutil.rmtree(out, ignore_errors=True)
    out.mkdir(parents=True)

    html = pathlib.Path(a.portal).read_text(encoding='utf-8')
    html, sheetjs = bundle_sheetjs(html, out, a.strict)
    html, fonts = bundle_fonts(html, out, a.strict)

    shutil.copyfile(HERE / 'bridge.js', out / 'app-bridge.js')
    cut = html.rindex('</body>')
    html = html[:cut] + '<script src="app-bridge.js"></script>\n' + html[cut:]
    (out / 'index.html').write_text(html, encoding='utf-8')

    version = re.search(r"const APP_VERSION = '([^']+)'", html)
    line = (f'portal v{version.group(1) if version else "?"} · Excel library {sheetjs} · '
            f'fonts {fonts} · bridge added')
    print(f'app assets in {out}: {line}')
    if os.environ.get('GITHUB_STEP_SUMMARY'):   # shown on the workflow run's page
        with open(os.environ['GITHUB_STEP_SUMMARY'], 'a', encoding='utf-8') as s:
            s.write(f'**App web assets:** {line}\n\n')


if __name__ == '__main__':
    main()
