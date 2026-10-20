"""A small stand-in for Microsoft sign-in and SharePoint (Microsoft Graph), for testing the portal's sync.

It implements just what the portal uses, the way Microsoft does it:
  - sign-in: /{tenant}/oauth2/v2.0/authorize (an account picker page; prompt=none for silent renewal)
    and /token (authorization code with PKCE, refresh tokens), with CORS for the portal's origin;
  - Graph: /shares/{id}/driveItem, items by id and by path, children listings with paging, uploads with
    If-Match, pre-signed download addresses, and 401/403/404/412/429 answers;
  - control endpoints for tests under /__ctl/ (expire tokens, end sessions, deny writes, inspect files).

  server = MockMicrosoft(); server.start(); ... server.stop()
  endpoints for the portal: {'login': server.url + '/login', 'graph': server.url + '/graph/v1.0'}
"""
import base64, hashlib, http.server, itertools, json, re, secrets, threading, time, urllib.parse

USERS = {
    'pm@demo.test': 'Priya Planner',
    'ravi@demo.test': 'Ravi Kumar',
    'site@demo.test': 'Site Office',
    'viewer@demo.test': 'Vera Viewer',
}
# ID-token claims that differ from the account name: Ravi's sign-in name (UPN) isn't his work email
CLAIMS = {
    'ravi@demo.test': {'preferred_username': 'ravi.kumar@demo.onmicrosoft.test', 'email': 'ravi@demo.test'},
}
CLIENT_ID = 'test-client'
TENANT_ID = 'tid-demo'


def b64url(b):
    return base64.urlsafe_b64encode(b).rstrip(b'=').decode()


def jwt(claims):
    head = b64url(json.dumps({'alg': 'none', 'typ': 'JWT'}).encode())
    return f"{head}.{b64url(json.dumps(claims).encode())}.sig"


class Drive:
    """One SharePoint document library, as a tree of items."""
    def __init__(self, base_url):
        self.id = 'drv-proj'
        self.base = base_url  # e.g. http://127.0.0.1:port/sites/proj/Shared Documents
        self.items = {}
        self.seq = itertools.count(1)
        self.root = self._new('Shared Documents', None, folder=True)
        self.lock = threading.RLock()

    def _new(self, name, parent, folder=False, content=b''):
        iid = f'itm{next(self.seq):04d}'
        it = {'id': iid, 'name': name, 'parent': parent, 'folder': folder, 'content': content, 'ver': 1,
              'mtime': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'by': ''}
        self.items[iid] = it
        return it

    def child(self, parent, name):
        for it in self.items.values():
            if it['parent'] == parent['id'] and it['name'].lower() == name.lower():
                return it
        return None

    def by_path(self, start, rel, create_folders=False):
        cur = start
        for part in [p for p in rel.split('/') if p]:
            nxt = self.child(cur, part)
            if not nxt:
                if not create_folders:
                    return None
                nxt = self._new(part, cur['id'], folder=True)
            cur = nxt
        return cur

    def path_of(self, it):
        parts = []
        while it and it['parent']:
            parts.append(it['name']); it = self.items[it['parent']]
        return '/'.join(reversed(parts))

    def json(self, it, server_url):
        etag = f'"{{{it["id"]}}},{it["ver"]}"'
        out = {'id': it['id'], 'name': it['name'], 'eTag': etag, 'size': len(it['content']),
               'lastModifiedDateTime': it['mtime'],
               'webUrl': self.base + '/' + urllib.parse.quote(self.path_of(it)),
               'parentReference': {'driveId': self.id, 'id': it['parent'] or ''}}
        if it['folder']:
            out['folder'] = {'childCount': sum(1 for x in self.items.values() if x['parent'] == it['id'])}
        else:
            out['cTag'] = f'"c:{{{it["id"]}}},{it["ver"]}"'
            out['file'] = {'mimeType': 'application/octet-stream'}
            out['@microsoft.graph.downloadUrl'] = f'{server_url}/dl/{it["id"]}?v={it["ver"]}&t={secrets.token_hex(4)}'
        if it['by']:
            out['lastModifiedBy'] = {'user': {'email': it['by'], 'displayName': USERS.get(it['by'], it['by'])}}
        return out


class State:
    def __init__(self):
        self.codes = {}          # code -> request
        self.access = {}         # token -> {user, exp}
        self.refresh = {}        # token -> {user, valid}
        self.sessions = set()    # users signed in at the stand-in sign-in page
        self.requests = {}       # interactive authorize requests waiting for an account choice
        self.deny = []           # (user, path prefix) that may not write
        self.fail_next = []      # statuses to answer the next Graph requests with
        self.log = []            # (method, path, user)
        self.refused = []        # (user, path) uploads refused because the file had changed (412)
        self.access_ttl = 3600


