# NIGHTSALVO // LAB WRITEUPS

Night falls. Threats end. This is where the hands learn before the night comes.

Author: Gavin Blacklock

## What this is

This repository is my practice ground: a set of small, original,
self-contained security labs, each one built by me, solved by me, and
written up in full. It sits next to
[NIGHTSALVO-CTF-WRITEUPS](https://github.com/Epsilon0xCell/NIGHTSALVO-CTF-WRITEUPS),
where the event writeups live. The difference is simple. The CTF repo
records what I solved out in the world. This repo records the work I
built at home to get better at solving it: the vulnerable apps, the
generators, the captures, the logs, and the exploit scripts, all
included, all runnable.

Every lab was executed end to end before it was published here. If a
writeup shows a command, I ran it. If it shows output, that is what
the terminal gave back, including the attempts that failed first.

## How the labs are organized

```
labs/<category>/<lab-name>/
  README.md    the lab itself: objective, files, setup, the task, hints
  WRITEUP.md   my full worked solution, first person, real output
  ...          whatever the lab needs to run: source, generators, artifacts
```

Categories so far: web, crypto, reversing, pwn, forensics, linux,
misc. The full list is in [INDEX.md](INDEX.md).

Each lab README carries a hint ladder, at least two hints that get
more revealing as they go. Read the task, try on your own, take a
hint only when you are stuck, and open the writeup last. That order
is the whole point of a lab.

## Safety note

Every lab in this repository is an original exercise I created for
authorized local practice. The vulnerable programs are deliberately
vulnerable, the flags are invented, the logs and captures are
synthetic, and nothing here targets a real system or copies a real
event's challenge. Run the labs on machines you own, in environments
you control, and run the cleanup steps when a lab provides them. A
setuid binary or a vulnerable web app left running on a real network
is not practice anymore.

## Start here

Pick a category in [INDEX.md](INDEX.md), open that lab's README, and
work the problem before you read a word of the writeup.
