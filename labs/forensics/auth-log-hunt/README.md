# auth-log-hunt

An sshd authentication log from a small server, two days of it, 464 lines. People log in, people mistype passwords, random names get knocked on from the internet, sessions open and close. Somewhere in those two days, one person was not a user having a bad morning. One person was working their way in, and they got in.

Author: Gavin Blacklock

## Objective

Read the log like an incident responder on their first morning: find the break in, and name exactly who did it, who they got in as, and when.

## Files

- `auth.log`: the log you have to work. Classic syslog style, `Oct 27` and `Oct 28`.
- `gen_log.py`: the generator that built the log, with a fixed seed, in case you want to rebuild it. Python 3.12 standard library only.

## Setup

No installs, and no Python for the solve. This one is shell only: `grep` and `awk`, plus the usual `sort`, `uniq`, and `wc`.

```bash
cd labs/forensics/auth-log-hunt
python3 gen_log.py   # rebuilds auth.log, optional
wc -l auth.log
```

## The task

Answer all three questions, from the log, with the commands that prove each one:

1. Which IP address carried out the brute force attack?
2. Which account did that IP finally get in with?
3. At what date and time did that successful login happen?

## Hint ladder

Hint 1, a nudge: do not read 464 lines top to bottom. Count things first. A normal user fails a login now and then. An attacker fails on a schedule, so count the failures per source IP and see who sits at the top of that list by a wide margin.

Hint 2, more specific: once you have a suspect IP, stop looking at the whole log. Filter the log to that IP alone, and look for the one line in its history that is not a failure. The account name and the time are both on that single line, in plain text.
