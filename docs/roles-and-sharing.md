# Roles and sharing

## The three roles

| Action | Planning manager | Site engineer | View only |
|---|:---:|:---:|:---:|
| Enter daily progress (whole tower and pours) and mark pours cast | ✓ | ✓ *only their towers, if any are set* | — |
| Enter labour, machinery, material & staff and site logs | ✓ | ✓ *unless "site-wide reports" is off for them* | — |
| Send their entries to the planning manager as a file | ✓ | ✓ | — |
| View every tab and export the DPR to Excel | ✓ | ✓ | ✓ |
| Change BOQ items, towers, lists, floors & pours and the project workbook | ✓ | — | — |
| Set and change the monthly plan | ✓ | — | — |
| Close, reopen and roll over periods | ✓ | — | — |
| Manage the team, import engineers' entries and data backups | ✓ | — | — |

The portal shows each person only what they can use:

- Buttons for base data are hidden from engineers.
- Towers outside an engineer's list are read-only for them. They appear under *Others (view only)* in the tower picker.
- Panels a person can't edit carry a short note explaining why.

## Signing in

- **PINs and passwords.** Planning managers use a password of six or more characters. Engineers use a 4–8 digit PIN, which the planning manager sets and can reset. Only salted SHA-256 hashes are stored.
- **Wrong attempts.** After five wrong attempts, that person's sign-in pauses for 30 seconds.
- **Recovery code.** A planning manager who forgets their password can reset it with the recovery code shown when the account was made. Another planning manager can also set a new password for them.
- **Staying signed in.** By default a session lasts as long as the browser tab is open. **Stay signed in on this device** keeps it across visits.
- **Screen lock.** The planning manager can turn on a lock for shared computers (Team & access → Shared computers). The screen locks after the chosen number of minutes without use and stays locked across a page reload.
- **Who saved what.** Every save records the person and the time. You can see it in:
  - the "Saved by" lines on each tab;
  - initials on pour rows and site-log rows;
  - *Recorded by* on the printable DPR;
  - the activity list in Team & access.

These rules are checked in the browser. They keep people to their job and make every change traceable, but someone holding the file and using the browser's developer tools could get around them. If the portal moves to a shared backend such as SharePoint, the same three roles become server-enforced groups.

## Working on several devices

There is no server. Each person works on their own copy of the portal file, on a laptop, tablet or phone, and two kinds of file keep the copies in step:

```
                     setup file  (BOQ, towers, pours, plan, periods, team, workbook, optionally everyone's entries)
  Planning manager  ─────────────────────────────────────────────▶  Site engineer
  (master copy)     ◀─────────────────────────────────────────────  (own copy)
                     entries file  (that engineer's progress, labour, machinery, material, logs, casts)
```

### Setup file (planning manager → engineers)

Made in **Settings → Team & access → Save setup file** and named `<project>_setup_<date>.json`. It holds:

- the project configuration: BOQ, towers, lists, floors & pours, words, money and modules;
- the team, with PIN hashes;
- the monthly plan and its change log;
- contractor presets;
- periods and the period log;
- the project workbook, if one was imported;
- optionally, every entry made so far.

An engineer opens it from the welcome screen (**I'm joining a project**) or later from **My account → Open setup file…**:

- **Same project:** the base data is updated and the engineer's own entries are kept.
- **Older setup:** if the file is older than the setup already on the device, the portal asks before using it.
- **Different project:** the portal warns that the current project's entries on that device will be removed.

Send a new setup file after any change to base data. The Team & access card says when the last one is out of date.

### Entries file (engineer → planning manager)

Made from **Send my entries…** and named `<project>_entries_<name>_<to-date>.json`. It holds the sender's entries for a date range, with who saved each one and when. Records that arrived in a setup file and were not changed afterwards are left out, so engineers don't send the planning manager's own data back.

The planning manager imports one or more of these from **Team & access → Import entries files…**. Before anything changes, a preview shows each file's counts: *new*, *updated*, *removed*, *same*, *newer here* and *skipped*.

### How merging decides

- **Which record wins.** The unit of comparison is a single record: one tower/day/location of progress, one day's labour, machinery or material report, one site-log row, or one pour's cast date. The most recently saved version wins. Identical records are left alone, so importing the same file twice changes nothing.
- **Deletions.** A removed site-log row or a cleared cast date travels as a deletion marker with its own time. It removes the record only where that record wasn't saved again later.
- **Skipped days.** Days before the project workbook's baseline date, and days in a closed month, are not changed by an import; they are counted as *skipped*. A setup file from the planning manager may write into closed months.
- **Removed or renamed towers.** Entries for a tower the project no longer has are skipped. Entries made under a tower's old name, before the engineer received the setup with the new name, are moved to the new name on import.

**Working tip.** Two people saving the same tower on the same day both "own" that record, and the later save wins. Give each engineer their own towers, or their own pours within a tower.

## Personal data on the device

| What | Where (browser storage) |
|---|---|
| Entries, configuration and team | `localStorage`, under the build's storage key (for example `dpr_demo_v2`) |
| The project workbook | IndexedDB, database `dpr_portal_files` |
| Who is signed in in this tab | `sessionStorage`, key `dpr_session_<projectId>` |
| Stay signed in / screen lock | `localStorage`, keys `dpr_remember_<projectId>` and `dpr_locked_<projectId>` |
| Last item filter chosen | `localStorage`, key `dpr_item_filter` |

Clearing the browser's site data removes all of it. Keep backups (Settings → Data).
