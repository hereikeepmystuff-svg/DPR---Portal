# Android app

The DPR Portal is also an Android app. It is the same portal, packed together with its fonts and Excel library so it works fully offline, inside a thin app that adds what a phone needs: saving and sharing files, opening setup and entries files from WhatsApp or email, printing, and the back button.

Every push to `main` builds the app on GitHub (the [Android app workflow](../.github/workflows/android.yml)), and every release gets the APK attached for phones to download.

- [Getting the app](#getting-the-app)
- [The signing key: set it up before installing on site phones](#the-signing-key)
- [Using the app](#using-the-app)
- [Building it yourself](#building-it-yourself)
- [How it works](#how-it-works)

## Getting the app

**From a release (for site phones).** Open the repository's *Releases* page on the phone and tap the APK under *Assets*, e.g. `DPR-Portal-v3.0-build12.apk`.

**From any build (for trying a change).** Open *Actions → Android app*, pick a run and download the APK listed under *Artifacts*. Downloading it needs a GitHub sign-in.

**Making a release.** On GitHub choose *Releases → Draft a new release*. Type a new tag such as `v3.0` (it must start with `v`) and publish. A few minutes later the workflow attaches the APK to the release, together with the portal itself as one offline file (`dpr_portal_v3.0.html`). Pushing a `v…` tag from git does the same and creates the release.

**Installing.** Open the downloaded APK on the phone.
- The first time, Android asks whether the app you downloaded it with (Chrome, Files, WhatsApp) may install apps. Allow it, go back and tap *Install*.
- Play Protect may say the app is from an unknown developer. Choose *More details → Install anyway*.
- Android 7.0 or newer is needed.

**Updating.** Install the new APK over the old one. Everything entered on the phone is kept, as long as both APKs carry the same signature (see below).

## The signing key

Android installs an update only if it is signed with the same key as the app already on the phone. If the key differs, the old app has to be uninstalled first, and **uninstalling deletes everything entered on that phone**. So set up the project's own key once, before the app goes onto site phones.

Without a key, the workflow signs with a temporary key. Builds then show a *Temporary signing key* warning. The temporary key is kept between builds for a while, but it can be lost, so use those APKs only to try the app.

**1. Make a key** (once, on any computer with Java; `keytool` comes with it):

```bash
keytool -genkeypair -v -keystore dpr-portal-release.jks -storetype PKCS12 \
  -alias dpr-portal -keyalg RSA -keysize 4096 -validity 10000
```

It asks for a password and a few details about your organisation. Keep the `.jks` file and its password somewhere safe outside GitHub. Without them, no later version can be installed over the apps already on phones.

**2. Turn the key file into text:**

| On | Command |
|---|---|
| Linux | `base64 -w 0 dpr-portal-release.jks > keystore.txt` |
| macOS | `base64 -i dpr-portal-release.jks -o keystore.txt` |
| Windows (PowerShell) | `[Convert]::ToBase64String([IO.File]::ReadAllBytes("dpr-portal-release.jks")) \| Set-Content keystore.txt` |

**3. Add four secrets** in the repository's *Settings → Secrets and variables → Actions → New repository secret*:

| Secret | Value |
|---|---|
| `ANDROID_KEYSTORE_BASE64` | the contents of `keystore.txt` |
| `ANDROID_KEYSTORE_PASSWORD` | the password you chose |
| `ANDROID_KEY_ALIAS` | `dpr-portal` |
| `ANDROID_KEY_PASSWORD` | the same password (PKCS12 keys share the keystore's password) |

The next build is signed with this key. Delete `keystore.txt` afterwards.

A release published before the key was set up still carries an APK with the temporary key. To replace it, open that release's run under *Actions → Android app* and choose *Re-run all jobs*. The new APK, signed with the project key, takes the place of the old one in the release.

An app installed earlier with the temporary key can't be updated to one signed with the project key. Before switching, take a full backup on that phone (*Settings → Data*), uninstall, install the new APK and restore the backup.

## Using the app

The app *is* the portal, so everything in the [user guide](user-guide.md) applies: roles, PINs, daily entry, setup and entries files, the printable DPR and exports. Each phone keeps its own data, just as each browser does. What the app adds:

**Saving files.** Setup files, entries files, backups and Excel exports go to *Downloads › DPR Portal*. A prompt then offers:
- *Share*, to send the file on by WhatsApp, email or Drive;
- *Open*, to open it in another app, such as Excel for an export.

**Opening files from other apps.** Tap a setup or entries file in WhatsApp, email or Files, and choose *DPR Portal* (or share the file to *DPR Portal*).
- **A setup file** joins the project on a new phone, or brings the latest setup to a phone that already has it, as *Open setup file* does.
- **An entries file** goes straight to the import when a planning manager is signed in. Anyone else is asked to sign in as one first.
- **A full data backup** isn't opened this way. A planning manager restores it in *Settings → Data → Import full data backup*.
- If the lock screen is showing, unlock first, then open the file again.
- If another app doesn't offer *DPR Portal* for a file, save it to the phone and use *Open setup file…* or *Import entries files* in the portal.

**Printing and PDF.** *Printable DPR → Print / Save as PDF* opens Android's print screen. Choose a printer, or *Save as PDF*. Only the report is printed.

**The back button** works through what is open, one press at a time:
1. it closes an open dialog, menu or Settings;
2. it goes back to the Progress tab;
3. it scrolls to the top;
4. it leaves the app.

Leaving keeps the app as it was, including anything typed but not saved. On the lock screen, back leaves the app straight away.

**Screen sizes.** The app fits small and large phones, tablets and foldables, upright or sideways, and in split screen.
- Turning or folding the phone re-lays out the page without reloading it.
- Held sideways, the header gets out of the way.
- Buttons and tabs are larger for fingers.
- On a phone, the printable DPR scrolls sideways one section at a time, so the page itself never does.
- Text follows the phone's text size, within limits the layout can take, and pinch-to-zoom works.

**Offline.** Nothing needs a connection: the fonts and the Excel library are inside the app. If a build couldn't download them, its summary says so. Such an app uses the phone's fonts, and the summary Excel export needs a connection.

**Where the data lives.** Entries stay in the app's storage on the phone. *Uninstall* and *Clear storage* delete them, so take full backups (*Settings → Data*). Android's own backup may bring the data back on a new phone, but don't rely on it. The app and Chrome on the same phone keep separate data. To move from one to the other, make a full backup in one and restore it in the other.

## SharePoint sync in the app

From v3.0 the app can keep the project in step through SharePoint. See [SharePoint sync](sharepoint.md).
- **Signing in:** Microsoft's sign-in page opens inside the app. The back button returns to the portal.
- **Address for IT:** IT registers the app's address once, `https://appassets.androidplatform.net/assets/www/index.html`, as a single-page application redirect URI.
- **Invite links:**
  - Opened in the phone's browser, an invite link offers **Open in the DPR Portal app**.
  - Or, in the app, choose *Join with invite link* and paste it.
  - Links made in the app point at the website, so they also work on laptops.
- **Device rules:** if the organisation only allows sign-ins from approved apps or managed devices, the in-app sign-in may be refused. The website in the phone's browser is the alternative.

## Building it yourself

You need JDK 17, the Android SDK (platform 35, build-tools 34) and Gradle 8.10.2. Android Studio provides the SDK and runs Gradle for you: open the `android` folder in it.

```bash
# 1. the portal, packed for the app (fonts and SheetJS are downloaded into it)
python3 tools/build.py --seed src/seeds/demo.json --out build/portal.html
python3 android/prepare_assets.py build/portal.html android/app/src/main/assets/www

# 2. the APK
cd android
gradle assembleDebug        # app/build/outputs/apk/debug/app-debug.apk
gradle assembleRelease      # signed with DPR_KEYSTORE_PATH etc. if set, else the debug key
```

`prepare_assets.py` warns, and carries on, if it can't download the fonts or SheetJS; `--strict` makes that an error. The release build reads these environment variables:

| Variable | Use |
|---|---|
| `DPR_VERSION_NAME` | version shown in Android's app info (CI: portal version and run number, e.g. `3.0 (build 57)`) |
| `DPR_VERSION_CODE` | a number that must go up with every build (CI: minutes since 2026) |
| `DPR_KEYSTORE_PATH`, `DPR_KEYSTORE_PASSWORD`, `DPR_KEY_ALIAS`, `DPR_KEY_PASSWORD` | the signing key |

**An app for your own project.** Build the portal from your private seed (see the [README](../README.md#your-own-projects-portal)), then pack it and build as above:

```bash
python3 tools/build.py --seed seeds/private/my_project.json --workbook DPR.xlsx --out build/portal.html
python3 android/prepare_assets.py build/portal.html android/app/src/main/assets/www
```

That APK carries your project's data (BOQ, rates, the workbook), so build it on your own computer and share it only with the team. Don't push it, or a seed, to the public repository. The workflow only ever builds the demo.

## How it works

| Part | What it does |
|---|---|
| `android/app/…/MainActivity.java` | A full-screen WebView. It serves the packed portal from the app at `https://appassets.androidplatform.net/assets/www/index.html` (androidx.webkit `WebViewAssetLoader`), so browser storage, IndexedDB and Web Crypto behave as in Chrome. It also keeps the page clear of the status bar, navigation bar, camera cut-out and keyboard, writes saved files to Downloads, offers *Share* and *Open*, prints, opens incoming files and handles the back button. |
| `android/bridge.js` | Added to the packed page. It sends the portal's file saves and printing to the app, opens incoming setup and entries files through the portal's own *Open setup file* and *Import entries files* flows, and handles the back button. It also adds touch and screen-size styles. In a normal browser it does nothing. |
| `android/prepare_assets.py` | Copies a built portal into `android/app/src/main/assets/www/`, downloads its fonts (Latin subsets) and SheetJS into the app, and adds the bridge. The folder is generated and not committed. |
| `.github/workflows/android.yml` | Builds the demo portal, packs it, then builds, signs and names the APK and uploads it or attaches it to the release. The packing and bridge tests run in `.github/workflows/tests.yml`, with screenshots. |

Tests (see [development](development.md#tests)):

```bash
python3 tests/android_assets.py   # the packing, without a network
python3 tests/android_bridge.py   # the bridge in Chromium: files, printing, back button, lock screen, five screen sizes
```
