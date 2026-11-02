# Writeup: auth-log-hunt

By Gavin Blacklock

Two days of sshd logs, 464 lines, and somewhere in them a server got broken into. My job was to answer three questions from the log alone: which IP did it, which account they got in with, and at what time. No Python for this one. I set myself `grep` and `awk`, plus `sort`, `uniq`, and `wc`, because that is what you actually have on a box at 3 in the morning, so that is what I practised with.

## What I tried first, and why it was too noisy

My first move was the obvious one: pull every successful login and eyeball the list.

```text
$ grep "Accepted" auth.log | head -n 10
Oct 27 06:17:45 salvo-server sshd[1819]: Accepted password for ben from 192.168.1.45 port 55047 ssh2
Oct 27 06:32:02 salvo-server sshd[2421]: Accepted password for david from 192.168.1.47 port 47836 ssh2
Oct 27 07:04:08 salvo-server sshd[2159]: Accepted password for david from 192.168.1.47 port 42648 ssh2
Oct 27 07:14:40 salvo-server sshd[2130]: Accepted password for carmen from 198.51.100.23 port 48769 ssh2
Oct 27 08:56:15 salvo-server sshd[1808]: Accepted password for david from 192.168.1.47 port 57717 ssh2
Oct 27 08:57:06 salvo-server sshd[1827]: Accepted password for tomas from 192.168.1.49 port 42734 ssh2
Oct 27 09:52:54 salvo-server sshd[2438]: Accepted password for priya from 192.168.1.61 port 53430 ssh2
Oct 27 10:37:01 salvo-server sshd[2169]: Accepted password for ben from 192.168.1.45 port 51410 ssh2
Oct 27 11:06:31 salvo-server sshd[2361]: Accepted password for carmen from 198.51.100.23 port 45155 ssh2
Oct 27 12:30:02 salvo-server sshd[2270]: Accepted password for carmen from 198.51.100.23 port 47476 ssh2

$ grep "Accepted" auth.log | wc -l
71
```

Seventy one successes, and the first ten all look like people starting their day. The bad login is one line inside that list, with nothing on the line itself marking it as bad. An `Accepted` line only becomes suspicious when you know whose it is, so reading successes first was backwards. I needed to find the attacker from the failures, where their behaviour actually shows.

For scale, the failures:

```text
$ wc -l auth.log
464 auth.log

$ grep "Failed password" auth.log | wc -l
105
```

One hundred and five failed passwords in two days. Also too many to read raw, but failures can be counted, and counting is where an attacker cannot hide. Normal people fail because they fumbled a password. An attacker fails because guessing is the job.

## The breakthrough

So I counted failures per source IP. This needs one small piece of care: the IP is not in a fixed column. In a plain failure line it sits in a different field than in a failure line for an invalid user, because the words `invalid user` push everything two fields over. Counting a fixed field would split one attacker into two phantom sources. Instead I told `awk` to walk each line, find the word `from`, and print the field after it, since the IP always follows `from`:

```text
$ grep "Failed password" auth.log | awk '{for(i=1;i<=NF;i++) if($i=="from") print $(i+1)}' | sort | uniq -c | sort -nr | head -n 6
     47 203.0.113.47
      7 192.168.1.44
      4 198.51.100.23
      2 192.168.1.47
      2 192.168.1.45
      2 192.0.2.38
```

That is not a close call. One address, `203.0.113.47`, has 47 failures. The runner up has 7, and that one is an internal address, a person having a rough week with their own password. Forty seven failures in a tight window is a brute force run, and it is not even trying to look like anything else.

## The full solution

With a suspect IP in hand, I looked at what it had been aiming at:

```text
$ grep "203.0.113.47" auth.log | grep "Failed password" | awk '{if($9=="invalid") print $11; else print $9}' | sort | uniq -c | sort -nr
     14 priya
      6 ubuntu
      6 root
      6 admin
      5 test
      5 oracle
      5 guest
```

A spread of guesses: `root`, `admin`, `ubuntu`, `oracle`, `guest`, `test`, most of which are not real accounts on this box, and one real name, `priya`, tried 14 times, more than any other. The last stretch of the attack drops the guesses and hammers only that account:

```text
$ grep "203.0.113.47" auth.log | head -n 4
Oct 28 03:02:11 salvo-server sshd[2503]: Failed password for root from 203.0.113.47 port 52710 ssh2
Oct 28 03:02:36 salvo-server sshd[2508]: Invalid user admin from 203.0.113.47 port 58160 ssh2
Oct 28 03:02:37 salvo-server sshd[2508]: Failed password for invalid user admin from 203.0.113.47 port 58160 ssh2
Oct 28 03:02:49 salvo-server sshd[2510]: Invalid user ubuntu from 203.0.113.47 port 51854 ssh2

$ grep "203.0.113.47" auth.log | tail -n 4
Oct 28 03:14:41 salvo-server sshd[2681]: Failed password for priya from 203.0.113.47 port 60660 ssh2
Oct 28 03:14:57 salvo-server sshd[2686]: Failed password for priya from 203.0.113.47 port 47123 ssh2
Oct 28 03:15:12 salvo-server sshd[2688]: Failed password for priya from 203.0.113.47 port 42889 ssh2
Oct 28 03:17:42 salvo-server sshd[2692]: Accepted password for priya from 203.0.113.47 port 51234 ssh2
```

Then the question that settles it. Filter that one IP for the one outcome that is not a failure:

```text
$ grep "203.0.113.47" auth.log | grep "Accepted"
Oct 28 03:17:42 salvo-server sshd[2692]: Accepted password for priya from 203.0.113.47 port 51234 ssh2
```

One line, and it answers all three questions at once. Just to pull the fields out cleanly, rather than trusting my eyes:

```text
$ grep "203.0.113.47" auth.log | grep "Accepted" | awk '{print $1, $2, $3, $9, $11}'
Oct 28 03:17:42 priya 203.0.113.47
```

Fields 1 to 3 are the date and time, field 9 is the account, field 11 is the source IP, on an `Accepted` line all three sit in fixed places.

## Verified

I re-ran the checks the other way around to make sure the answer was unique, not just first:

- Failures per IP put `203.0.113.47` on top with 47, against a next highest of 7, so no other address in the log looks like a brute force source.
- That address has exactly one `Accepted` line in the whole file:

```text
$ grep "203.0.113.47" auth.log | grep -c "Accepted"
1
```

The answers, verified at the end:

- Attacker IP: `203.0.113.47`
- Compromised account: `priya`
- Successful login: `Oct 28 03:17:42`

The attack ran from 03:02 to 03:17 on Oct 28, about fifteen minutes of guessing that ended on a real account with a guessable password. The log knew everything the whole time. It just needed counting, not reading.
