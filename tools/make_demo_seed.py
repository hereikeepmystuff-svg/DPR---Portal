#!/usr/bin/env python3
"""Writes src/seeds/demo.json: a made-up residential project used by the public demo build.

Every name, rate and quantity here is invented. Run it again after editing to refresh the seed:
  python3 tools/make_demo_seed.py && python3 tools/build.py --seed src/seeds/demo.json --out dist/dpr-portal.html
"""
import json, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent

TOWERS = ['Tower A', 'Tower B', 'Tower C', 'Podium']
# (BOQ id, short name, description, unit, rate, total quantity, stage) — stage drives the demo's progress to date
ITEMS = [
    ('1.1', 'Excavation in all soils', 'Excavation in all kinds of soil for foundations and basement, including disposal within 1 km', 'CUM', 320, 18500, 'sub'),
    ('1.2', 'Backfilling with excavated earth', 'Backfilling around foundations with selected excavated earth in 200 mm compacted layers', 'CUM', 180, 9200, 'sub'),
    ('1.3', 'Anti-termite treatment', 'Pre-construction anti-termite treatment to foundations and plinth', 'SQM', 95, 12400, 'sub'),
    ('2.1', 'PCC M15 below foundations', 'Plain cement concrete M15 in levelling course below foundations', 'CUM', 6800, 640, 'sub'),
    ('2.2', 'RCC M40 raft', 'Reinforced cement concrete M40 in raft foundation, excluding reinforcement', 'CUM', 9600, 4200, 'sub'),
    ('2.3', 'RCC M40 columns & walls', 'Reinforced cement concrete M40 in columns and shear walls, excluding reinforcement', 'CUM', 10100, 6800, 'frame'),
    ('2.4', 'RCC M35 slabs & beams', 'Reinforced cement concrete M35 in slabs and beams, excluding reinforcement', 'CUM', 9400, 9500, 'frame'),
    ('2.5', 'Reinforcement Fe550D', 'TMT reinforcement Fe550D: cutting, bending, placing and binding', 'MT', 78500, 3350, 'frame'),
    ('2.6', 'Aluminium formwork', 'Aluminium formwork system for walls and slabs, including props', 'SQM', 410, 86000, 'frame'),
    ('2.7', 'Conventional shuttering', 'Plywood shuttering to podium and transfer structures', 'SQM', 520, 21000, 'frame'),
    ('3.1', 'AAC blockwork 200 mm', 'AAC block masonry 200 mm thick in thin-bed mortar', 'SQM', 1150, 38000, 'fit'),
    ('3.2', 'Internal plaster 12 mm', 'Gypsum or cement plaster 12 mm thick to internal walls', 'SQM', 310, 92000, 'fit'),
    ('3.3', 'External plaster 20 mm', 'Cement plaster 20 mm thick in two coats to external walls', 'SQM', 420, 31000, 'fit'),
    ('3.4', 'Waterproofing', 'Membrane waterproofing to basement walls, wet areas and terraces', 'SQM', 640, 9800, 'fit'),
    ('4.1', 'Vitrified tile flooring', 'Vitrified tiles 800 x 800 mm laid on mortar bed, including skirting', 'SQM', 1280, 41000, 'finish'),
    ('4.2', 'Internal emulsion paint', 'Two coats of acrylic emulsion over primer and putty', 'SQM', 165, 120000, 'finish'),
    ('4.3', 'External texture paint', 'Textured exterior paint system over primer', 'SQM', 260, 34000, 'finish'),
    ('4.4', 'Aluminium windows', 'Powder-coated aluminium sliding windows with glazing and hardware', 'SQM', 6900, 5600, 'finish'),
    ('4.5', 'Flush doors with frames', 'Flush doors with hardwood frames, hardware and polish', 'NOS', 14500, 1150, 'finish'),
    ('5.1', 'MEP sleeves & inserts', 'Sleeves, inserts and cut-outs for services, as directed', 'NOS', 850, 3600, 'frame'),
]
SHARE = {'Tower A': 0.3, 'Tower B': 0.3, 'Tower C': 0.3, 'Podium': 0.1}
DONE = {   # share of each area's quantity already done before the portal was started, by stage
    'Tower A': {'sub': 1.0, 'frame': 0.62, 'fit': 0.18, 'finish': 0.0},
    'Tower B': {'sub': 1.0, 'frame': 0.41, 'fit': 0.05, 'finish': 0.0},
    'Tower C': {'sub': 0.95, 'frame': 0.12, 'fit': 0.0, 'finish': 0.0},
    'Podium':  {'sub': 1.0, 'frame': 0.85, 'fit': 0.30, 'finish': 0.05},
}

