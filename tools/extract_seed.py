#!/usr/bin/env python3
"""Pull the project seed out of an existing portal file, so it can be rebuilt with tools/build.py.

The seed holds the project's own data (BOQ, rates, quantities, workbook). Keep extracted seeds
out of public repositories: the default output folder seeds/private/ is git-ignored.

Usage
  python3 tools/extract_seed.py dpr_portal_v2.3.html --out seeds/private/my_project.json
  python3 tools/build.py --seed seeds/private/my_project.json --out my_project_portal.html
"""
import argparse, json, pathlib, re, sys


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('portal', help='a portal HTML file built for your project')
    ap.add_argument('--out', default='seeds/private/project.json')
    a = ap.parse_args()

    html = pathlib.Path(a.portal).read_text(encoding='utf-8')
    line = next((l for l in html.split('\n') if l.startswith('const SEED = ')), None)
    if not line:
        sys.exit('No embedded project data found (expected a line starting "const SEED = ").')
    seed = json.loads(line[len('const SEED = '):].rstrip().rstrip(';'))

    key = re.search(r"const STORAGE_KEY = '([^']+)';", html)
    title = re.search(r'<title>([^<]*)</title>', html)
    wb = re.search(r"source:'seed'[^}]*?fileName:'([^']+)'", html)
    if key: seed['storage_key'] = key.group(1)        # same key = the rebuilt file keeps the data already in the browser
    if title: seed['page_title'] = title.group(1).replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
    if wb and seed.get('template_b64'): seed['workbook_name'] = wb.group(1)

    out = pathlib.Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(seed), encoding='utf-8')
    print(f'wrote {out}: {len(seed.get("items", []))} BOQ items, {len(seed.get("towers", []))} areas, '
          f'workbook {"included" if seed.get("template_b64") else "not included"}, storage key {seed.get("storage_key", "(default)")}')


if __name__ == '__main__':
    main()
