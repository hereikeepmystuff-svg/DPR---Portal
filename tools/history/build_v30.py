#!/usr/bin/env python3
"""v2.3 -> v3.0: SharePoint sync.

Applies exact, asserted replacements to src/portal.template.html and inserts src/modules/sync.js and
src/modules/sync.css. Run once from the repository root on the v2.3 template:

  python3 tools/history/build_v30.py
"""
import pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
TPL = ROOT / 'src' / 'portal.template.html'
s = TPL.read_text(encoding='utf-8')
if "const APP_VERSION = '2.3';" not in s:
    sys.exit('expected the v2.3 template')
JS = (ROOT / 'src' / 'modules' / 'sync.js').read_text(encoding='utf-8')
CSS = (ROOT / 'src' / 'modules' / 'sync.css').read_text(encoding='utf-8')


def rep(old, new, cnt=1):
    global s
    n = s.count(old)
    assert n == cnt, (n, old[:160])
    s = s.replace(old, new)


# ---------------------------------------------------------------- head: the hidden sign-in renewal frame stops at once
rep('<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">\n',
    '<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">\n'
    '<script>/* A Microsoft sign-in reply loaded in the portal\'s hidden renewal frame needs nothing else from this page. */\n'
    'if(window.self!==window.top && /[#&]state=/.test(location.hash) && /[#&](code|error)=/.test(location.hash)){ window.stop(); }</script>\n')

# ---------------------------------------------------------------- CSS
rep(':where(select, textarea, input:not([type]), input[type=text], input[type=number], input[type=date], input[type=time], input[type=month], input[type=password], input[type=search]){',
    ':where(select, textarea, input:not([type]), input[type=text], input[type=number], input[type=date], input[type=time], input[type=month], input[type=password], input[type=search], input[type=email], input[type=url]){')
rep('</style>\n</head>', CSS + '</style>\n</head>')

# ---------------------------------------------------------------- header: the sync light, version
rep('<button id="userChip" class="user-chip" type="button" hidden aria-haspopup="menu"></button>',
    '<button id="syncChip" class="sync-chip" type="button" hidden></button>\n'
    '        <button id="userChip" class="user-chip" type="button" hidden aria-haspopup="menu"></button>')
rep('title="What&rsquo;s new">v2.3</button>', 'title="What&rsquo;s new">v3.0</button>')
rep('<span class="ver">DPR Portal v2.3</span> &middot; Entries are saved in this browser; engineers&rsquo; copies stay in step through setup and entries files (Settings &rarr; Team &amp; access) &middot;',
    '<span class="ver">DPR Portal v3.0</span> &middot; Entries are saved on this device; everyone&rsquo;s copies stay in step through the project&rsquo;s SharePoint folder, or through setup and entries files (Settings &rarr; Team &amp; access) &middot;')
rep("const APP_VERSION = '2.3';", "const APP_VERSION = '3.0';")
rep("const CHANGELOG = [\n", """const CHANGELOG = [
  {v:'v3.0', date:'20 Oct 2026', items:[
    'SharePoint sync: the planning manager connects the project to a SharePoint folder once (Settings, Team & access). Site engineers join with an invite link and sign in with their Microsoft work account. From then on the setup and everyone’s entries stay in step by themselves, without setup or entries files.',
    'Works offline: entries are saved on the device first and sent when there is a connection. The light at the top shows when everything is in step, and what is waiting.',
    'After the Microsoft sign-in the portal recognises each person by their work email, so engineers need no PIN on their own phone. A shared site account still works: pick your name and enter your PIN.',
    'SharePoint permissions now back the roles: with edit access to the “entries” folder only, engineers can’t change the setup on the server either.',
    'A changed project setup reaches everyone by itself. It is applied once they have saved what they were typing, and the portal comes back to the same tab and day.',
    'Setup and entries files still work for anyone who isn’t syncing.',
    'A full data backup now carries the project’s DPR workbook too, so a backup can move a project from a portal file to the website or the app.']},
""")

