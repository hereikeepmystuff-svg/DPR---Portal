# Changelog

Each version is also listed inside the portal: click the version number at the top right.

## v3.0 — 20 Oct 2026 · SharePoint sync
See [docs/sharepoint.md](docs/sharepoint.md).
- **SharePoint sync:** the planning manager connects the project to a SharePoint folder once (Settings → Team & access).
  - Site engineers join with an invite link and sign in with their Microsoft work account.
  - From then on, the setup and everyone's entries stay in step by themselves. No setup or entries files are needed.
- **Works offline:** entries are saved on the device first and sent when there is a connection. A light at the top shows when everything is in step, and what is waiting.
- **No PIN on your own phone:** after the Microsoft sign-in, the portal recognises each person by their work email. A shared site account still works: pick your name and enter your PIN.
- **Roles backed by SharePoint:** with edit access to the `entries` folder only, engineers can't change the setup on the server either.
- **Setup changes arrive by themselves.** They apply once what you're typing is saved, and the portal comes back to the same tab and day.
- **The portal is also a website** (GitHub Pages). It works offline and can be installed to a phone's home screen. The Android app signs in to Microsoft inside the app and opens invite links.
- **Files still work:** setup and entries files work as before for anyone who isn't syncing.
- **Backups carry the workbook:** a full data backup now includes the project's DPR workbook, built in or imported, so a backup can move a project from a portal file to the website or the app. If a workbook file goes missing, *Settings → Workbook & periods* offers to choose it again, keeping everything entered.

## Android app — 20 Oct 2026
The portal as an Android app, built on GitHub from v2.3. The portal itself is unchanged. See [docs/android.md](docs/android.md).
- **Works offline:** the fonts and the Excel library are inside the app.
- **Saving files:** setup files, entries files, backups and Excel exports go to *Downloads › DPR Portal*. From there you can share them (WhatsApp, email, Drive) or open them in another app.
- **Opening files from other apps:** tap a setup or entries file in WhatsApp, email or Files to open it in the app.
  - A setup file joins the project, or updates it.
  - An entries file goes to the planning manager's import.
- **Printing:** the printable DPR prints, or saves as a PDF, through Android.
- **Back button:** closes dialogs, menus and settings first. Then it goes back to Progress, then to the top of the page, then leaves the app.
- **Every screen size:** phones and tablets, upright or sideways, foldables and split screen.
  - Turning the phone doesn't reload the page.
  - Buttons and tabs are bigger for fingers.
  - On a phone, the printable DPR scrolls sideways section by section.
  - Text follows the phone's text size, within limits.
- **Builds:**
  - Every push to `main` builds an APK (*Actions → Android app*).
  - Every release gets the APK attached.
  - With the project's signing key stored as repository secrets, each version installs over the last.

## v2.3 — 19 Oct 2026 · Fits any project
- **Your project's own words:** areas can be Towers, Blocks, Buildings, Zones or Sections; floors can be Levels, Floors or Stages; pours can be Pours, Bays or Segments. Labels follow everywhere, including the printable DPR and exports (Settings → Project).
- **Money and numbers:** rupees in crore or lakh; dollars, dirhams, riyals, pounds or euro in millions; or your own unit. Indian or international digit grouping.
- **Modules:** switch off what a project doesn't report: floors & pours, labour, machinery, material & staff, or any site log. Tabs, day status and the printable DPR follow, and saved data is kept.
- **BOQ from Excel:** paste BOQ items straight from Excel in Settings → BOQ & lists.
  - Headings can be in any order.
  - Rows with a matching BOQ number are updated.
  - Section headings are left out.
- **Renaming an area** (tower, block, zone…) moves everything recorded against it to the new name: progress, plan, pours, cast dates, labour and engineers' access.
  - Exports still find the area in the project workbook under its original name.
  - Entries from engineers who haven't had the new setup yet are translated on import.
