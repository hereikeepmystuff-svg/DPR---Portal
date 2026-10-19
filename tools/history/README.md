# How each version was produced

Versions v2.1 to v2.3 were made by patch scripts. Each script reads the previous version's finished portal file, applies exact, asserted text replacements, inserts the new module, and writes the next version.

| Script | From → to | Main changes |
|---|---|---|
| `build_v21.py` | v2.0 → v2.1 | Roles and access, sign-in, setup and entries files, settings tabs (`src/modules/access.js`, `team.js`, `access.css`) |
| `build_v22.py` | v2.1 → v2.2 | Faster daily entry: day status, unsaved-change guards, item filters, keyboard, copy and prefill, phone cards, screen lock (`entry.js`, `entry.css`) |
| `build_v23.py` | v2.2 → v2.3 | Words, money, modules, BOQ paste, area renames, module-aware printable DPR (`flex.js`) |
| `make_template.py` | v2.3 → `src/portal.template.html` | Swaps the embedded project data, storage key, title and workbook name for build placeholders |

The scripts are kept as a record. They point at the absolute paths of the machine they ran on, and expect a v2.0 file with the original project's data, which isn't part of this repository. New work starts from `src/portal.template.html`.
