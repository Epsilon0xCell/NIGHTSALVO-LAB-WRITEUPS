# SQL Injection Login Bypass

Author: Gavin Blacklock

## Objective

Log in to a small web app without knowing the admin password. The app
checks credentials with a SQL query, and somewhere in how that query is
built there is a flaw. Find it, use it, and read the flag on the page
that only a logged in user is supposed to see.

Flag format: `SALVO{...}`

## Files

- `app.py`: the whole lab. A login app in pure Python 3.12 standard
  library, using `http.server` for the web side and `sqlite3` for the
  database. It seeds a `users` table, serves a login form at `/`, and
  answers posts to `/login`.
- `WRITEUP.md`: my full walkthrough, with the real commands I ran and
  the real output they produced.

## Setup

You need Python 3.12 and curl. Nothing to install, the app uses only
the standard library.

Start the app:

```bash
cd labs/web/sqli-login-bypass
python3 app.py
```

You should see:

```text
Listening on http://127.0.0.1:8001
```

The app runs on port **8001**. Open `http://127.0.0.1:8001/` in a
browser, or work from the terminal with curl, the way I did in the
writeup. The database file is created at `/var/tmp/sqli_login.db` and
is reseeded every time the app starts.

Stop the app with Ctrl+C when you are done.

## The Task

1. Try a normal login with a wrong password first and note what the
   app tells you.
2. Work out how the app builds its SQL query. Reading `app.py` is fair
   game in this lab, it is a training target, not a black box test.
3. Craft a login attempt that the database reads as true, no matter
   what password you send.
4. Submit it, read the welcome page, and copy the flag.

Solve it on your own machine only. This technique against a site you
do not own or have permission to test is not a lab, it is a crime.

## Hint Ladder

Hint 1, a nudge: The username and password do not stay data. They
become part of the SQL sentence the database runs. If you could add
words to that sentence, what would you want it to say?

Hint 2, more direct: A single quote in the username ends the username
string early. After that, an `OR` with a condition that is always
true, like `'1'='1'`, makes the `WHERE` clause pass for a real row.

Hint 3, nearly the answer: In SQL, `-- ` starts a comment. Put it
after your always true condition and the rest of the query, including
the password check, is ignored. Your username field carries the whole
attack, the password field can be anything.

## What a Good Run Looks Like

A failed login returns HTTP 401 and the words "Login failed". A
successful bypass returns HTTP 200, a welcome page naming the user,
and the flag in the page body.