- **Printable DPR:** now lists hindrances in force on the day and BBS checks, and shows the value of work done to date.
- **Fixes:**
  - New BOQ rows added together in Settings no longer share a number.
  - Names with quotes no longer break the settings tables.
  - Opening a pour from the Structure tab offers to save unsaved progress first.

## v2.2 — 19 Oct 2026 · Faster daily entry
- **Day status** at the top shows what is saved for the selected day (progress per area, labour, machinery, material & staff) and takes you straight to what is missing.
- **Date stepping:** move a day at a time with the arrows beside the date, or jump back to Today.
- **Unsaved changes:**
  - Tabs with unsaved changes are marked.
  - Changing the date or area, signing out, exporting or sending entries first offers to save them.
  - **Ctrl+S** saves the tab you are on.
- **Progress item list:** find an item by name, BOQ number or #, and show only the items planned this month or already entered.
- **Keyboard:** Enter and the arrow keys move down the column in the progress, labour, machinery, material and staff lists. The mouse wheel no longer changes a number by accident.
- **Copying from the last saved day:**
  - Labour can be copied, with or without the head counts.
  - Machinery and staff on site start from the last saved day instead of fixed defaults.
- **Soft checks:**
  - An entry that pushes an item past its BOQ quantity, or that is ten times the day's plan, is highlighted and must be confirmed before saving.
  - Future dates are flagged.
- **Phones:** the progress item list and the labour table become cards, and a floating Save button follows long lists.
- **Screen lock:** the portal can lock after a period without use (Team & access → Shared computers). Unlocking keeps anything typed but not saved.
- **Fixes:**
  - Machinery counts saved as zero no longer come back as defaults.
  - Empty starter rows are no longer saved as labour crews.
  - New site-log rows start on the entry date.
  - Numbers pasted into material and staff lists fill down the list.

## v2.1 — 19 Oct 2026 · Roles and access
- **Team & access:** planning managers, site engineers and a view-only mode.
  - Each person signs in with their own PIN or password.
  - A recovery code resets a forgotten planning-manager password.
- **Who changes what:**
  - Only planning managers change base data: BOQ, areas, lists, floors & pours, the monthly plan, the project workbook and periods.
  - Engineers make the daily entries, optionally limited to their own areas and to progress only.
- **Who saved what:**
  - Every saved entry records who made it and when.
  - Settings shows the activity on each device.
  - Pour rows and site-log rows show initials, and the printable DPR lists who recorded the day.
- **Engineers can work on their own copy:**
  - The planning manager sends a setup file.
  - Engineers send their entries back as a file.
  - The import keeps the newest version of each record without double counting.
- **Settings tabs:** Team & access, Project, BOQ & lists, Floors & pours, Workbook & periods, Data.
- **Fixes:**
  - Saving Settings no longer drops floors & pours, workbook history or the workbook link.
  - "Today" follows the local date instead of UTC.
  - The labour table header follows the project's own trades.
  - Backups, CSVs and templates also download inside the claude.ai viewer.
  - A warning appears if the browser refuses to save.

## v2.0 — 14 Oct 2026 · New look
- Bright neumorphic look: raised panels, pressed-in entry fields, segmented tabs and lit status pills.
- **In-page dialogs:** messages and confirmations open inside the portal. Closing, reopening and rolling over a period now also work in the claude.ai viewer, which blocks browser pop-ups.
- Save, paste and export confirmations show as a toast at the bottom of the screen, wherever you have scrolled to.
- Change password asks for all three entries in one dialog.
- Version number and an in-app list of changes.

## Earlier releases — Sep–Oct 2026, before version numbers
- **Daily reports:** progress, labour, machinery, material & staff, site logs, the printable DPR, the overview and Excel export.
- **Plan and protection:** password-protected settings and a fixed monthly plan with a change log; paste from Excel; past-date warnings.
- **Workbooks and periods:**
  - An import wizard for any project's DPR workbook.
  - Month close, reopen and roll-over.
  - Exports keep the workbook's own layout.
- **Structure:** the Tower → Level → Pour structure, the Structure tab with slab cycles, and the spreadsheet-style pour grid.