# ---------------------------------------------------------------- data: removals that arrive by sync are marked, workbook from sync
rep("  if(!dry) Object.keys(tomb).forEach(id=>{ if(!store.tomb[id] || store.tomb[id].at < tomb[id].at) store.tomb[id] = tomb[id]; });",
    "  if(!dry) Object.keys(tomb).forEach(id=>{ if(!store.tomb[id] || store.tomb[id].at < tomb[id].at) store.tomb[id] = via? Object.assign({}, tomb[id], {via}) : tomb[id]; });")
BS = chr(92)   # a backslash: the v2.3 template writes these characters as JavaScript escapes
rep("  if(CFG.template && CFG.template.source==='idb'){ const b=await TPL_DB.get('template'); if(b) return new Uint8Array(b); throw new Error('The project workbook is missing from this browser "
    + BS + "u2014 re-import it from Settings " + BS + "u2192 Project workbook.'); }",
    "  if(CFG.template && CFG.template.source==='idb'){ const b=await TPL_DB.get('template'); if(b) return new Uint8Array(b); throw new Error(workbookMissingText()); }")
rep("  if(SEED.template_b64) return b64ToBytes(SEED.template_b64);\n  throw new Error('No project workbook has been imported yet.');\n}\n",
    "  if(SEED.template_b64) return b64ToBytes(SEED.template_b64);\n"
    "  if(CFG.template){ const b=await TPL_DB.get('template'); if(b) return new Uint8Array(b); throw new Error(workbookMissingText()); }   // received from SharePoint\n"
    "  throw new Error('No project workbook has been imported yet.');\n}\n"
    r"""function workbookMissingText(){
  if(ME && can('base')) return 'The project workbook file isn’t on this device. Choose it again in Settings → Workbook & periods; everything entered is kept.';
  return syncOn()? 'The project workbook hasn’t reached this device yet. Tap the sync light, choose Sync now and try again. If it still doesn’t come, ask the planning manager.'
                 : 'The project workbook isn’t on this device. Ask the planning manager for a new setup file.';
}
""")
# the workbook pane offers to re-attach a workbook whose file is missing (e.g. after restoring an older backup)
rep("""${logs.length? 'Logs: '+logs.join(', ') : ''}`;\n  }\n  renderPeriodPanel();\n}""",
    r"""${logs.length? 'Logs: '+logs.join(', ') : ''}`;
    let have = true; try{ await loadTemplateBytes(); }catch(e){ have = false; }
    if(!have && box.isConnected){
      box.insertAdjacentHTML('beforeend', '<div class="warn-banner" style="margin-top:8px;">The workbook file itself isn’t on this device, so exports can’t use it. Choose the same workbook again: everything entered is kept.</div>');
      const first = document.getElementById('openWizardBtn');
      if(first && !document.getElementById('tplAgainBtn')){
        const again = document.createElement('button'); again.type = 'button'; again.className = 'btn blue'; again.id = 'tplAgainBtn';
        again.textContent = 'Choose the workbook file again…'; again.onclick = ()=> openWizard('replace');
        first.className = 'btn secondary'; first.before(again);
        const dl = document.getElementById('downloadTplBtn'); if(dl) dl.style.display = 'none';
      }
    }
  }
  renderPeriodPanel();
}""")
# a full data backup carries the workbook however it came (built in or imported), so a backup can move a project
# from a portal file to the website or the app; restored, the workbook lives in this browser's storage
rep("    if(CFG.template && CFG.template.source==='idb'){ try{ const b=await TPL_DB.get('template'); if(b) out.templateB64 = bytesToB64(new Uint8Array(b)); }catch(e){ console.error(e); } }\n",
    "    if(CFG.template){ try{ out.templateB64 = bytesToB64(await loadTemplateBytes()); }catch(e){ console.error(e); } }   // built in or imported: the workbook travels with the backup\n")
