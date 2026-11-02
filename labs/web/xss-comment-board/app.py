#!/usr/bin/env python3
"""Intentionally vulnerable comment board for a local training lab.

Pure Python 3.12 standard library: http.server only.
Comments are stored in memory and rendered back with no sanitizing at
all, which is a stored cross site scripting flaw on purpose. Run this
only on localhost, in a throwaway environment, for learning.
"""

from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse, parse_qsl

HOST = "127.0.0.1"
PORT = 8002
STOLEN_PATH = "/var/tmp/stolen.txt"

# In memory store. Restarting the app clears the board.
COMMENTS = []

BOARD_PAGE = """<!doctype html>
<html>
<head><title>Night Salvo Comment Board</title></head>
<body>
<h1>Night Salvo Comment Board</h1>
<p>Leave a comment. Be nice. Or do not, the board will print it anyway.</p>
<form method="POST" action="/comment">
  <label>Name: <input name="name" type="text"></label><br>
  <label>Comment: <input name="comment" type="text" size="80"></label><br>
  <button type="submit">Post comment</button>
</form>
<hr>
<h2>Comments</h2>
{comments}
</body>
</html>
"""

ADMIN_PAGE = """<!doctype html>
<html>
<head><title>Admin Review</title></head>
<body>
<h1>Admin Review</h1>
<p>Every comment, rendered exactly as stored.</p>
{comments}
</body>
</html>
"""


def render_comments():
    if not COMMENTS:
        return "<p>No comments yet.</p>"
    parts = []
    for entry in COMMENTS:
        # Vulnerable on purpose: name and comment are inserted raw.
        parts.append(f"<div><strong>{entry['name']}</strong>: {entry['comment']}</div>")
    return "\n".join(parts)


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self._send(200, BOARD_PAGE.format(comments=render_comments()))
        elif parsed.path == "/admin":
            self._send(200, ADMIN_PAGE.format(comments=render_comments()))
        elif parsed.path == "/collect":
            params = dict(parse_qsl(parsed.query))
            line = "&".join(f"{k}={v}" for k, v in params.items()) or "(empty)"
            with open(STOLEN_PATH, "a", encoding="utf-8") as handle:
                handle.write(line + "\n")
            print(f"[app] /collect received: {line}", flush=True)
            self._send(200, "ok\n", content_type="text/plain; charset=utf-8")
        else:
            self._send(404, "Not found\n", content_type="text/plain; charset=utf-8")

    def do_POST(self):
        if self.path != "/comment":
            self._send(404, "Not found\n", content_type="text/plain; charset=utf-8")
            return
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8", errors="replace")
        fields = parse_qs(body)
        name = fields.get("name", ["anonymous"])[0]
        comment = fields.get("comment", [""])[0]
        COMMENTS.append({"name": name, "comment": comment})
        print(f"[app] stored comment from {name}: {comment}", flush=True)
        self._send(200, BOARD_PAGE.format(comments=render_comments()))

    def _send(self, code, body, content_type="text/html; charset=utf-8"):
        data = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, fmt, *args):
        print(f"[app] {self.address_string()} {fmt % args}", flush=True)


if __name__ == "__main__":
    server = HTTPServer((HOST, PORT), Handler)
    print(f"Listening on http://{HOST}:{PORT}", flush=True)
    server.serve_forever()
