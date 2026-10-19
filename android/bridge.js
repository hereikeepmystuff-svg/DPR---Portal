/* DPR Portal: Android app bridge.
   android/prepare_assets.py adds this file to the copy of the portal packed into the Android app.
   In a normal browser window.DPRAndroid doesn't exist, so it does nothing.

   It hands the jobs a WebView can't do on its own to the native side (MainActivity.Bridge):
   saving files, printing and the back button. It also opens setup and entries files that arrive
   from other apps, and tunes the page for touch and for every screen size from small phones to
   tablets. */
(function(){
  'use strict';
  var A = window.DPRAndroid;
  if(!A) return;
  document.documentElement.classList.add('in-app');

  /* ---------- touch and screen sizes ---------- */
  var css = [
    'html{-webkit-text-size-adjust:100%; text-size-adjust:100%; -webkit-tap-highlight-color:transparent;}',
    'html, body{overscroll-behavior-y:none;}',
    '.tab, .subtab, .btn, .dchip, .pill-group button, .set-tabs button, .user-chip, .ver-pill, .gear-btn, .step-btn, .user-tile, .linkbtn{-webkit-user-select:none; user-select:none;}',
    '.dlg{max-height:calc(100vh - 32px); max-height:calc(100dvh - 32px);}',
    /* fingers need bigger targets than a mouse */
    '@media (pointer:coarse){',
    '  .tab{padding:11px 16px;} .subtab{padding:9px 15px;} .set-tabs button{padding:10px 14px;}',
    '  .btn{min-height:42px;} .btn.ghost{min-height:36px;} .step-btn{width:40px; height:40px;}',
    '  .dchip{min-height:36px;} .row-x{display:inline-block; padding:8px 10px;}',
    '  .menu-pop button{padding:13px 14px;} .pill-group button{padding:9px 14px;}',
    '  input[type=checkbox], input[type=radio]{width:20px; height:20px;}',
    '}',
    /* phones */
    '@media (max-width:600px){',
    '  .brand-block h1{font-size:22px;} .brand-mark{width:46px; height:46px;}',
    '  .settings-overlay{padding:10px 8px;}',
    '  .settings-panel{padding:20px 14px 24px; border-radius:20px;}',
    '  .set-savebar{margin:22px -14px -24px; padding:12px 14px 14px; border-radius:0 0 20px 20px;}',
    '  .dlg{padding:20px 18px 18px; border-radius:20px;}',
    '  .dlg-actions{gap:10px;} .dlg-actions .btn{flex:1 1 auto;}',
    '  .card{padding:16px 14px;} .controls{padding:12px 14px;}',
    '}',
    /* the DPR report is laid out for A4: on a phone each section scrolls sideways on its own,
       so the page itself never does */
    '@media screen and (max-width:700px){',
    '  .dpr-sheet{padding:20px 16px; border-radius:16px;}',
    '  .dpr-kv{grid-template-columns:repeat(2, minmax(0,1fr)); gap:12px 14px;}',
    '  .dpr-sheet .dpr-section{overflow-x:auto; -webkit-overflow-scrolling:touch;}',
    '}',
    /* phones held sideways: little height, so the header gets out of the way */
    '@media (orientation:landscape) and (max-height:520px){',
    '  header.top{margin-bottom:10px; gap:8px 16px;} .brand-mark, .brand-block .sub, #clockLine{display:none;}',
    '  .brand-block h1{font-size:20px;} .controls{padding:10px 14px; margin-bottom:12px;}',
    '  .panel{padding-top:12px;} .tabs{padding:5px;}',
    '}',
    /* Android printing renders the page as it is: keep floating controls off the paper */
    '@media print{ .fab-save, .menu-pop, #authOverlay{display:none !important;} }'
  ].join('\n');
  var style = document.createElement('style'); style.id = 'appStyle'; style.textContent = css;
  document.head.appendChild(style);

  /* keep the chosen tab in view when the tab bar scrolls sideways */
  document.addEventListener('click', function(e){
    var t = e.target.closest && e.target.closest('.tab, .subtab, .set-tabs button');
    if(t && t.scrollIntoView) t.scrollIntoView({block:'nearest', inline:'nearest'});
  }, true);

  /* ---------- saving files: Downloads, then open or share ---------- */
  function toBase64(blob){
    return blob.arrayBuffer().then(function(buf){
      var u8 = new Uint8Array(buf), s = '';
      for(var i = 0; i < u8.length; i += 0x8000) s += String.fromCharCode.apply(null, u8.subarray(i, i + 0x8000));
      return btoa(s);
    });
  }
  window.saveFile = function(filename, data, mime){
    var blob = (data instanceof Blob)? data : new Blob([data], {type: mime || 'application/octet-stream'});
    var type = blob.type || mime || 'application/octet-stream';
    if(/\.xlsx$/i.test(filename)) type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet';
    else if(/\.json$/i.test(filename)) type = 'application/json';
    else if(/\.csv$/i.test(filename)) type = 'text/csv';
    return toBase64(blob).then(function(b64){
      var r = String(A.saveFile(String(filename), b64, type) || '');
      if(r === 'saved') return 'saved';
      if(typeof uiAlert === 'function') uiAlert(r.replace(/^failed:\s*/, '') || 'The phone did not save the file.', 'File not saved');
      return 'failed';
    }).catch(function(err){
      if(typeof uiAlert === 'function') uiAlert('The file could not be prepared: ' + (err && err.message || err), 'File not saved');
      return 'failed';
    });
  };

  /* ---------- printing (the DPR's print styles apply, so only the report is printed) ---------- */
  window.print = function(){
    var name = (typeof CFG !== 'undefined' && CFG.project && CFG.project.name) || 'Project';
    var d = document.getElementById('dateInput');
    A.print(name + ' DPR ' + (d && d.value || ''));
  };

  /* ---------- the back button: close what's open, then go back to Progress, then leave ---------- */
  function shown(id){ var el = document.getElementById(id); return el && !el.hidden ? el : null; }
  function locked(){ var o = shown('authOverlay'); return !!(o && o.classList.contains('lock')); }
  function note(msg, title){
    if(locked()){ if(A.toast) A.toast(msg); return; }   // the lock screen sits above the portal's dialogs
    if(typeof uiAlert === 'function') uiAlert(msg, title);
  }
  window.__dprBack = function(){
    if(locked()) return 'exit';                         // nothing behind the lock screen is closed
    if(document.querySelector('.dlg-overlay')){
      document.dispatchEvent(new KeyboardEvent('keydown', {key:'Escape', bubbles:true}));
      return 'handled';
    }
    if(document.getElementById('userMenu') && typeof closeUserMenu === 'function'){ closeUserMenu(); return 'handled'; }
    if(document.getElementById('popMenu') && typeof closePopMenu === 'function'){ closePopMenu(); return 'handled'; }
    var settings = document.getElementById('settingsOverlay');
    if(settings && settings.style.display === 'flex' && typeof closeSettings === 'function'){ closeSettings(); return 'handled'; }
    if(shown('authOverlay')) return 'exit';
    var active = document.querySelector('.tab.active');
    if(active && active.dataset.tab !== 'entry'){
      var entry = document.querySelector('.tab[data-tab="entry"]');
      if(entry){ entry.click(); window.scrollTo(0, 0); return 'handled'; }
    }
    if(window.scrollY > 200){ window.scrollTo({top:0, behavior:'smooth'}); return 'handled'; }
    return 'exit';
  };

  /* ---------- setup and entries files opened from WhatsApp, email or a file manager ---------- */
  /* The portal's own "Open setup file" and "Import entries files" flows run as usual; their file
     picker just returns the file that arrived instead of asking. Both ask for the file before
     their first pause, so a file that isn't taken straight away is dropped, never handed to a
     later, unrelated pick. */
  var waiting = null;
  if(typeof window.pickFile === 'function'){
    var pick = window.pickFile;
    window.pickFile = function(accept, multiple){
      if(waiting){ var f = waiting; waiting = null; return Promise.resolve(f); }
      return pick(accept, multiple);
    };
  }
  function openWith(flow, file){
    waiting = [file];
    try{ flow(); } finally { waiting = null; }
  }
  window.__dprOpenFile = function(name, b64){
    var bin = atob(b64), u8 = new Uint8Array(bin.length);
    for(var i = 0; i < bin.length; i++) u8[i] = bin.charCodeAt(i);
    var file = new File([u8], name || 'file.json', {type:'application/json'});
    var kind = '', json = null;
    try{ json = JSON.parse(new TextDecoder().decode(u8)); kind = (json && json.kind) || ''; }catch(e){ json = null; }
    if(!kind && json && json.config && json.config.items) kind = 'backup';   // a full data backup is the stored data as it is
    if(locked()){ note('Unlock the portal, then open the file again.'); return; }
    if(document.querySelector('.dlg-overlay')){
      note('Finish or close what is open in the portal, then open the file again.', 'Busy');
      return;
    }
    if(kind === 'dpr-setup'){ openWith(joinFromSetupFile, file); return; }
    if(kind === 'dpr-entries'){
      if(!(typeof can === 'function' && can('import'))){
        note('Entries files are imported by a planning manager. Sign in as one, then open the file again.', 'Entries file');
        return;
      }
      openWith(importEntriesFiles, file); return;
    }
    if(kind === 'backup'){
      note('This is a full data backup. A planning manager restores it in Settings \u2192 Data \u2192 Import full data backup.', 'Data backup');
      return;
    }
    note('The DPR Portal opens its own setup and entries files. This file isn\u2019t one of them.', 'Can\u2019t open this file');
  };
})();