rep("        const tplB64 = imported.templateB64; delete imported.templateB64;\n",
    "        const tplB64 = imported.templateB64; delete imported.templateB64;\n"
    "        if(tplB64 && imported.config.template) imported.config.template.source = 'idb';   // from now on the workbook lives in this browser\n")

# ---------------------------------------------------------------- sign-in screens can name another project (the join screen
# names the invite's project, not the one this device has so far)
rep("function authShell(inner){\n  const o = authOverlay();\n  const p = CFG.project||{};\n",
    "function authShell(inner, sub){\n  const o = authOverlay();\n  const p = CFG.project||{};\n")
rep("""<div class="sub">${escH(p.name||'Project')}${p.contractor? ' · '+escH(p.contractor) : ''}</div>""",
    """<div class="sub">${sub!==undefined? escH(sub) : escH(p.name||'Project')+(p.contractor? ' · '+escH(p.contractor) : '')}</div>""")

# ---------------------------------------------------------------- sign-in: recognised by the Microsoft account
rep("  ME = CFG.team? readSession() : null;\n  applyAccess();",
    "  ME = CFG.team? readSession() : null;\n"
    "  if(!ME && CFG.team){ const u = syncMatchedUser(); if(u){ ME = u; writeSession(u.id, true); } }\n"
    "  applyAccess();")
rep("  ME = null; clearSession(); setLockFlag('');\n",
    "  ME = null; clearSession(); setLockFlag('');\n"
    "  try{ sessionStorage.setItem('dpr_no_auto', '1'); }catch(e){}   // signed out on purpose: don't sign back in from the Microsoft account\n")
rep("""      <div class="choice-card"><h3>I&rsquo;m joining a project</h3><p>Open the setup file your planning manager sent, then sign in with the PIN they gave you.</p>
        <button class="btn secondary" type="button" id="wcJoin">Open setup file&hellip;</button></div>""",
    """      <div class="choice-card"><h3>I&rsquo;m joining a project</h3><p>Use the invite link your planning manager sent and sign in with your Microsoft work account. Or open the setup file they sent and sign in with your PIN.</p>
        <button class="btn blue" type="button" id="wcJoinLink">Join with invite link&hellip;</button>
        <button class="btn secondary" type="button" id="wcJoin">Open setup file&hellip;</button></div>""")
rep("  o.querySelector('#wcJoin').onclick = joinFromSetupFile;\n",
    "  o.querySelector('#wcJoin').onclick = joinFromSetupFile;\n  o.querySelector('#wcJoinLink').onclick = joinWithLinkDialog;\n")
rep("""    <p class="auth-q">Who&rsquo;s signing in?</p>
    <div class="user-tiles">""",
    """    <p class="auth-q">Who&rsquo;s signing in?</p>
    ${syncSignInNote()}
    <div class="user-tiles">""")
rep("""      <button class="linkbtn" type="button" id="authJoin">Open a setup file&hellip;</button>
    </div>`);""",
    """      <button class="linkbtn" type="button" id="authJoin">Open a setup file&hellip;</button>
      ${syncOn() && canSyncHere() && !msAccount()? '<button class="linkbtn" type="button" id="authMs">Sign in with Microsoft</button>' : ''}
    </div>`);""")
rep("  o.querySelector('#authJoin').onclick = joinFromSetupFile;\n",
    "  o.querySelector('#authJoin').onclick = joinFromSetupFile;\n"
    "  if(o.querySelector('#authMs')) o.querySelector('#authMs').onclick = ()=> msSignInSaved('resume');\n")

# ---------------------------------------------------------------- menu and my account
rep("""    items.push(['My account', ()=>{ openSettingsOverlay(); renderMyAccount(); }]);\n""",
    """    items.push(['My account', ()=>{ openSettingsOverlay(); renderMyAccount(); }]);\n    if(syncOn()) items.push(['SharePoint sync…', openSyncPanel]);\n""")
