package com.dprportal.app;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.ActivityNotFoundException;
import android.content.ClipData;
import android.content.ContentResolver;
import android.content.ContentValues;
import android.content.Intent;
import android.content.res.Configuration;
import android.database.Cursor;
import android.graphics.Bitmap;
import android.graphics.Insets;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Environment;
import android.os.Handler;
import android.os.Looper;
import android.print.PrintAttributes;
import android.print.PrintManager;
import android.provider.MediaStore;
import android.provider.OpenableColumns;
import android.util.Base64;
import android.view.View;
import android.view.ViewGroup;
import android.view.Window;
import android.view.WindowInsets;
import android.view.WindowInsetsController;
import android.webkit.JavascriptInterface;
import android.webkit.RenderProcessGoneDetail;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.FrameLayout;
import android.widget.Toast;

import androidx.core.content.FileProvider;
import androidx.webkit.WebViewAssetLoader;

import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;

/**
 * The DPR Portal as an Android app: the portal's single HTML file (with its fonts and Excel library)
 * runs in a WebView, served from the app's own assets under a secure https address so browser
 * storage, IndexedDB and the Web Crypto API behave exactly as in Chrome.
 *
 * The native side adds what a WebView lacks on its own:
 *  - the page fills the screen between the status bar, the navigation bar, any camera cut-out and
 *    the on-screen keyboard, on phones, tablets, foldables and in split screen;
 *  - turning, folding or resizing the screen re-lays out the page without reloading it;
 *  - files the portal saves (Excel exports, setup and entries files, backups) go to
 *    Downloads/DPR Portal and can be opened or shared straight away;
 *  - setup and entries files can be opened in the app from WhatsApp, email or a file manager;
 *  - "Print / Save as PDF" uses Android printing;
 *  - the back button closes dialogs and menus first, then returns to Progress, then leaves.
 */
public class MainActivity extends Activity {
    private static final String HOST = "appassets.androidplatform.net";
    private static final String START_URL = "https://" + HOST + "/assets/www/index.html";
    private static final int REQUEST_FILES = 41;
    private static final int SURFACE = 0xFFE8EDF4;
    private static final int INK = 0xFF1F2B43;
    private static final int MAX_OPEN_BYTES = 40 * 1024 * 1024;

    private WebView web;
    private ValueCallback<Uri[]> fileCallback;
    private Uri pendingOpen;
    private boolean pageReady;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        FrameLayout root = new FrameLayout(this);
        root.setBackgroundColor(SURFACE);

