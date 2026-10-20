# SharePoint sync

From v3.0, the project can live in a SharePoint folder. The planning manager connects it once. After that, site engineers open an invite link and sign in with their Microsoft work account, and everything stays in step by itself: no setup files or entries files. That includes the BOQ, the plan, periods and the team, and everyone's daily entries.

- [How it works](#how-it-works)
- [1. IT: register the portal with Microsoft 365 (once)](#1-it-register-the-portal-with-microsoft-365-once)
- [2. The website (once)](#2-the-website-once)
- [3. Planning manager: connect the project](#3-planning-manager-connect-the-project)
- [4. Site engineers: join](#4-site-engineers-join)
- [5. Day to day](#5-day-to-day)
- [6. Moving a project you already run onto sync](#6-moving-a-project-you-already-run-onto-sync)
- [7. When something goes wrong](#7-when-something-goes-wrong)
- [8. Security and privacy](#8-security-and-privacy)
- [9. Technical notes](#9-technical-notes)

## How it works

```
SharePoint folder (one per project)
  dpr-project.json        the setup: BOQ, areas, floors & pours, plan, periods, team. Planning managers write it.
  dpr-workbook.xlsx       the project's DPR workbook, if one has been imported
  entries/                each device's entries, one file per month: 2026-10__d7k2….json
  About these files.txt   a note for anyone browsing the folder
```

- **Each device keeps a full copy.** It saves on the device first, then sends what was entered there to the folder. It also collects everyone else's files.
- **Same rules as entries files:** the newest version of a record wins, removals travel, and nothing is counted twice. Days in closed periods are left alone.
- **Offline still works:** entries wait on the device until there is a connection.
- **Signing in:** people use their Microsoft 365 work account. SharePoint's own permissions decide who can read the folder and who can write to it.

The portal still works as before without SharePoint. Setup and entries files stay available for anyone who isn't syncing.

## 1. IT: register the portal with Microsoft 365 (once)

About ten minutes for someone who administers the company's Microsoft 365 (Entra ID). There is no server and no secret: the portal signs people in the way any single-page web app does (OAuth 2.0 authorization code with PKCE).

1. **Create the app registration.** In the Microsoft Entra admin center, open **App registrations** and choose **New registration**.
   - Name: `DPR Portal`.
   - Supported account types: **Accounts in this organizational directory only**.
   - Redirect URI: platform **Single-page application (SPA)**, address `https://hereikeepmystuff-svg.github.io/DPR---Portal/`. This is the website, see [step 2](#2-the-website-once).
2. **Add the app's address.** Under **Authentication**, in the *Single-page application* section, add a second redirect URI for the Android app: `https://appassets.androidplatform.net/assets/www/index.html`.

   If the portal is published at another address as well, add that too, exactly as the portal shows it under *Settings → Team & access → SharePoint sync → App registration*.
3. **Add the permissions.** Under **API permissions**, choose *Add a permission → Microsoft Graph → Delegated permissions* and add:
   - `Files.ReadWrite.All`
   - `offline_access`
   - `openid`
   - `profile`
   - `email`

   Then choose **Grant admin consent for (your organisation)**.

   Files.ReadWrite.All is a *delegated* permission. The portal only ever acts as the person signed in, on files that person can already open in SharePoint, and in practice only in the project folder they were invited to.
4. **Hand over the IDs.** Give the planning manager the **Application (client) ID** and the **Directory (tenant) ID** from the app's *Overview*.

   Nothing else is needed: no client secret, no certificate, no API to expose.

**Optional: build the IDs into the website and the app** so nobody has to type them. Add both as repository variables (*Settings → Secrets and variables → Actions → Variables*):

| Variable | Value |
|---|---|
| `DPR_MS_CLIENT_ID` | the Application (client) ID |
| `DPR_MS_TENANT` | the Directory (tenant) ID |

The next website and APK builds include them.

**Device rules:** if your organisation only allows sign-ins from managed devices or approved apps (Conditional Access), the Android app's built-in sign-in may be refused. Either allow it, or let engineers use the website in their phone's browser.

## 2. The website (once)

Browsers can only use Microsoft sign-in from a web address, not from a file opened on the computer. The repository publishes the portal with GitHub Pages:

1. In the repository, open **Settings → Pages**, and under *Build and deployment* set **Source: GitHub Actions**.
2. Run the **Website** workflow once (*Actions → Website → Run workflow*). After that it updates on every push.

The website is at **https://hereikeepmystuff-svg.github.io/DPR---Portal/**.
- It holds only the portal and its demo project; your project's data lives in your SharePoint folder.
- Once opened, it works offline.
- It can be installed to a phone's home screen or a computer's apps (the browser's *Install* or *Add to Home screen*).

The Android app works without the website, but invite links made in the app point at it.

## 3. Planning manager: connect the project

1. **Make a folder in SharePoint** for the project, for example `Documents/DPR Portal/<project>` on the project's site. Start with an empty folder.
2. **Share it** (*Manage access* in SharePoint). Choose one of two setups:
   - **Simple:** everyone on the team gets **Edit** on the folder.
   - **Strict, with roles enforced by SharePoint:**
     - Planning managers get **Edit** on the folder.
     - Engineers get **View** on the folder and **Edit** on its `entries` folder. The portal creates `entries` when you connect, so set this right after connecting, before you send the invite link.
     - View-only people get **View**.
3. In the portal (the website or the app), open **Settings → Team & access → SharePoint sync**.
   - Paste the folder's address from the browser, or its *Copy link* link.
   - Enter the app and tenant IDs from IT, unless they are built in.
   - Choose **Sign in with Microsoft and connect**.
4. The portal sends the setup and every entry already on your device, then shows the **invite link**.
5. Under **People**, add each person's **work email**. The portal then recognises them after the Microsoft sign-in, with no PIN.
6. Send the invite link to the team on WhatsApp or by email. You'll find it again under *Team & access → Invite link*.

## 4. Site engineers: join

**On a phone with the Android app**
- Open the invite link and choose **Open in the DPR Portal app**.
- Or, in the app, choose *Join with invite link* and paste it.

**In a browser** (laptop or phone): open the invite link.

Then choose **Sign in with Microsoft**. The project and everyone's entries download, and the portal signs you in by your work email. That's all: from then on, what you save is sent by itself.

**A shared site account instead of personal ones:**
- The planning manager hands out one Microsoft login for the site devices.
- Each person signs in with it, then picks their own name and enters their PIN.
- Entries still record who made them.

## 5. Day to day

**The light at the top** (next to your name) shows the state of things:

| Light | Meaning |
|---|---|
| ● Synced 10:42 | In step with SharePoint at that time. |
| ● Syncing… | Sending and receiving. |
| ● Offline | No connection. What you save waits on this device and goes when the connection is back. |
| ● Sign in to sync | The Microsoft sign-in on this device has run out. Tap the light, then *Sign in with Microsoft*. |
| ● No access | SharePoint refused your account. The planning manager needs to share the folder with you (edit access to `entries`). |
| ● Update ready | The planning manager changed the setup. It applies once what you're typing is saved. |

Tap the light for details, **Sync now**, or *Sign out of Microsoft*.

**When it syncs:**
- a few seconds after each save;
- every two minutes while the portal is open;
- when the portal comes back on screen;
- when the connection returns.

**When the planning manager changes the setup** (BOQ, areas, plan, periods, team), it reaches everyone by itself. The portal reloads to apply it and comes back to the same tab and day. If you are in the middle of typing, it waits until you've saved.

**Staying signed in:** Microsoft limits sign-ins for web pages to 24 hours. The portal renews quietly in the background where the browser allows it. Where it can't, the light asks for one tap.

**Removing someone:** remove them under *People*, and remove their access to the folder in SharePoint.

**Stopping:** *Team & access → Stop syncing*. Every device stops at its next sync; what is in SharePoint stays there.

## 6. Moving a project you already run onto sync

If your project's data is in a portal file on your computer (opened in the browser from a file):

1. **Export a backup from the v3.0 version of that file.**
   - Open your project's v3.0 portal file in the same browser as before. It opens with the data already there. (A file built from a project seed is rebuilt as in the [README](../README.md#your-own-projects-portal).)
   - Then *Settings → Data → Export full data backup*.
   - From v3.0 the backup also carries the project's DPR workbook, built in or imported, so Excel exports keep working after the move.
2. **Set up the website or the app.**
   - Choose *I'm the planning manager*. Any name and password will do; the backup replaces them.
   - Then *Settings → Data → Import full data backup → Replace everything*.
   - Sign in with your usual account.
3. **Connect SharePoint** as in [step 3](#3-planning-manager-connect-the-project). Everything in the backup is sent, including entries engineers sent you as files.
4. **Ask engineers to send their entries file once more**, as before, and import it before they switch. Their old portal file and the website keep separate data, even on the same computer.

A backup from an older version doesn't carry a built-in workbook. After restoring one, *Settings → Workbook & periods* says the workbook file is missing: choose **Choose the workbook file again** and pick the same `.xlsx`. Everything entered is kept.

## 7. When something goes wrong

| What you see | What to do |
|---|---|
| *Your organisation hasn't approved the DPR Portal app yet* | IT grants admin consent ([step 1.3](#1-it-register-the-portal-with-microsoft-365-once)). |
| *This address isn't registered with the app: …* | IT adds that exact address under *Authentication → Single-page application*. |
| *The app is registered as a web app…* | The address was added under *Web*; IT moves it to *Single-page application*. |
| *The app is registered for your organisation only…* | Enter the Directory (tenant) ID with the app ID in *Team & access*, or build it in with `DPR_MS_TENANT`. |
| *SharePoint couldn't find that folder…* | Check the link, and that the folder is shared with the account you signed in with. |
| *This folder already holds a project* | Choose an empty folder, or open that project on this device instead. |
| *SharePoint sync works in the portal's own web address or the Android app* | You opened a file from the computer, or the portal inside another page. Use the website or the app. |
| *Your organisation's access rules blocked the sign-in* | Conditional Access: IT allows the device or app, or use the website in the phone's browser. |
| *The project workbook hasn't reached this device yet* (Excel export) | Tap the light, then *Sync now*. If it still doesn't come, the planning manager opens *Settings → Workbook & periods*. If it says the workbook file is missing there, they choose it again. |

The files in the folder show who changed them and when, and SharePoint keeps their earlier versions. Please don't edit or rename them by hand.

## 8. Security and privacy

**Where things live:**
- Your project's data lives on the devices and in your SharePoint folder.
- The website and the app hold no project data.

**Sign-in:** goes straight to Microsoft. The portal never sees a password. It keeps the Microsoft tokens on the device, separately from the project data and from full backups.

**What the portal reaches in SharePoint:** only what the signed-in person can already reach. In practice that means the one project folder.

**What enforces the roles:**
- With the strict folder setup, SharePoint itself stops engineers from changing the setup.
- PINs and the in-portal roles still apply as before.
- The project file contains the team with salted hashes of PINs and passwords, as setup files always have. Keep the folder shared only with the team.

## 9. Technical notes

- **Sign-in:**
  - OAuth 2.0 authorization code flow with PKCE (S256), `response_mode=fragment`, against `login.microsoftonline.com/{tenant}/oauth2/v2.0`.
  - Scopes: `Files.ReadWrite.All offline_access openid profile email`.
  - The person is identified from the ID token: its `preferred_username`, `email` and `upn` are matched to the team's work emails, so a sign-in name that differs from the email still works.
  - Refresh tokens for single-page apps last 24 hours. Before asking for a tap, the portal renews silently in a hidden frame (`prompt=none`).
- **Microsoft Graph calls:**
  - `GET /shares/{u!…}/driveItem` turns the pasted folder link into a drive and folder id.
  - Items are addressed by path under the folder: `/drives/{d}/items/{f}:/{name}:`.
  - Files are uploaded with `PUT …:/content`. The setup is uploaded with `If-Match`, so two planning managers' changes are caught: the newer setup wins.
  - Files are downloaded through their pre-signed `@microsoft.graph.downloadUrl`.
  - Listings follow `@odata.nextLink`. Answers 429 and 503 are retried after `Retry-After`.
- **What a device sends:**
  - Records saved on it, or imported on it from files. Records received by sync carry `via:'sync'` and are never sent back.
  - Its files are rewritten only when their content hash changes. Each file is per device and month, so a device never overwrites another's.
- **Code:** `src/modules/sync.js` and `sync.css`, patched into the template by `tools/history/build_v30.py`.
- **Tests:** `tests/sync_e2e.py` runs the whole flow in Chromium against `tests/mock_microsoft.py`, a stand-in for Microsoft sign-in and Graph. It covers:
  - connecting, joining, entries and removals both ways, setup changes, offline use;
  - token expiry, silent renewal, refused access, a shared account, conflicting setups, invite links from the app, and stopping;
  - moving a project whose portal file has its workbook built in onto sync, with a full backup.
