# Lab: SUID PATH Hijack

- **Category:** linux
- **Difficulty:** beginner to intermediate
- **Author:** Gavin Blacklock

## Objective

A backup helper runs with root privileges through the setuid bit, but it
calls `tar` without an absolute path. Anything the helper runs, it runs
as root, and the shell decides what `tar` means by searching your PATH.
Plant a fake `tar`, get the helper to run it, and read a flag file that
only root can open.

## Files

- `helper.c`: the setuid helper source. It archives `/tmp/lab-data` by
  calling `system("tar czf /tmp/lab-backup.tgz /tmp/lab-data")`.
- `setup.sh`: builds the helper, installs it as `/usr/local/lab-helper`
  owned by root with mode 4755, creates the sample data, and writes the
  flag to `/root/lab-flag.txt` at mode 600.
- `cleanup.sh`: removes the helper, the flag, the backup, and the data.

## Setup

Run this on a throwaway machine or a disposable VM, as root:

```sh
sudo ./setup.sh
```

Setup installs the helper on the root filesystem rather than in /tmp,
on purpose: many systems mount /tmp with the `nosuid` option, which
silently ignores setuid bits there. Check your own mounts if the lab
misbehaves; the writeup tells the story of hitting exactly that wall.

## The task

Working as an unprivileged user:

1. Prove the boundary: try to read `/root/lab-flag.txt` directly.
2. Run `/usr/local/lab-helper` once with a normal PATH and confirm it
   does its real job.
3. Create a directory you control, write a fake `tar` script in it that
   prints its ids and reads the flag, and make it executable.
4. Run the helper again with your directory first in PATH.
5. Run `sudo ./cleanup.sh` when you are done.

## Hint ladder

**Hint 1:** Read `helper.c` closely. The command inside `system()`
names a tool with no directory in front of it. Who chooses which file
that name resolves to?

**Hint 2:** The shell searches the directories in PATH in order, first
match wins. If a directory you can write to comes before `/usr/bin`,
and it contains an executable file with the right name, the helper
will run yours with its own privileges.

**Hint 3:** Your fake tool does not need to do the backup at all. It
inherits the helper's effective uid. Have it run `id` and
`cat /root/lab-flag.txt`, and let the helper's error message about a
failed backup be the sound of the door closing behind you.

## Safety note

This lab is an original exercise built for authorized local practice.
Run it only on machines you own, and always run cleanup.sh afterward:
a leftover setuid binary is a real hole, not a souvenir.
