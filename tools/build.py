#!/usr/bin/env python3
"""Build a ready-to-use portal file from the template and a project seed.

The portal is a single, self-contained HTML file that runs offline. Everything specific to a
project (BOQ items, towers, baseline quantities, trades, machinery, the project workbook) comes
from a seed JSON file and is embedded at build time.

Examples
  # the public demo build
  python3 tools/build.py --seed src/seeds/demo.json --out dist/dpr-portal.html

  # your own project, rebuilt from a portal file you already use (keep it out of git!)
  python3 tools/extract_seed.py my_portal.html --out seeds/private/my_project.json
  python3 tools/build.py --seed seeds/private/my_project.json --out my_project_portal.html

  # embed (or replace) the project's DPR workbook so exports write straight into it
  python3 tools/build.py --seed seeds/private/my_project.json --workbook DPR.xlsx --out my_project_portal.html

Build-only keys in the seed (all optional): storage_key, page_title, workbook_name.
"""
import argparse, base64, json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
BUILD_ONLY = ('storage_key', 'page_title', 'workbook_name')


def slug(text):
    return re.sub(r'[^a-z0-9]+', '_', (text or '').lower()).strip('_')[:24] or 'project'


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--seed', required=True, help='project seed JSON')
    ap.add_argument('--out', required=True, help='portal HTML file to write')
    ap.add_argument('--template', default=str(ROOT / 'src' / 'portal.template.html'))
    ap.add_argument('--workbook', help='project DPR workbook (.xlsx) to embed; replaces any workbook in the seed')
    ap.add_argument('--storage-key', help="browser storage key; changing it gives the file a fresh, empty store")
    ap.add_argument('--title', help='browser tab title')
    a = ap.parse_args()

    seed = json.loads(pathlib.Path(a.seed).read_text(encoding='utf-8'))
    for key in ('items', 'towers', 'project'):
        if key not in seed:
            sys.exit(f'seed is missing "{key}"')
    meta = {k: seed.pop(k) for k in BUILD_ONLY if k in seed}
    if a.workbook:
        wb = pathlib.Path(a.workbook)
        seed['template_b64'] = base64.b64encode(wb.read_bytes()).decode('ascii')
        meta['workbook_name'] = wb.name
    if meta.get('workbook_name') and seed.get('template_b64'):
        seed['workbook_name'] = meta['workbook_name']

    name = (seed.get('project') or {}).get('name') or 'Project'
    storage_key = a.storage_key or meta.get('storage_key') or f"dpr_{slug(name)}_v2"
    title = a.title or meta.get('page_title') or f"{name} — DPR Portal"

    html = pathlib.Path(a.template).read_text(encoding='utf-8')
    for marker in ('@@SEED@@', '@@STORAGE_KEY@@', '@@TITLE@@'):
        if html.count(marker) != 1:
            sys.exit(f'template should contain {marker} exactly once')
    esc = lambda t: t.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    html = (html.replace('@@SEED@@', json.dumps(seed))
                .replace('@@STORAGE_KEY@@', storage_key.replace("'", ''))
                .replace('@@TITLE@@', esc(title)))
    out = pathlib.Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding='utf-8')
    print(f'built {out} ({len(html):,} chars) · storage key {storage_key} · '
          f'{len(seed["items"])} BOQ items · {len(seed["towers"])} areas · '
          f'workbook: {"embedded" if seed.get("template_b64") else "none"}')


if __name__ == '__main__':
    main()
