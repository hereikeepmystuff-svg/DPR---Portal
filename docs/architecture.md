# Architecture

The portal is one HTML file: markup, styles and JavaScript, plus the project's data embedded as a JSON *seed*. There are no dependencies to install and no build step to run it. Network use is optional:
- Google Fonts, and SheetJS from cdnjs for the summary workbook. Both have fallbacks, and the Android app and the website bundle them.
- SharePoint sync (v3.0): Microsoft sign-in and Microsoft Graph.

## File layout (`src/portal.template.html`)

| Part | What it holds |
|---|---|
| `<style>` | Design tokens on `:root` (neumorphic palette, shadows, radii, type), then components: header, toolbars, tabs, tables, pour grid, dialogs, settings, sign-in, day status, phone card layouts, print rules |
| Markup | Header (period pill, user chip, version, settings), the day bar (date stepper, day status, export), the tabs and one `.panel` per tab, plus overlays (sign-in or lock, settings, in-page dialogs, toast, floating save) |
| `<script>` | In order: version and changelog, in-page dialogs, the seed and storage, progress and locations, pour grid, entry page, structure tab, labour, machinery, material & staff, overview, site logs, printable DPR, the workbook engine (`DPRX`), periods, import wizard, export, settings, monthly plan, then the later modules: access (v2.1), team and files (v2.1), faster entry (v2.2), project flexibility (v2.3), SharePoint sync (v3.0), and finally `INIT` |

`const SEED = @@SEED@@;`, `const STORAGE_KEY = '@@STORAGE_KEY@@';` and `<title>@@TITLE@@</title>` are filled in by `tools/build.py`.

## Data

Everything a device knows sits in one object, `store`, saved as JSON in `localStorage[STORAGE_KEY]` by `persist()`. If the browser refuses to save, a one-time warning tells the user to back up. The project workbook is too large for `localStorage`, so its bytes live in IndexedDB (`dpr_portal_files`, key `template`).

