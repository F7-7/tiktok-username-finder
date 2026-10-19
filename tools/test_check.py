"""Offline test: serves fake profile pages locally and checks the helper's classification and safety stops."""
import json, subprocess, sys, tempfile, threading, os
from http.server import BaseHTTPRequestHandler, HTTPServer

def page(code, user=None):
    d = {'__DEFAULT_SCOPE__': {'webapp.user-detail': {'statusCode': code, **({'userInfo': {'user': {'uniqueId': user}}} if user else {})}}}
    return f'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__" type="application/json">{json.dumps(d)}</script>'

class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        n = self.path.lstrip('/@')
        if n == 'ratelimited': self.send_response(429); self.end_headers(); return
        body = {'exists': page(0, 'exists'), 'gone': page(10202), 'captcha': '<html>verify you are human</html>', 'weird': page(10221)}.get(n, page(10202))
        self.send_response(200); self.end_headers(); self.wfile.write(body.encode())

srv = HTTPServer(('127.0.0.1', 0), H); threading.Thread(target=srv.serve_forever, daemon=True).start()
base = f'http://127.0.0.1:{srv.server_port}'
here = os.path.dirname(os.path.abspath(__file__))

import importlib.util, time
spec = importlib.util.spec_from_file_location('check', os.path.join(here, 'check.py')); chk = importlib.util.module_from_spec(spec); spec.loader.exec_module(chk)
assert chk.classify(page(0, 'x'))[0] == 'taken'
assert chk.classify(page(10202))[0] == 'notfound'
assert chk.classify(page(10221))[0] == 'unknown'
assert chk.classify('<html>captcha</html>')[0] == 'unknown'
assert chk.classify('')[0] == 'unknown'
assert 'available' not in {chk.classify(page(c))[0] for c in (0, 10202, 10221, 1, None)}
assert chk.VALID.match('fa.had_1') and not chk.VALID.match('bad.') and not chk.VALID.match('a')
print('classification ok: never returns "available"')

# Safety stop: two blocks in a row end the run (uses real main with a monkeypatched sleep).
import io, contextlib
with tempfile.TemporaryDirectory() as d:
    src, out = os.path.join(d, 'n.txt'), os.path.join(d, 'o.json')
    open(src, 'w').write('exists\ngone\nratelimited\ncaptcha\nnever_reached\n')
    chk.time.sleep = lambda s: None
    sys.argv = ['check.py', src, '-o', out, '--base', base]
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf): chk.main()
    r = json.load(open(out))
    assert r['exists']['status'] == 'taken' and r['gone']['status'] == 'notfound'
    assert r['ratelimited']['status'] == 'unknown' and 'never_reached' not in r, r
    assert 'Stopping' in buf.getvalue()
    print('stops after a block and does not retry: ok')