seed = {
    'items': [{'sno': i + 1, 'boq_id': b, 'desc': d, 'short': s, 'uom': u, 'rate': r, 'total_qty': q}
              for i, (b, s, d, u, r, q, _) in enumerate(ITEMS)],
    'towers': TOWERS,
    'achieved': {t: [round(q * SHARE[t] * DONE[t][st], 2) for (_, _, _, _, _, q, st) in ITEMS] for t in TOWERS},
    'project': {'contractor': 'Demo Constructions Ltd', 'name': 'Riverside Residences (demo)', 'employer': 'Riverside Developers (demo)'},
    'machinery': [{'sno': i + 1, 'label': l, 'uom': u, 'default': d} for i, (l, u, d) in enumerate([
        ('Tower crane', 'No', 3), ('Passenger & material hoist', 'No', 3), ('Concrete pump', 'No', 1), ('Boom placer', 'No', 2),
        ('Transit mixer', 'No', 0), ('Excavator', 'No', 0), ('Backhoe loader', 'No', 1), ('Mobile crane', 'No', 1),
        ('Bar bending machine', 'Set', 4), ('Bar cutting machine', 'Set', 4), ('DG set', 'No', 2), ('Water tanker', 'No', 1)])],
    'material_items': [{'key': 'steel', 'label': 'Steel', 'uom': 'MT'}, {'key': 'cement', 'label': 'Cement', 'uom': 'Bags'},
                       {'key': 'rmc', 'label': 'Ready-mix concrete', 'uom': 'CUM'}, {'key': 'blocks', 'label': 'AAC blocks', 'uom': 'Nos'}],
    'staff_roles': [{'label': l, 'default': d} for l, d in [
        ('Project manager', 1), ('Construction manager', 1), ('Site engineers', 6), ('Quality engineers', 2),
        ('Safety officers', 2), ('Surveyors', 1), ('Store keepers', 1), ('Supervisors', 8)]],
    'labour_day_trades': ['Carpenter', 'Carpenter helper', 'Fitter', 'Fitter helper', 'Mason', 'Mason helper', 'Unskilled',
                          'Welder', 'Electrician', 'Plumber', 'Painter'],
    'labour_night_trades': ['Carpenter', 'Fitter', 'Mason', 'Unskilled'],
    'labour_extra_roles': ['Supervisor', 'Operator'],
    'labour_presets_default': [
        {'contractor': 'Alpha Formwork Co.', 'tower': 'Tower A', 'category': 'Formwork'},
        {'contractor': 'Alpha Formwork Co.', 'tower': 'Tower B', 'category': 'Formwork'},
        {'contractor': 'Beta Rebar Works', 'tower': 'ALL', 'category': 'Reinforcement'},
        {'contractor': 'Gamma Masonry', 'tower': 'Tower C', 'category': 'Masonry'},
        {'contractor': 'Delta Finishes', 'tower': 'ALL', 'category': 'Plaster & paint'},
        {'contractor': 'Omega MEP Services', 'tower': 'ALL', 'category': 'MEP'},
    ],
    'baseline_as_of': '',
    'daily_history': {},
    'tower_daily_history': {},
    'storage_key': 'dpr_demo_v2',
    'page_title': 'DPR Portal (demo project)',
}

out = ROOT / 'src' / 'seeds' / 'demo.json'
out.write_text(json.dumps(seed, indent=1), encoding='utf-8')
print('wrote', out)