| `store.` | Shape | Notes |
|---|---|---|
| `config` (alias `CFG`) | object | Base data (below) |
| `progress` | `{"Tower|YYYY-MM-DD": {sno: {a, p}}}` | Daily achieved (`a`) and planned (`p`) per tower; always the sum of `progressLoc` |
| `progressLoc` | `{"Tower|date": {locId: {sno: qty}}}` | `locId` is `''` for the whole tower or `"L3|P2"` for a pour |
| `plan` | `{"Tower|date": {sno: qty}}` | The fixed monthly plan (falls back to the workbook's history) |
| `planAuditLog` | `[{ts, by, tower, date, sno, item, oldValue, newValue}]` | Plan change log |
| `labour`, `labourCamp` | `{date: [rows]}` | Crew rows `{contractor, tower, category, counts: {"D:Carpenter": n}}`; at-camp rows |
| `machinery` | `{date: {sno: count}}` | |
| `material` | `{date: {key: qty, "S:Role": count, remark}}` | Material received and staff on site |
| `concrete`, `rain`, `hindrance`, `bbs` | `[rows]` | Site logs; each row has `id`, `by`, `at` |
| `pourCast` | `{"Tower|L|P": {date, source, by, at}}` | Cast dates |
| `stamps` | `{key: {by, at}}` | Who saved what and when: `p|Tower|date|locId`, `labour|date`, `mach|date`, `mat|date` |
| `tomb` | `{rowId or "cast|pourId": {by, at}}` | Deletion markers that travel in entries files |
| `periods`, `periodLog` | | Month status (`open`/`closed`), closing cumulative snapshot, log of close, reopen, roll-over and import |
| `activity` | `[{at, by, act, what}]` | Last 3,000 actions on this device |
| `labourPresets`, `pourGridExtra`, `sent`, `lastSetupExport`, `renamesAppliedAt` | | Smaller bookkeeping |

`CFG` (the base data) holds:

- **Project and BOQ:** `project`, `towers`, `items` (`{sno, boq_id, desc, short, uom, rate, total_qty}`), `achieved` (baseline cumulative per tower and item);
- **Workbook history:** `baseline_as_of`, `daily_history`, `tower_daily_history`;
- **Lists:** `machinery`, `material_items`, `staff_roles`, labour trade lists, `concrete_grades`, `pours`;
- **The workbook map:** `template` (where each figure goes in the project workbook) and `bakedThrough`;
- **Team:** `team` (`users` with salted PIN or password hashes, roles, towers and `siteWide`; `recovery`; `autoLock`);
- **Project identity and version:** `projectId`, `updatedAt` (bumped by every base-data change);
- **v2.3 additions:** `terms`, `money`, `modules`, `renames` and `zoneAlias`.

## Daily entry state (v2.2)

Forms on screen always belong to one context, held in `FORM`: the date, and for progress the tower and entry mode.

- **Snapshots.** Each section has a reader (`SECTION_READ`) that turns its form into canonical JSON. `snapSection()` stores that when the form is drawn. A section is *dirty* when its reader no longer matches its snapshot; the pour grid keeps its own count of unsaved cells.
- **Guard.** `leaveGuard()` runs before the date, tower or entry mode changes, and before sign-out. It offers to save (against the old context), discard or keep editing. `saveBeforeAction()` does the same before an export or an entries file.
- **Indicators.** `updateDirtyUI()` marks the tabs, pulses the Save buttons, redraws the day status and shows the floating save button.

## Words, money and modules (v2.3)

- **Words.** `T('zone' | 'level' | 'pour' | 'zones' | …)` returns the project's words. Static labels carry `data-term` and are filled by `applyTerms()`; the rest are built with `T()`.
- **Money.** `MONEY()` returns the currency symbol, the large-amount unit and its size, and the number locale. `fmt()` formats with that locale.
- **Modules.** `modOn(k)` gates tabs, sub-tabs, overview cards, day-status chips and printable-DPR sections. Data of a switched-off module is kept.
- **Renames.** `renameZone(from, to)` moves every key and reference: progress, locations, plan, stamps, casts, deletion markers, labour rows, presets, the concrete and BBS logs, closing snapshots, baselines, history, pours and engineers' towers.
  - It records the rename in `CFG.renames` and, if the old name was a workbook label, in `CFG.zoneAlias`.
  - Exports translate back through `zoneAlias`.
  - Entries files carry the sender's `setupUpdatedAt`, so renames the sender hasn't seen are applied on import.
  - Devices that receive a newer setup apply pending renames to their own store.

## Access (v2.1)

- **Roles.** `PERMS` maps permissions (`base`, `plan`, `periods`, `team`, `import`, `progress`, `site`, `cast`, `send`, `export`, `view`) to roles. `can(perm, tower)` adds engineers' tower and site-wide limits. `need()` explains a refusal in a dialog.
- **Read-only panels.** Disabled `<fieldset class="pfs">` elements and the body classes `no-base`, `no-site` and `no-entry` hide what a person can't use.
- **Secrets.** Stored as salted SHA-256 (`crypto.subtle`).
- **Sessions.** In `sessionStorage`, optionally remembered in `localStorage`.
- **Setup and entries files.** `buildSetupPackage()`, `collectEntries()`, `mergeEntries()` (newest wins per record, using `stamps` and row `at`, with deletion markers) and `joinFromSetupFile()`.

## SharePoint sync (v3.0)

The module is `src/modules/sync.js`, patched in by `tools/history/build_v30.py`. The full description is in [SharePoint sync](sharepoint.md#9-technical-notes).

**The folder.**
- `dpr-project.json`: the setup package, the same shape as a setup file, written by planning managers.
- `dpr-workbook.xlsx`: the workbook.
- `entries/<YYYY-MM>__<device>.json`: what each device entered, per month.

**Connection details.**
- `CFG.sync` holds the client and tenant IDs, plus the drive and folder ids. It travels with the setup.
- `tools/build.py --ms-client-id --ms-tenant --portal-url` can build defaults into a portal (`FACTORY.sync`).

**Device-only state.** None of it is in `store` or in backups:
- `dpr_ms_auth`: the Microsoft account and its tokens;
- `dpr_sync_<projectId>`: the eTags already seen, content hashes already sent, and the last result;
- `dpr_device_id`.

**A sync (`syncNow`).**
1. Pull the setup. When its eTag changed, apply it, unless this planning manager's own unsent change is newer.
2. Pull the workbook.
3. Pull every other device's changed entries files through `mergeEntries(…, {via:'sync'})`.
4. Push the setup (planning managers, with `If-Match`; on 412 the newer setup wins).
5. Push this device's months whose content hash changed.

**Who sent what.**
- Records stamped `via:'sync'` or `via:'setup'` came from elsewhere and are never sent back (`syncOwnByMonth`).
- Removals that arrive by sync are marked the same way.

**Triggers.** `persist()` is wrapped to schedule a sync a few seconds after each save. There is also a two-minute timer, and syncs on visibility, coming back online, and Sync now.

**Applying received data.**
- New entries re-render when nothing is half-typed (`syncIdle`).
- A new setup reloads the page through `reloadKeepingPlace()`, which restores the tab, day, area and scroll position.

**Sign-in.** Authorization code with PKCE, built on `crypto.subtle`; the redirect comes back in the URL fragment. Renewal uses the refresh token. When that has expired (24 hours for single-page apps), a hidden `prompt=none` frame tries first; a tiny script at the top of `<head>` stops that frame's copy of the page from loading anything else.

## The workbook engine (`DPRX`)

Project DPR workbooks are filled in place, so their formulas, formatting, images and other sheets survive.

- **Reading and writing the file.** A small zip reader and writer built on the browser's `CompressionStream`/`DecompressionStream`. The `.xlsx` is opened, only the sheet XML it needs is rewritten, and everything else is copied byte for byte.
- **`analyze`.** Detects the progress sheet: the header row; the row of dates; the item, unit, rate, quantity and cumulative columns; the tower or zone labels (with a row map); and the labour, machinery and log sheets. The import wizard shows this mapping so it can be corrected.
- **`buildTemplate`.** Turns that mapping into `CFG.template`: where every figure goes.
- **`exportInto`.** Writes portal entries (daily planned and achieved, labour rows, machinery counts, site-log rows) into the mapped cells. It reports rows that didn't fit and cells that hold formulas.
- **`rollover`.** Shifts the date columns to the next month, clears the daily cells, writes closing cumulatives and relabels the month names in the headers.

## Building and the seed

`tools/build.py` replaces the three placeholders in the template:

- the seed JSON, minus build-only keys;
- a storage key, by default derived from the project name;
- the page title.

With `--workbook`, it also embeds a DPR workbook as `template_b64`. `tools/extract_seed.py` does the reverse for an existing portal file, recording its storage key so that a rebuilt file keeps the data already in that browser.

On first run, `makeDefaultConfig()` turns the seed (`FACTORY`) into `CFG`. If the seed embeds a workbook, its layout map is derived the first time it's needed (`ensureTemplate()`).