        web = new WebView(this);
        root.addView(web, new FrameLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));
        setContentView(root);
        fitBetweenSystemBars(root);

        WebView.setWebContentsDebuggingEnabled(BuildConfig.DEBUG);
        configure(web);
        // A file this activity was started with is opened once, not again when Android rebuilds it.
        if (savedInstanceState == null) handleIntent(getIntent());
        web.loadUrl(START_URL);
    }

    /** Keep the page clear of the status bar, navigation bar, cut-outs and the keyboard. */
    @SuppressWarnings("deprecation")   // the bar colour and flag calls are only made on Android 7 to 10
    private void fitBetweenSystemBars(View root) {
        Window window = getWindow();
        if (Build.VERSION.SDK_INT >= 30) {
            window.setDecorFitsSystemWindows(false);
            WindowInsetsController bars = window.getInsetsController();
            if (bars != null) {
                int light = WindowInsetsController.APPEARANCE_LIGHT_STATUS_BARS | WindowInsetsController.APPEARANCE_LIGHT_NAVIGATION_BARS;
                bars.setSystemBarsAppearance(light, light);
            }
            root.setOnApplyWindowInsetsListener((v, insets) -> {
                Insets in = insets.getInsets(WindowInsets.Type.systemBars() | WindowInsets.Type.displayCutout() | WindowInsets.Type.ime());
                v.setPadding(in.left, in.top, in.right, in.bottom);
                return WindowInsets.CONSUMED;
            });
        } else {
            window.setStatusBarColor(SURFACE);
            int flags = View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR;
            if (Build.VERSION.SDK_INT >= 26) {
                window.setNavigationBarColor(SURFACE);
                flags |= View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR;
            } else {
                window.setNavigationBarColor(INK);   // Android 7 only draws white navigation buttons
            }
            window.getDecorView().setSystemUiVisibility(flags);
        }
    }

    private void configure(WebView w) {
        WebSettings s = w.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setAllowFileAccess(false);
        s.setAllowContentAccess(true);
        s.setUseWideViewPort(true);
        s.setLoadWithOverviewMode(false);
        s.setSupportZoom(true);
        s.setBuiltInZoomControls(true);
        s.setDisplayZoomControls(false);
        s.setSupportMultipleWindows(false);
        s.setTextZoom(textZoomFor(getResources().getConfiguration()));
        if (Build.VERSION.SDK_INT >= 33) s.setAlgorithmicDarkeningAllowed(false);
        s.setUserAgentString(s.getUserAgentString() + " DPRPortalApp/" + BuildConfig.VERSION_NAME);
        w.setBackgroundColor(SURFACE);
        w.setOverScrollMode(View.OVER_SCROLL_NEVER);

        final WebViewAssetLoader assets = new WebViewAssetLoader.Builder()
                .setDomain(HOST)
                .addPathHandler("/assets/", new WebViewAssetLoader.AssetsPathHandler(this))
                .build();

        w.setWebViewClient(new WebViewClient() {
            @Override
            public WebResourceResponse shouldInterceptRequest(WebView view, WebResourceRequest request) {
                return assets.shouldInterceptRequest(request.getUrl());
            }

            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                Uri url = request.getUrl();
                if (HOST.equals(url.getHost())) return false;
                try {
                    startActivity(new Intent(Intent.ACTION_VIEW, url));
                } catch (ActivityNotFoundException e) {
                    toast("No app on this phone opens that link.");
                }
                return true;
            }

            @Override
            public void onPageStarted(WebView view, String url, Bitmap favicon) {
                pageReady = false;   // a file that arrives now waits for the page
            }

            @Override
            public void onPageFinished(WebView view, String url) {
                pageReady = true;
                deliverPendingFile();
            }

            @Override
            public boolean onRenderProcessGone(WebView view, RenderProcessGoneDetail detail) {
                // The page's engine stopped, usually for lack of memory. Saved entries are safe in
                // storage, so start the page again instead of letting the app close.
                if (view == web) {
                    ViewGroup parent = (ViewGroup) view.getParent();
                    if (parent != null) parent.removeView(view);
                    view.destroy();
                    web = null;
                    pageReady = false;
                    recreate();
                }
                return true;
            }
        });

        w.setWebChromeClient(new WebChromeClient() {
            @Override
            public boolean onShowFileChooser(WebView view, ValueCallback<Uri[]> callback, FileChooserParams params) {
                if (fileCallback != null) fileCallback.onReceiveValue(null);
                fileCallback = callback;
                Intent pick = new Intent(Intent.ACTION_OPEN_DOCUMENT);
                pick.addCategory(Intent.CATEGORY_OPENABLE);
                pick.setType("*/*");
                if (params.getMode() == FileChooserParams.MODE_OPEN_MULTIPLE) pick.putExtra(Intent.EXTRA_ALLOW_MULTIPLE, true);
                try {
                    startActivityForResult(pick, REQUEST_FILES);
                } catch (ActivityNotFoundException e) {
                    fileCallback = null;
                    toast("No file picker is available on this phone.");
                    return false;
                }
                return true;
            }
        });

        w.addJavascriptInterface(new Bridge(), "DPRAndroid");
    }

    /** Follow the phone's text size, within limits the page's layout can take. */
    private static int textZoomFor(Configuration c) {
        float f = c.fontScale;
        if (f < 0.85f) f = 0.85f;
        if (f > 1.3f) f = 1.3f;
        return Math.round(f * 100);
    }

    @Override
    public void onConfigurationChanged(Configuration newConfig) {
        super.onConfigurationChanged(newConfig);
        if (web != null) web.getSettings().setTextZoom(textZoomFor(newConfig));
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        if (requestCode != REQUEST_FILES) {
            super.onActivityResult(requestCode, resultCode, data);
            return;
        }
        Uri[] picked = null;
        if (resultCode == RESULT_OK && data != null) {
            ClipData clip = data.getClipData();
            if (clip != null && clip.getItemCount() > 0) {
                picked = new Uri[clip.getItemCount()];
                for (int i = 0; i < clip.getItemCount(); i++) picked[i] = clip.getItemAt(i).getUri();
            } else if (data.getData() != null) {
                picked = new Uri[]{data.getData()};
            }
        }
        if (fileCallback != null) fileCallback.onReceiveValue(picked);
        fileCallback = null;
    }

    // ------------------------------------------------------------------ back button

    @Override
    @SuppressWarnings("deprecation")
    public void onBackPressed() {
        if (web == null || !pageReady) {
            moveTaskToBack(true);   // still loading: step aside, as on the last back press
            return;
        }
        web.evaluateJavascript("(window.__dprBack ? window.__dprBack() : 'exit')", value -> {
            if (value != null && value.contains("handled")) return;
            moveTaskToBack(true);   // keep the app (and anything typed) as it is, just out of the way
        });
    }

    // ------------------------------------------------------------------ files opened from other apps

    @Override
    protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        setIntent(intent);
        handleIntent(intent);
    }

    @SuppressWarnings("deprecation")
    private void handleIntent(Intent intent) {
        if (intent == null) return;
        Uri file = null;
        if (Intent.ACTION_VIEW.equals(intent.getAction())) {
            file = intent.getData();
        } else if (Intent.ACTION_SEND.equals(intent.getAction())) {
            if (Build.VERSION.SDK_INT >= 33) file = intent.getParcelableExtra(Intent.EXTRA_STREAM, Uri.class);
            else file = intent.getParcelableExtra(Intent.EXTRA_STREAM);
        }
        if (file == null) return;
        pendingOpen = file;
        if (pageReady) deliverPendingFile();
    }

    private void deliverPendingFile() {
        final Uri file = pendingOpen;
        if (file == null || web == null) return;
        pendingOpen = null;
        new Thread(() -> {
            try {
                String name = displayName(file);
                byte[] bytes = readAll(file);
                final String js = "window.__dprOpenFile && window.__dprOpenFile(" + JSONObject.quote(name) + ","
                        + JSONObject.quote(Base64.encodeToString(bytes, Base64.NO_WRAP)) + ")";
                new Handler(Looper.getMainLooper()).postDelayed(() -> {
                    if (web != null) web.evaluateJavascript(js, null);
                }, 700);
            } catch (Exception e) {
                runOnUiThread(() -> toast("Couldn't open that file: " + e.getMessage()));
            }
        }).start();
    }

    private String displayName(Uri file) {
        String name = null;
        try (Cursor c = getContentResolver().query(file, new String[]{OpenableColumns.DISPLAY_NAME}, null, null, null)) {
            if (c != null && c.moveToFirst()) name = c.getString(0);
        } catch (Exception ignored) {
            // fall back to the last part of the address
        }
        if (name == null) name = file.getLastPathSegment();
        return name == null ? "file.json" : name;
    }

    private byte[] readAll(Uri file) throws IOException {
        try (InputStream in = getContentResolver().openInputStream(file)) {
            if (in == null) throw new IOException("it can't be read");
            ByteArrayOutputStream out = new ByteArrayOutputStream();
            byte[] buf = new byte[65536];
            int n, total = 0;
            while ((n = in.read(buf)) != -1) {
                total += n;
                if (total > MAX_OPEN_BYTES) throw new IOException("it's too large");
                out.write(buf, 0, n);
            }
            return out.toByteArray();
        }
    }

    // ------------------------------------------------------------------ files the portal saves

    private static String cleanName(String name) {
        String n = name == null ? "" : name.replaceAll("[\\\\/:*?\"<>|\\p{Cntrl}]", "_").trim();
        return n.isEmpty() ? "DPR file" : n;
    }

    private Uri writeDownload(String name, byte[] data, String mime) throws IOException {
        if (Build.VERSION.SDK_INT >= 29) {
            ContentResolver cr = getContentResolver();
            ContentValues values = new ContentValues();
            values.put(MediaStore.MediaColumns.DISPLAY_NAME, name);
            values.put(MediaStore.MediaColumns.MIME_TYPE, mime);
            values.put(MediaStore.MediaColumns.RELATIVE_PATH, Environment.DIRECTORY_DOWNLOADS + "/DPR Portal");
            values.put(MediaStore.MediaColumns.IS_PENDING, 1);
            Uri uri = cr.insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI, values);
            if (uri == null) throw new IOException("Downloads couldn't take the file");
            try (OutputStream os = cr.openOutputStream(uri)) {
                if (os == null) throw new IOException("Downloads couldn't take the file");
                os.write(data);
            }
            values.clear();
            values.put(MediaStore.MediaColumns.IS_PENDING, 0);
            cr.update(uri, values, null, null);
            return uri;
        }
        File dir = getExternalFilesDir(Environment.DIRECTORY_DOWNLOADS);
        if (dir == null) throw new IOException("storage isn't available");
        if (!dir.exists() && !dir.mkdirs()) throw new IOException("the folder couldn't be made");
        File out = new File(dir, name);
        try (FileOutputStream os = new FileOutputStream(out)) {
            os.write(data);
        }
        return FileProvider.getUriForFile(this, getPackageName() + ".files", out);
    }

    private void offerFile(Uri uri, String mime, String name) {
        String where = Build.VERSION.SDK_INT >= 29 ? "Downloads › DPR Portal" : "the app's Downloads folder";
        new AlertDialog.Builder(this)
                .setTitle(name)
                .setMessage("Saved to " + where + ". Send it on, or open it in another app.")
                .setPositiveButton("Share", (d, which) -> share(uri, mime, name))
                .setNeutralButton("Open", (d, which) -> open(uri, mime))
                .setNegativeButton("Done", null)
                .show();
    }

    private void share(Uri uri, String mime, String name) {
        Intent send = new Intent(Intent.ACTION_SEND);
        send.setType(mime);
        send.putExtra(Intent.EXTRA_STREAM, uri);
        send.putExtra(Intent.EXTRA_SUBJECT, name);
        send.setClipData(ClipData.newRawUri(name, uri));
        send.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
        try {
            startActivity(Intent.createChooser(send, "Send " + name));
        } catch (ActivityNotFoundException e) {
            toast("No app on this phone can send it.");
        }
    }

    private void open(Uri uri, String mime) {
        Intent view = new Intent(Intent.ACTION_VIEW);
        view.setDataAndType(uri, mime);
        view.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
        try {
            startActivity(view);
        } catch (ActivityNotFoundException e) {
            toast("No app on this phone opens this kind of file. Use Share instead.");
        }
    }

    private void printPage(String title) {
        PrintManager printer = (PrintManager) getSystemService(PRINT_SERVICE);
        if (printer == null || web == null) return;
        String job = (title == null || title.trim().isEmpty()) ? "DPR" : title.trim();
        PrintAttributes a4 = new PrintAttributes.Builder().setMediaSize(PrintAttributes.MediaSize.ISO_A4).build();
        printer.print(job, web.createPrintDocumentAdapter(job), a4);
    }

    private void toast(String message) {
        Toast.makeText(this, message, Toast.LENGTH_LONG).show();
    }

    /** What the page can ask of the phone (see android/bridge.js). Called on a background thread. */
    public class Bridge {
        @JavascriptInterface
        public String saveFile(String name, String base64, String mime) {
            try {
                final byte[] bytes = Base64.decode(base64, Base64.DEFAULT);
                final String type = (mime == null || mime.isEmpty()) ? "application/octet-stream" : mime;
                final String clean = cleanName(name);
                final Uri uri = writeDownload(clean, bytes, type);
                runOnUiThread(() -> offerFile(uri, type, clean));
                return "saved";
            } catch (Exception e) {
                return "failed: " + e.getMessage();
            }
        }

        @JavascriptInterface
        public void print(String title) {
            runOnUiThread(() -> printPage(title));
        }

        @JavascriptInterface
        public void toast(String message) {
            runOnUiThread(() -> MainActivity.this.toast(message == null ? "" : message));
        }

        @JavascriptInterface
        public String version() {
            return BuildConfig.VERSION_NAME;
        }
    }

    // ------------------------------------------------------------------ lifecycle

    @Override
    protected void onPause() {
        super.onPause();
        if (web != null) web.onPause();
    }

    @Override
    protected void onResume() {
        super.onResume();
        if (web != null) web.onResume();
    }

    @Override
    protected void onDestroy() {
        if (web != null) {
            web.destroy();
            web = null;
        }
        super.onDestroy();
    }
}