class MockMicrosoft:
    def __init__(self, host='127.0.0.1', port=0):
        self.state = State()
        handler = self._handler()
        self.httpd = http.server.ThreadingHTTPServer((host, port), handler)
        self.url = f'http://{host}:{self.httpd.server_address[1]}'
        self.drive = Drive(self.url + '/sites/proj/Shared Documents')
        self.drive.by_path(self.drive.root, 'DPR/Riverside', create_folders=True)
        self.drive.by_path(self.drive.root, 'DPR/Other project', create_folders=True)
        self.thread = None

    @property
    def endpoints(self):
        return {'login': self.url + '/login', 'graph': self.url + '/graph/v1.0'}

    def folder_link(self, rel='DPR/Riverside'):
        return self.drive.base.replace(' ', '%20') + '/' + urllib.parse.quote(rel)

    def start(self):
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True); self.thread.start(); return self

    def stop(self):
        self.httpd.shutdown()

    def files(self, under='DPR/Riverside'):
        d = self.drive
        top = d.by_path(d.root, under)
        out = {}
        for it in d.items.values():
            if it['folder']:
                continue
            p = d.path_of(it)
            if p.startswith(under + '/'):
                out[p[len(under) + 1:]] = it
        return out

    def file_json(self, rel, under='DPR/Riverside'):
        it = self.files(under).get(rel)
        return json.loads(it['content']) if it else None

    # ------------------------------------------------------------------ HTTP
    def _handler(self):
        mock = self

        class H(http.server.BaseHTTPRequestHandler):
            protocol_version = 'HTTP/1.1'

            def log_message(self, *a):
                pass

            # ---- plumbing
            def cors(self):
                o = self.headers.get('Origin')
                if o:
                    self.send_header('Access-Control-Allow-Origin', o)
                    self.send_header('Vary', 'Origin')
                self.send_header('Access-Control-Allow-Methods', 'GET, PUT, POST, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', 'Authorization, Content-Type, If-Match, Prefer')
                self.send_header('Access-Control-Max-Age', '600')

            def send(self, code, body=b'', ctype='application/json', headers=None):
                if isinstance(body, (dict, list)):
                    body = json.dumps(body).encode()
                elif isinstance(body, str):
                    body = body.encode()
                self.send_response(code)
                self.cors()
                if body or code not in (204, 302):
                    self.send_header('Content-Type', ctype)
                for k, v in (headers or {}).items():
                    self.send_header(k, v)
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                if body:
                    self.wfile.write(body)

            def redirect(self, url):
                self.send(302, b'', headers={'Location': url})

            def body(self):
                return self.payload

            def graph_error(self, code, gcode, msg):
                self.send(code, {'error': {'code': gcode, 'message': msg}})

            def do_OPTIONS(self):
                self.send(204)

            # ---- routing
            def do_GET(self):
                self.route('GET')

            def do_POST(self):
                self.route('POST')

            def do_PUT(self):
                self.route('PUT')

            def route(self, method):
                n = int(self.headers.get('Content-Length') or 0)
                self.payload = self.rfile.read(n) if n else b''
                u = urllib.parse.urlsplit(self.path)
                path, q = u.path, urllib.parse.parse_qs(u.query)
                try:
                    if path.startswith('/__ctl/'):
                        return self.control(path[7:], q)
                    if path.startswith('/login/'):
                        return self.login(method, path[7:], q)
                    if path.startswith('/dl/'):
                        it = mock.drive.items.get(path[4:])
                        if not it:
                            return self.send(404, b'gone', 'text/plain')
                        return self.send(200, it['content'], 'application/octet-stream')
                    if path.startswith('/graph/v1.0/'):
                        return self.graph(method, path[len('/graph/v1.0'):], q, u.path)
                    self.send(404, b'not found', 'text/plain')
                except Exception as e:  # noqa: BLE001
                    import traceback; traceback.print_exc()
                    self.send(500, {'error': {'code': 'mockError', 'message': str(e)}})

            # ---- sign-in
            def login(self, method, rest, q):
                st = mock.state
                m = re.match(r'([^/]+)/oauth2/v2\.0/(authorize|token|logout)$', rest)
                if rest.startswith('approve'):
                    req = st.requests.pop((q.get('rid') or [''])[0], None)
                    user = (q.get('u') or [''])[0]
                    if not req or user not in USERS:
                        return self.send(400, b'bad request', 'text/plain')
                    st.sessions.add(user)
                    return self.redirect(self.issue(req, user))
                if not m:
                    return self.send(404, b'no such sign-in endpoint', 'text/plain')
                tenant, what = m.groups()
                if what == 'logout':
                    st.sessions.clear()
                    return self.send(200, b'<p>Signed out</p>', 'text/html')
                if what == 'authorize':
                    g = lambda k: (q.get(k) or [''])[0]
                    req = {k: g(k) for k in ('client_id', 'redirect_uri', 'state', 'code_challenge', 'code_challenge_method', 'scope', 'response_mode', 'prompt', 'login_hint')}
                    if req['client_id'] != CLIENT_ID:
                        return self.redirect(req['redirect_uri'] + '#' + urllib.parse.urlencode({'error': 'unauthorized_client', 'error_description': f"AADSTS700016: Application with identifier '{req['client_id']}' was not found in the directory.", 'state': req['state']}))
                    if req['response_mode'] != 'fragment' or req['code_challenge_method'] != 'S256' or not req['code_challenge']:
                        return self.send(400, b'expects PKCE (S256) and response_mode=fragment', 'text/plain')
                    if req['prompt'] == 'none':
                        hint = req['login_hint']   # any name the account goes by
                        user = next((u for u, c in CLAIMS.items() if hint in c.values()), hint)
                        if user in st.sessions:
                            return self.redirect(self.issue(req, user))
                        return self.redirect(req['redirect_uri'] + '#' + urllib.parse.urlencode({'error': 'login_required', 'error_description': 'AADSTS50058: A silent sign-in request was sent but no user is signed in.', 'state': req['state']}))
                    rid = secrets.token_hex(6)
                    st.requests[rid] = req
                    links = ''.join(f'<li><a class="acct" data-user="{u}" href="/login/approve?rid={rid}&u={urllib.parse.quote(u)}">{n} &lt;{u}&gt;</a></li>' for u, n in USERS.items())
                    return self.send(200, f'<!doctype html><title>Sign in</title><h1>Pick an account</h1><ul>{links}</ul>', 'text/html')
                # token
                form = {k: v[0] for k, v in urllib.parse.parse_qs(self.body().decode()).items()}
                if form.get('grant_type') == 'authorization_code':
                    c = st.codes.pop(form.get('code', ''), None)
                    if not c:
                        return self.send(400, {'error': 'invalid_grant', 'error_description': 'AADSTS70008: The code has expired or was already used.'})
                    chal = b64url(hashlib.sha256(form.get('code_verifier', '').encode()).digest())
                    if chal != c['code_challenge'] or form.get('redirect_uri') != c['redirect_uri'] or form.get('client_id') != c['client_id']:
                        return self.send(400, {'error': 'invalid_grant', 'error_description': 'AADSTS501481: The code verifier does not match.'})
                    if self.headers.get('Origin') and not c['redirect_uri'].startswith(self.headers.get('Origin')):
                        return self.send(400, {'error': 'invalid_request', 'error_description': 'AADSTS9002326: Cross-origin token redemption is permitted only for the Single-Page Application client-type.'})
                    return self.send(200, self.tokens(c['user'], with_id=True))
                if form.get('grant_type') == 'refresh_token':
                    r = st.refresh.get(form.get('refresh_token', ''))
                    if not r or not r['valid']:
                        return self.send(400, {'error': 'invalid_grant', 'error_description': 'AADSTS700084: The refresh token was issued to a single page app (SPA), and therefore has a fixed, limited lifetime of 1.00:00:00, which was exceeded.'})
                    r['valid'] = False
                    return self.send(200, self.tokens(r['user'], with_id=False))
                return self.send(400, {'error': 'unsupported_grant_type'})

            def issue(self, req, user):
                code = secrets.token_hex(12)
                mock.state.codes[code] = dict(req, user=user)
                return req['redirect_uri'] + '#' + urllib.parse.urlencode({'code': code, 'state': req['state']})

            def tokens(self, user, with_id):
                st = mock.state
                at, rt = 'at-' + secrets.token_hex(10), 'rt-' + secrets.token_hex(10)
                st.access[at] = {'user': user, 'exp': time.time() + st.access_ttl}
                st.refresh[rt] = {'user': user, 'valid': True}
                out = {'token_type': 'Bearer', 'access_token': at, 'expires_in': st.access_ttl, 'refresh_token': rt, 'scope': 'Files.ReadWrite.All openid profile email'}
                if with_id:
                    out['id_token'] = jwt(dict({'name': USERS[user], 'preferred_username': user, 'oid': 'oid-' + user.split('@')[0], 'tid': TENANT_ID, 'aud': CLIENT_ID}, **CLAIMS.get(user, {})))
                return out

            # ---- Graph
            def graph(self, method, path, q, raw):
                st = mock.state
                auth = self.headers.get('Authorization', '')
                tok = st.access.get(auth[7:]) if auth.startswith('Bearer ') else None
                user = tok['user'] if tok else ''
                st.log.append((method, urllib.parse.unquote(path), user))
                if not tok or tok['exp'] < time.time():
                    return self.graph_error(401, 'InvalidAuthenticationToken', 'Access token has expired or is not yet valid.')
                if st.fail_next:
                    status = st.fail_next.pop(0)
                    return self.send(status, {'error': {'code': 'throttled', 'message': 'Too many requests'}}, headers={'Retry-After': '1'})
                d = mock.drive
                with d.lock:
                    m = re.match(r'^/shares/(u![A-Za-z0-9_-]+)/driveItem$', path)
                    if m and method == 'GET':
                        enc = m.group(1)[2:]
                        url = base64.urlsafe_b64decode(enc + '=' * (-len(enc) % 4)).decode()
                        p = urllib.parse.unquote(urllib.parse.urlsplit(url).path)
                        prefix = urllib.parse.urlsplit(d.base).path
                        if not p.startswith(prefix):
                            return self.graph_error(404, 'itemNotFound', 'The sharing link no longer exists, or you do not have permission to access it.')
                        it = d.by_path(d.root, p[len(prefix):])
                        if not it:
                            return self.graph_error(404, 'itemNotFound', 'Item not found')
                        return self.send(200, d.json(it, mock.url))
                    m = re.match(r'^/drives/([^/]+)/items/([^/:]+)(?::/(.+?):)?(/content|/children)?$', path)
                    if not m:
                        return self.graph_error(400, 'invalidRequest', 'Unsupported path ' + path)
                    drive, iid, rel, tail = m.groups()
                    rel = urllib.parse.unquote(rel or '')
                    if drive != d.id or iid not in d.items:
                        return self.graph_error(404, 'itemNotFound', 'Item not found')
                    base = d.items[iid]
                    if method == 'PUT' and tail == '/content':
                        full = (d.path_of(base) + '/' + rel).strip('/')
                        for u, pre in st.deny:
                            if u == user and full.startswith(pre):
                                return self.graph_error(403, 'accessDenied', 'Access denied. You do not have permission to perform this action or access this resource.')
                        parent_rel, _, name = rel.rpartition('/')
                        parent = d.by_path(base, parent_rel, create_folders=True)
                        it = d.child(parent, name)
                        im = self.headers.get('If-Match')
                        if im and (not it or f'"{{{it["id"]}}},{it["ver"]}"' != im):
                            st.refused.append((user, full))
                            return self.graph_error(412, 'resourceModified', 'ETag does not match current item\'s value')
                        data = self.body()
                        if it:
                            it['content'] = data; it['ver'] += 1
                        else:
                            it = d._new(name, parent['id'], content=data)
                        it['mtime'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()); it['by'] = user
                        return self.send(200 if it['ver'] > 1 else 201, d.json(it, mock.url))
                    if method != 'GET':
                        return self.graph_error(405, 'invalidRequest', 'Method not allowed')
                    it = d.by_path(base, rel) if rel else base
                    if not it:
                        return self.graph_error(404, 'itemNotFound', 'The resource could not be found.')
                    if tail == '/children':
                        kids = sorted((x for x in d.items.values() if x['parent'] == it['id']), key=lambda x: x['name'])
                        top = int((q.get('$top') or ['200'])[0]); skip = int((q.get('$skiptoken') or ['0'])[0])
                        page = kids[skip:skip + top]
                        out = {'value': [d.json(x, mock.url) for x in page]}
                        if skip + top < len(kids):
                            out['@odata.nextLink'] = f"{mock.url}/graph/v1.0{path}?$top={top}&$skiptoken={skip + top}"
                        return self.send(200, out)
                    if tail == '/content':
                        return self.redirect(d.json(it, mock.url)['@microsoft.graph.downloadUrl'])
                    return self.send(200, d.json(it, mock.url))

            # ---- control
            def control(self, what, q):
                st = mock.state
                g = lambda k: (q.get(k) or [''])[0]
                if what == 'expire-access':
                    for t in st.access.values():
                        t['exp'] = 0
                elif what == 'expire-refresh':
                    for t in st.refresh.values():
                        t['valid'] = False
                    for t in st.access.values():
                        t['exp'] = 0
                elif what == 'logout':
                    st.sessions.discard(g('u'))
                elif what == 'deny':
                    st.deny.append((g('u'), g('path')))
                elif what == 'allow':
                    st.deny = [x for x in st.deny if x[0] != g('u')]
                elif what == 'fail-next':
                    st.fail_next += [int(g('status') or 429)] * int(g('n') or 1)
                return self.send(200, {'ok': True})

        return H


if __name__ == '__main__':
    s = MockMicrosoft(port=8765).start()
    print('stand-in Microsoft at', s.url, '· folder link', s.folder_link())
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        s.stop()
