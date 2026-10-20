#!/usr/bin/env python3
"""Pack a portal file into the Android app's assets, or for a web host, ready to work offline.

  python3 tools/build.py --seed src/seeds/demo.json --out build/portal.html
  python3 android/prepare_assets.py build/portal.html android/app/src/main/assets/www
  python3 android/prepare_assets.py build/portal.html build/site --web      # for GitHub Pages

What it does to the copy that goes into the app (the portal file itself is left as it is):
  - downloads the SheetJS library the summary export uses and points the page at the local copy;
  - downloads the portal's web fonts (Latin subsets) and points the page at the local copies;
  - for the app, adds android/bridge.js, which connects the page to the app (saving files, printing,
    back button, opening setup and entries files, touch and screen-size tuning);
  - for the web (--web), adds a service worker that keeps the portal working offline once opened, and
    an install manifest, so it can be added to a phone's home screen or a computer's apps.

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


WEB_ICON = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 108 108">
<rect width="108" height="108" rx="24" fill="#E8EDF4"/>
<path fill="#A9C0FF" d="M46.5,32.75 L61.5,32.75 A5,5 0 0,1 61.5,42.75 L46.5,42.75 A5,5 0 0,1 46.5,32.75 Z"/>
<path fill="#5C86F8" d="M39,49 L69,49 A5,5 0 0,1 69,59 L39,59 A5,5 0 0,1 39,49 Z"/>
<path fill="#2C56E0" d="M31.5,65.25 L76.5,65.25 A5,5 0 0,1 76.5,75.25 L31.5,75.25 A5,5 0 0,1 31.5,65.25 Z"/>
</svg>
"""

SERVICE_WORKER = """/* DPR Portal: keeps the portal working offline once it has been opened here.
   Microsoft sign-in and SharePoint are on other addresses and always go to the network. */
const CACHE = 'dpr-portal-@@BUILD@@';
const SHELL = @@SHELL@@;
self.addEventListener('install', e=>{ e.waitUntil(caches.open(CACHE).then(c=> c.addAll(SHELL)).then(()=> self.skipWaiting())); });
self.addEventListener('activate', e=>{
  e.waitUntil(caches.keys().then(keys=> Promise.all(keys.filter(k=> k.startsWith('dpr-portal-') && k!==CACHE).map(k=> caches.delete(k))))
    .then(()=> self.clients.claim()));
});
self.addEventListener('fetch', e=>{
  const r = e.request, u = new URL(r.url);
  if(r.method!=='GET' || u.origin!==location.origin) return;
  if(r.mode==='navigate'){          // the page itself: the newest when online, the kept copy offline
    e.respondWith(fetch(r).then(res=>{ if(res.ok){ const copy = res.clone(); caches.open(CACHE).then(c=> c.put('./', copy)); } return res; })
      .catch(()=> caches.match('./')));
    return;
  }
  e.respondWith(caches.match(r).then(hit=> hit || fetch(r).then(res=>{
    if(res.ok){ const copy = res.clone(); caches.open(CACHE).then(c=> c.put(r, copy)); }
    return res;
  })));
});
"""


def pack_web(html, out):
    """Offline support and an install manifest for a web host."""
    import json
    shell = ['./'] + sorted(str(f.relative_to(out)).replace('\\', '/') for f in out.rglob('*') if f.is_file())
    build = hashlib.sha1((html + ''.join(shell)).encode()).hexdigest()[:12]
    (out / 'sw.js').write_text(SERVICE_WORKER.replace('@@BUILD@@', build).replace('@@SHELL@@', json.dumps(shell + ['icon.svg', 'manifest.webmanifest'])), encoding='utf-8')
    (out / 'icon.svg').write_text(WEB_ICON, encoding='utf-8')
    manifest = {'name': 'DPR Portal', 'short_name': 'DPR Portal', 'start_url': './', 'scope': './', 'display': 'standalone',
                'background_color': '#E8EDF4', 'theme_color': '#E8EDF4',
                'icons': [{'src': 'icon.svg', 'sizes': 'any', 'type': 'image/svg+xml', 'purpose': 'any'}]}
    (out / 'manifest.webmanifest').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    head = ('<link rel="manifest" href="manifest.webmanifest">\n<meta name="theme-color" content="#E8EDF4">\n'
            '<link rel="icon" href="icon.svg" type="image/svg+xml">\n')
    html = html.replace('</head>', head + '</head>', 1)
    cut = html.rindex('</body>')
    sw = ("<script>if('serviceWorker' in navigator && location.protocol==='https:' && window.self===window.top)"
          " addEventListener('load', ()=> navigator.serviceWorker.register('sw.js').catch(()=>{}));</script>\n")
    return html[:cut] + sw + html[cut:]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('portal', help='a portal file built with tools/build.py')
    ap.add_argument('out', help='the app\'s web folder, normally android/app/src/main/assets/www (or build/site with --web)')
    ap.add_argument('--strict', action='store_true', help='fail instead of warning when a download fails')
    ap.add_argument('--web', action='store_true', help='pack for a web host such as GitHub Pages instead of the app')
    a = ap.parse_args()

    out = pathlib.Path(a.out)
    if out.name not in ('www', 'site'):
        sys.exit('The output folder must be called "www" or "site" (it is emptied first).')
    shutil.rmtree(out, ignore_errors=True)
    out.mkdir(parents=True)

    html = pathlib.Path(a.portal).read_text(encoding='utf-8')
    html, sheetjs = bundle_sheetjs(html, out, a.strict)
    html, fonts = bundle_fonts(html, out, a.strict)

    if a.web:
        html = pack_web(html, out)
        extra = 'offline support and install manifest added'
    else:
        shutil.copyfile(HERE / 'bridge.js', out / 'app-bridge.js')
        cut = html.rindex('</body>')
        html = html[:cut] + '<script src="app-bridge.js"></script>\n' + html[cut:]
        extra = 'bridge added'
    (out / 'index.html').write_text(html, encoding='utf-8')

    version = re.search(r"const APP_VERSION = '([^']+)'", html)
    line = f'portal v{version.group(1) if version else "?"} · Excel library {sheetjs} · fonts {fonts} · {extra}'
    print(f'{"web" if a.web else "app"} assets in {out}: {line}')
    if os.environ.get('GITHUB_STEP_SUMMARY'):   # shown on the workflow run's page
        with open(os.environ['GITHUB_STEP_SUMMARY'], 'a', encoding='utf-8') as s:
            s.write(f'**{"Web" if a.web else "App"} assets:** {line}\n\n')


if __name__ == '__main__':
    main()
