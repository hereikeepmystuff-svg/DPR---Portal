# Development

## Requirements

- Python 3.10+
- Node.js, for `node --check` syntax checks
- Playwright for Python with Chromium, for the tests:

  ```bash
  pip install playwright openpyxl
  python3 -m playwright install chromium
  ```

## Build

```bash
python3 tools/build.py --seed src/seeds/demo.json --out dist/dpr-portal.html
```

`src/portal.template.html` is the application. Edit it directly, or keep a version's changes in a patch script like the ones in `tools/history/`. For a quick syntax check of the script part:

```bash
python3 - <<'EOF'
s = open('dist/dpr-portal.html', encoding='utf-8').read()
js = s[s.index('<script>\n', s.index('</head>')) + 8 : s.rindex('</script>')]
open('/tmp/portal.js', 'w', encoding='utf-8').write(js)
EOF
node --check /tmp/portal.js
```

## Tests

| Test | Runs against | Covers |
|---|---|---|
| `tests/smoke_demo.py` | `dist/dpr-portal.html` | First run, progress (item list and pour grid), labour copy, machinery prefill, settings (words, money, modules, BOQ paste, rename), floors & pours, structure, printable DPR, setup and entries files between two devices, screen lock, phone layout |
| `tests/project/test_roles_and_sharing.py` | a project build with its workbook | Roles, PINs, tower limits, view-only, setup and entries files, merge and re-import, settings save, export, migration from a pre-roles copy |
| `tests/project/test_regression.py` | same | Pour grid, monthly plan and audit, Excel export into the workbook, close, reopen and roll-over, the import wizard (`tests/fixtures/Harbour_View_DPR.xlsx`), phone overflow |
| `tests/project/test_daily_entry.py` | same | Day status, date stepper, unsaved-change guards, item search and filters, keyboard moves, soft checks, labour copy, machinery and staff prefill, export guard, sign-out guard, screen lock, site-log dates, phone cards |
| `tests/project/test_entry_filters.py` | same | Planned-this-month filter, the ten-times-plan check, focus after save, `/` search, engineer and viewer views |
| `tests/project/test_project_settings.py` | same | Words, money, modules, BOQ paste, renaming a tower (with the workbook alias on export and a stale entries file), floors & pours with custom words |
| `tests/android_assets.py` | `build/portal.html` | Packing the portal into the Android app without a network: local fonts (each file once) and SheetJS, the bridge, the offline fallback and `--strict` |
| `tests/android_bridge.py` | the packed app (`android/app/src/main/assets/www`) | The app bridge with a stand-in for Android: saving files, printing, the back button, the lock screen, setup and entries files opened from other apps, no sideways scrolling at five phone and tablet sizes |

```bash
python3 tests/smoke_demo.py                                  # demo build
python3 tests/project/test_regression.py my_project.html     # a build made from your own seed and workbook

python3 tools/build.py --seed src/seeds/demo.json --out build/portal.html
python3 tests/android_assets.py                              # the Android packing, offline
python3 android/prepare_assets.py build/portal.html android/app/src/main/assets/www
python3 tests/android_bridge.py                              # the Android bridge
```

The project tests were written for a nine-tower building project with its own DPR workbook: towers named *Tower A*–*Tower H* and *NTA*, BOQ items such as 13 *Shuttering*, and the workbook's *Data* sheet. Pointed at another project, they need those names adjusted.

Outputs (downloads, screenshots) go to `tests/output/`, which git ignores. `DPR_TEST_OUT` sets another folder. `DPR_SHOTS=docs/screenshots` makes the smoke test refresh the documentation screenshots.

## Releasing a version

1. Make the change in `src/portal.template.html`, or in a patch script applied to it.
2. Bump the version in four places:
   - `APP_VERSION`;
   - the version pill (`id="versionBtn"`);
   - the footer (`DPR Portal vX.Y`);
   - a new first entry in `CHANGELOG` inside the template, written in the users' words.
3. Add the same entry to `CHANGELOG.md`.
4. Rebuild `dist/dpr-portal.html` and run the smoke test. Run the project tests against your own project's build.
5. Keep a copy of each release under a versioned file name (`dpr_portal_vX.Y.html`) for the people who use it.

## The Android app

The app in `android/` is a thin shell around whichever portal file is packed into it. A change to the portal reaches the app with the next build. Nothing in `android/` needs touching unless the portal's file, print, back-button or sign-in flows change; `tests/android_bridge.py` notices when they do.

- **Every push to `main`** runs [`.github/workflows/android.yml`](../.github/workflows/android.yml), which checks the bridge and builds the APK. Download it from the run's *Artifacts*.
- **Releasing:** after step 5 above, publish a GitHub release with a tag such as `v2.4`. The workflow attaches `DPR-Portal-v2.4-build<N>.apk` to it.
- **Version:** the APK takes the portal's `APP_VERSION` and the run number, e.g. `2.4 (build 61)`. Its version code goes up with every build, so each APK installs over the last one.
- **Signing:** the four `ANDROID_*` repository secrets, set up once. See [android.md](android.md#the-signing-key).

Building locally, with your own project, and how the parts fit: [android.md](android.md#building-it-yourself).
