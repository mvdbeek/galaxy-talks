#!/usr/bin/env python3
"""Live-reloading dev server for the deck.

    python3 serve.py            # http://localhost:8000
    python3 serve.py 9000       # custom port

Watches slides.md / build.py / slides.css. On save it rebuilds slides.html
(when the source or builder changed) and tells the open browser tab to
reload — preserving your scroll position. The reload script is injected only
into the served page, so the committed slides.html stays clean.
"""
import http.server
import os
import re
import socketserver
import subprocess
import sys
import threading
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
WATCH = ["slides.md", "build.py", "slides.css"]   # css change = reload only
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000

_version = 0          # bumped whenever the page should reload
_lock = threading.Lock()

def _asset_mtime(rel):
    try:
        return int(os.path.getmtime(os.path.join(ROOT, rel)))
    except OSError:
        return 0


def cache_bust(html):
    """Append each asset's mtime as ?v=… so a changed file gets a fresh URL,
    defeating the browser image/CSS cache across live reloads."""
    html = re.sub(r'src="(images/[^"?]+)"',
                  lambda m: f'src="{m.group(1)}?v={_asset_mtime(m.group(1))}"', html)
    html = re.sub(r'href="(slides\.css)"',
                  lambda m: f'href="{m.group(1)}?v={_asset_mtime(m.group(1))}"', html)
    return html


RELOAD_JS = """
<script>
(function () {
  try {
    var y = sessionStorage.getItem('liveScroll');
    if (y !== null) { window.scrollTo(0, +y); sessionStorage.removeItem('liveScroll'); }
  } catch (e) {}
  var es = new EventSource('/events');
  es.onmessage = function () {
    try { sessionStorage.setItem('liveScroll', String(window.scrollY)); } catch (e) {}
    location.reload();
  };
})();
</script>
"""


def build():
    """Run build.py; return True on success."""
    r = subprocess.run([sys.executable, "build.py"], cwd=ROOT,
                       capture_output=True, text=True)
    if r.returncode == 0:
        print(r.stdout.strip())
        return True
    print("BUILD FAILED:\n" + (r.stderr or r.stdout), file=sys.stderr)
    return False


def watcher():
    """Poll mtimes; rebuild on source change, bump version on any change."""
    global _version
    mtimes = {}
    while True:
        changed_src = changed_any = False
        for f in WATCH:
            p = os.path.join(ROOT, f)
            try:
                m = os.path.getmtime(p)
            except OSError:
                continue
            if mtimes.get(f) != m:
                if f in mtimes:                     # skip the first sighting
                    changed_any = True
                    if f in ("slides.md", "build.py"):
                        changed_src = True
                    print(f"changed: {f}")
                mtimes[f] = m
        if changed_any:
            ok = build() if changed_src else True
            if ok:
                with _lock:
                    _version += 1
        time.sleep(0.3)


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=ROOT, **k)

    def log_message(self, *a):
        pass   # quiet

    def do_GET(self):
        if self.path == "/events":
            return self._events()
        if self.path in ("/", "/index.html", "/slides.html"):
            return self._page()
        return super().do_GET()

    def _page(self):
        try:
            html = open(os.path.join(ROOT, "slides.html"), encoding="utf-8").read()
        except OSError:
            self.send_error(404)
            return
        html = cache_bust(html)
        html = html.replace("</body>", RELOAD_JS + "</body>", 1)
        body = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _events(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Connection", "keep-alive")
        self.end_headers()
        with _lock:
            seen = _version
        try:
            while True:
                time.sleep(0.3)
                with _lock:
                    cur = _version
                if cur != seen:
                    seen = cur
                    self.wfile.write(b"data: reload\n\n")
                    self.wfile.flush()
                else:
                    self.wfile.write(b": ping\n\n")   # keep the socket alive
                    self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            pass


class Server(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def handle_error(self, request, client_address):
        # browser tabs drop their SSE socket on close/reload — that's normal,
        # don't dump a traceback for it
        exc = sys.exc_info()[1]
        if isinstance(exc, (BrokenPipeError, ConnectionResetError)):
            return
        super().handle_error(request, client_address)


if __name__ == "__main__":
    build()
    threading.Thread(target=watcher, daemon=True).start()
    print(f"serving http://localhost:{PORT}  (Ctrl-C to stop)")
    try:
        Server(("", PORT), Handler).serve_forever()
    except KeyboardInterrupt:
        print("\nbye")
