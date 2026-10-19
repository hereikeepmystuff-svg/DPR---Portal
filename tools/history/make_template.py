"""One-off: turn a finished portal build (v2.3) into src/portal.template.html.

The portal ships as one HTML file with its project data (the "seed") embedded on a single
`const SEED = {...};` line. This script swaps that line, the storage key, the page title and the
embedded workbook's file name for placeholders that tools/build.py fills in, and makes the few
project-specific labels generic.

Usage: python3 tools/history/make_template.py <portal build.html> src/portal.template.html
"""
import sys, re

src, dst = sys.argv[1], sys.argv[2]
s = open(src, encoding='utf-8').read()

def rep(old, new, count=1):
    global s
    n = s.count(old)
    assert n == count, (n, old[:100])
    s = s.replace(old, new)

lines = s.split('\n')
seed_lines = [i for i, l in enumerate(lines) if l.startswith('const SEED = ')]
assert len(seed_lines) == 1, seed_lines
lines[seed_lines[0]] = 'const SEED = @@SEED@@;'
s = '\n'.join(lines)

s = re.sub(r"const STORAGE_KEY = '[^']*';", "const STORAGE_KEY = '@@STORAGE_KEY@@';", s, count=1)
s = re.sub(r"<title>[^<]*</title>", "<title>@@TITLE@@</title>", s, count=1)
rep("const FACTORY = SEED; // the data this portal was originally seeded with (Linkbay); used only to build the first-run config",
    "const FACTORY = SEED; // the project data this file was built with (see tools/build.py); used only to build the first-run config")
rep("/* Existing Linkbay setups predate the wizard:", "/* Setups made from the built-in project data predate the wizard:")
rep("fileName:'DPR_Format.xlsx'});", "fileName: SEED.workbook_name || 'Project workbook.xlsx'});")
rep('<button class="btn secondary" id="cfgResetBtn">Reset to Linkbay sample data</button>',
    '<button class="btn secondary" id="cfgResetBtn">Reset to the built-in project data</button>')
rep("{title:'Reset to the original Linkbay sample data?', ok:'Reset', danger:true}",
    "{title:'Reset to the built-in project data ('+(FACTORY.project && FACTORY.project.name || 'sample')+')?', ok:'Reset', danger:true}")

open(dst, 'w', encoding='utf-8').write(s)
print('template written:', dst, len(s), 'chars')
