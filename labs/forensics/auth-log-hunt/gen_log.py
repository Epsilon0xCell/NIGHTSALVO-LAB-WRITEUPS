#!/usr/bin/env python3
"""Generate auth.log, a realistic sshd log with one brute force hidden in it.

Fixed seed, fixed story. A few hundred lines of normal logins, scattered
single failures, and session lines. Inside that noise, one external IP
fails many times against several usernames and then gets in once,
against one real account, at one specific time.

Python 3.12 standard library only.
Author: Gavin Blacklock
"""

import os
import random
from datetime import datetime, timedelta

SEED = 20261028
HOST = "salvo-server"

ATTACKER_IP = "203.0.113.47"
VICTIM = "priya"
# The one success: Oct 28, 03:17:42. The README asks for this, it never prints it.
SUCCESS_TIME = datetime(2026, 10, 28, 3, 17, 42)

NORMAL_USERS = ["alice", "ben", "carmen", "david", "priya", "tomas"]
HOME_IPS = {
    "alice": "192.168.1.44",
    "ben": "192.168.1.45",
    "carmen": "198.51.100.23",
    "david": "192.168.1.47",
    "priya": "192.168.1.61",
    "tomas": "192.168.1.49",
}
INVALID_NAMES = ["test", "ftpuser", "user1", "postgres", "jenkins", "backup", "student", "guest1"]


def stamp(when: datetime) -> str:
    return when.strftime("%b %d %H:%M:%S")


def line(when: datetime, pid: int, message: str) -> tuple[datetime, str]:
    return (when, f"{stamp(when)} {HOST} sshd[{pid}]: {message}")


def main() -> None:
    rng = random.Random(SEED)
    events = []
    pid = 1800

    def next_pid() -> int:
        nonlocal pid
        pid += rng.randint(1, 7)
        return pid

    # Background: two days of ordinary use, Oct 27 from 06:12 to Oct 28 at 23:40.
    start = datetime(2026, 10, 27, 6, 12, 0)
    end = datetime(2026, 10, 28, 23, 40, 0)
    span_seconds = int((end - start).total_seconds())
    background_failures_per_ip = {}

    for _ in range(175):
        when = start + timedelta(seconds=rng.randrange(span_seconds))
        # Keep the attack window readable: no background events between 03:00 and 03:25 on Oct 28.
        if when.date() == datetime(2026, 10, 28).date() and when.hour == 3 and when.minute < 25:
            when += timedelta(minutes=40)
        user = rng.choice(NORMAL_USERS)
        ip = HOME_IPS[user]
        port = rng.randint(40000, 61000)
        roll = rng.random()
        this_pid = next_pid()
        if roll < 0.46:
            events.append(line(when, this_pid, f"Accepted password for {user} from {ip} port {port} ssh2"))
            events.append(
                line(
                    when + timedelta(seconds=1),
                    this_pid,
                    f"pam_unix(sshd:session): session opened for user {user} by (uid=0)",
                )
            )
            events.append(
                line(
                    when + timedelta(minutes=rng.randint(4, 55)),
                    this_pid,
                    f"pam_unix(sshd:session): session closed for user {user}",
                )
            )
        elif roll < 0.62:
            # Scattered single failures: a typo at home, or a random external knock.
            if rng.random() < 0.5:
                fail_ip = ip
            else:
                while True:
                    fail_ip = f"198.51.100.{rng.randint(30, 220)}"
                    if background_failures_per_ip.get(fail_ip, 0) < 2:
                        break
                background_failures_per_ip[fail_ip] = background_failures_per_ip.get(fail_ip, 0) + 1
            events.append(line(when, this_pid, f"Failed password for {user} from {fail_ip} port {port} ssh2"))
        elif roll < 0.74:
            bad_name = rng.choice(INVALID_NAMES)
            while True:
                fail_ip = f"192.0.2.{rng.randint(10, 200)}"
                if background_failures_per_ip.get(fail_ip, 0) < 2:
                    break
            background_failures_per_ip[fail_ip] = background_failures_per_ip.get(fail_ip, 0) + 1
            events.append(line(when, this_pid, f"Invalid user {bad_name} from {fail_ip} port {port}"))
            events.append(
                line(when + timedelta(seconds=1), this_pid, f"Failed password for invalid user {bad_name} from {fail_ip} port {port} ssh2")
            )
        else:
            events.append(
                line(when, this_pid, f"pam_unix(sshd:session): session opened for user {user} by (uid=0)")
            )
            events.append(
                line(
                    when + timedelta(minutes=rng.randint(3, 40)),
                    this_pid,
                    f"pam_unix(sshd:session): session closed for user {user}",
                )
            )

    # The story: 47 failures from one external IP, spread over about 15 minutes,
    # cycling through guessed names and landing on a real account, then one success.
    attack_start = datetime(2026, 10, 28, 3, 2, 11)
    targets = ["root", "admin", "ubuntu", "oracle", "guest", "test", VICTIM]
    cursor = attack_start
    for attempt in range(47):
        # The last stretch concentrates on the victim account.
        if attempt >= 38:
            target = VICTIM
        else:
            target = targets[attempt % len(targets)]
        port = rng.randint(40000, 61000)
        this_pid = next_pid()
        if target in NORMAL_USERS or target == "root":
            events.append(line(cursor, this_pid, f"Failed password for {target} from {ATTACKER_IP} port {port} ssh2"))
        else:
            events.append(line(cursor, this_pid, f"Invalid user {target} from {ATTACKER_IP} port {port}"))
            events.append(
                line(cursor + timedelta(seconds=1), this_pid, f"Failed password for invalid user {target} from {ATTACKER_IP} port {port} ssh2")
            )
        cursor += timedelta(seconds=rng.randint(9, 26))

    success_pid = next_pid()
    events.append(
        line(SUCCESS_TIME, success_pid, f"Accepted password for {VICTIM} from {ATTACKER_IP} port 51234 ssh2")
    )
    events.append(
        line(
            SUCCESS_TIME + timedelta(seconds=1),
            success_pid,
            f"pam_unix(sshd:session): session opened for user {VICTIM} by (uid=0)",
        )
    )

    events.sort(key=lambda item: item[0])
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "auth.log")
    with open(out_path, "w", encoding="utf-8") as handle:
        for _when, text in events:
            handle.write(text + "\n")

    print(f"wrote {out_path}: {len(events)} lines")
    print(f"attacker failures planted: 47, successes planted: 1")


if __name__ == "__main__":
    main()
