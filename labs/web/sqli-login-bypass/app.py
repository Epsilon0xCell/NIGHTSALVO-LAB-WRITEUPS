#!/usr/bin/env python3
"""Intentionally vulnerable login app for a local training lab.

Pure Python 3.12 standard library: http.server plus sqlite3.
The login query is built with string formatting on purpose, so it is
genuinely injectable. Run this only on localhost, in a throwaway
environment, for learning.
"""

import sqlite3
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs

HOST = "127.0.0.1"
PORT = 8001
FLAG = "SALVO{sql_1nj3ct10n_club}"
DB_PATH = "/var/tmp/sqli_login.db"

LOGIN_PAGE = """<!doctype html>
<html>
<head><title>Night Salvo Login</title></head>
<body>
<h1>Night Salvo Login</h1>
<p>Members only. Sign in to enter.</p>
<form method="POST" action="/login">
  <label>Username: <input name="username" type="text"></label><br>
  <label>Password: <input name="password" type="password"></label><br>
  <button type="submit">Log in</button>
</form>
</body>
</html>
"""

SUCCESS_PAGE = """<!doctype html>
<html>
<head><title>Welcome</title></head>
<body>
<h1>Welcome, {username}</h1>
<p>You are in. Here is the flag you earned:</p>
<p><strong>{flag}</strong></p>
</body>
</html>
"""

FAIL_PAGE = """<!doctype html>
<html>
<head><title>Login failed</title></head>
<body>
<h1>Login failed</h1>
<p>Invalid username or password.</p>
<p><a href="/">Try again</a></p>
</body>
</html>
"""


def seed_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS users")
    cur.execute(
        "CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT, password TEXT)"
    )
    cur.execute(
        "INSERT INTO users (username, password) VALUES (?, ?)",
        ("admin", "s3cr3t_n0t_gu3ssable"),
    )
    cur.execute(
        "INSERT INTO users (username, password) VALUES (?, ?)",
        ("guest", "guest123"),
    )
    conn.commit()
    conn.close()


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self._send(200, LOGIN_PAGE)
        else:
            self._send(404, "Not found\n")

    def do_POST(self):
        if self.path != "/login":
            self._send(404, "Not found\n")
            return
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8", errors="replace")
        fields = parse_qs(body)
        username = fields.get("username", [""])[0]
        password = fields.get("password", [""])[0]

        # Vulnerable on purpose: user input goes straight into the query.
        query = (
            f"SELECT * FROM users WHERE username = '{username}' "
            f"AND password = '{password}'"
        )
        print(f"[app] query: {query}", flush=True)

        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        try:
            cur.execute(query)
            row = cur.fetchone()
        except sqlite3.Error as exc:
            print(f"[app] sql error: {exc}", flush=True)
            row = None
        conn.close()

        if row:
            self._send(200, SUCCESS_PAGE.format(username=row[1], flag=FLAG))
        else:
            self._send(401, FAIL_PAGE)

    def _send(self, code, body):
        data = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, fmt, *args):
        print(f"[app] {self.address_string()} {fmt % args}", flush=True)


if __name__ == "__main__":
    seed_db()
    server = HTTPServer((HOST, PORT), Handler)
    print(f"Listening on http://{HOST}:{PORT}", flush=True)
    server.serve_forever()
