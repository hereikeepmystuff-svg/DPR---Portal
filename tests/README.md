# Tests

Browser tests written with Playwright for Python. Each one drives a real Chromium against a portal file and fails on any page error, console error or native browser dialog.

```bash
pip install playwright openpyxl && python3 -m playwright install chromium

python3 tests/smoke_demo.py                               # the demo build in dist/
python3 tests/project/<test>.py path/to/project_build.html # a build made from your own project seed
```

- `smoke_demo.py` is the end-to-end check for the public demo build. It prints one PASS/FAIL line per check and exits non-zero on any failure.
- `project/` holds the deeper tests, written while building v2.1–v2.3 against a nine-tower project with its own DPR workbook. They log what they see and end with `ERRORS: []` when nothing went wrong. Point them at a portal built from that kind of project. See [docs/development.md](../docs/development.md).
- `fixtures/Harbour_View_DPR.xlsx` is a small made-up DPR workbook, used to test the import wizard.
- `android_assets.py` and `android_bridge.py` check the Android app's web side: how the portal is packed into the app, and the bridge between the page and Android (files, printing, back button, screen sizes). The commands are in their docstrings and in [docs/android.md](../docs/android.md#how-it-works); GitHub runs both on every push.

Downloads and screenshots go to `tests/output/`, or to the folder named in `DPR_TEST_OUT`.