rep("""  } else {
    items.push(['Sign in', ()=> signOut(true)]);""",
    """  } else {
    if(syncOn()) items.push(['SharePoint sync…', openSyncPanel]);
    items.push(['Sign in', ()=> signOut(true)]);""")
rep("""      <p class="hint">Save your daily entries as a file and send it to the planning manager (email, WhatsApp or a shared folder). They import it into the master copy; sending the same days again is safe.</p>""",
    """      <p class="hint">${syncOn()? 'SharePoint sync is on, so your entries reach the planning manager by themselves. A file is only needed for someone who isn’t syncing.' : 'Save your daily entries as a file and send it to the planning manager (email, WhatsApp or a shared folder). They import it into the master copy; sending the same days again is safe.'}</p>""")
rep("""      <p class="hint">When the planning manager changes the BOQ, plan, pours or team, they send a new setup file. Open it here; your entries are kept.</p>""",
    """      <p class="hint">${syncOn()? 'Changes the planning manager makes to the BOQ, plan, pours or team arrive by themselves.' : 'When the planning manager changes the BOQ, plan, pours or team, they send a new setup file. Open it here; your entries are kept.'}</p>""")
rep("""      <span class="hint" style="margin-left:10px;">Setup on this device: ${escH(CFG.updatedAt? whenText(CFG.updatedAt) : 'not dated')}</span>
    </div>""",
    """      <span class="hint" style="margin-left:10px;">Setup on this device: ${escH(CFG.updatedAt? whenText(CFG.updatedAt) : 'not dated')}</span>
    </div>
    ${syncOn()? `<div class="settings-section">
      <h4>SharePoint sync</h4>
      <p class="hint">${msAccount()? 'Signed in to Microsoft as '+escH(msAccount().username)+'.' : 'Not signed in to Microsoft on this device.'} ${syncState().lastOk? 'Last in step '+escH(whenText(syncState().lastOk))+'.' : ''}</p>
      <button class="btn secondary" type="button" id="maSync">SharePoint sync&hellip;</button>
    </div>` : ''}""")
rep("""      <button class="btn secondary" type="button" id="maPw">Change my ${u.pin? 'PIN' : 'password'}</button>""",
    """      ${syncOn() && u.role!=='pm'? '<span class="hint" style="margin-right:10px;">Your PIN is set by the planning manager.</span>' : `<button class="btn secondary" type="button" id="maPw">Change my ${u.pin? 'PIN' : 'password'}</button>`}""")
rep("  if(b('maPw')) b('maPw').onclick = changeMyPassword;\n",
    "  if(b('maPw')) b('maPw').onclick = changeMyPassword;\n  if(b('maSync')) b('maSync').onclick = openSyncPanel;\n")

# ---------------------------------------------------------------- team & access
rep("""  box.innerHTML = `
    <div class="settings-section first">
      <h4>People</h4>""",
    """  box.innerHTML = `${syncTeamHtml()}
    <div class="settings-section">
      <h4>People</h4>""")
rep("Each person signs in with their own PIN or password, and every saved entry records who made it.</p>",
    "Each person signs in with their own PIN or password${syncOn()? ', or simply with their Microsoft work account once their work email is added' : ''}, and every saved entry records who made it.</p>")
rep("""          <td><div class="person">${avatarHtml(u)}<b>${escH(u.name)}</b>${ME && u.id===ME.id? ' <span class="you">you</span>' : ''}</div></td>""",
    """          <td><div class="person">${avatarHtml(u)}<b>${escH(u.name)}</b>${ME && u.id===ME.id? ' <span class="you">you</span>' : ''}</div>${u.email? `<span class="team-email">${escH(u.email)}</span>` : ''}</td>""")
rep("""      <p class="hint">These rules are checked in the browser, so they keep people to their job rather than stop someone set on getting around them. Moved to a shared backend such as SharePoint, the same three roles become server-enforced groups.</p>""",
    """      <p class="hint">${syncOn()? 'These rules are checked in the portal, and with SharePoint sync on the folder’s permissions enforce them on the server too: give site engineers edit access to the “entries” folder only, and only planning managers can change the setup.' : 'These rules are checked in the browser, so they keep people to their job rather than stop someone set on getting around them. With SharePoint sync on, the project folder’s permissions enforce them on the server too.'}</p>""")
rep("""      <p class="hint">Each engineer works on their own copy of this portal (this same file, or the shared link). Files keep the copies in step: you send the setup out, engineers send their entries back.</p>""",
    """      ${syncOn()? '<p class="hint"><b>SharePoint sync is on, so these files aren’t needed.</b> They still work for anyone who isn’t syncing.</p>' : ''}<p class="hint">Each engineer works on their own copy of this portal (this same file, or the shared link). Files keep the copies in step: you send the setup out, engineers send their entries back.</p>""")
rep("""  const b = id=> document.getElementById(id);
  b('tmAdd').onclick = ()=> personDialog(null);""",
    """  const b = id=> document.getElementById(id);
  syncTeamWire();
  b('tmAdd').onclick = ()=> personDialog(null);""")
rep("""    <label class="dlg-field"><span>Name</span><input id="pfName" type="text" value="${escH(cur.name)}" autocomplete="off"></label>""",
    """    <label class="dlg-field"><span>Name</span><input id="pfName" type="text" value="${escH(cur.name)}" autocomplete="off"></label>
    <label class="dlg-field"><span>Work email <small>(for Microsoft sign-in, optional)</small></span><input id="pfEmail" type="email" value="${escH(cur.email||'')}" autocomplete="off" placeholder="name@company.com"></label>""")
rep("""      if(!name) return 'Enter a name.';\n""",
    """      if(!name) return 'Enter a name.';
      const em = node.querySelector('#pfEmail').value.trim().toLowerCase();
      if(em && !/^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/.test(em)) return 'That email doesn’t look right.';
      if(em && teamUsers().some(x=> (x.email||'').toLowerCase()===em && (!u || x.id!==u.id))) return 'Someone on the team already has that email.';\n""")
rep("""  Object.assign(rec, {name, role:rr, towers: rr==='engineer'? towers : [], siteWide: rr==='engineer'? node.querySelector('#pfSite').checked : true});\n""",
    """  Object.assign(rec, {name, role:rr, towers: rr==='engineer'? towers : [], siteWide: rr==='engineer'? node.querySelector('#pfSite').checked : true});
  rec.email = node.querySelector('#pfEmail').value.trim().toLowerCase();\n""")
rep("They sign in with it on their own copy after opening your setup file. Send a new setup file so their copy knows about this change.`, isNew? name+' added' : 'Sign-in changed');",
    "${syncOn()? (rec.email? 'On their own phone they simply sign in with their Microsoft work account ('+rec.email+'); the '+(rec.pin? 'PIN' : 'password')+' is for shared devices. The change reaches everyone by itself.' : 'They sign in with it after joining with the invite link. The change reaches everyone by itself.') : 'They sign in with it on their own copy after opening your setup file. Send a new setup file so their copy knows about this change.'}`, isNew? name+' added' : 'Sign-in changed');")

# ---------------------------------------------------------------- the module, and starting it
rep('\nfunction renderAll(){\n', '\n' + JS + '\nfunction renderAll(){\n')
rep("setTimeout(()=>{ ensureTemplate().then(t=>{ if(t) renderPeriodBadge(); }).catch(err=> console.error(err)); }, 400);\n</script>",
    "setTimeout(()=>{ ensureTemplate().then(t=>{ if(t) renderPeriodBadge(); }).catch(err=> console.error(err)); }, 400);\nsyncBoot();\n</script>")

TPL.write_text(s, encoding='utf-8')
print(f'wrote {TPL} (v3.0, {len(s):,} chars)')
