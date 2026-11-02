# ret2win-overflow

A first buffer overflow lab: the program has a `win()` function that
prints the flag, nothing ever calls it, and the only way in is to
overwrite a saved return address on the stack.

Author: Gavin Blacklock

## Objective

Feed the program a crafted input that lands execution in `win()` and
prints the flag: `SALVO{r3t2w1n_0v3rfl0w}`

## Files

- `vuln.c`: the source, with the bug in plain sight. Try the binary
  first if you want the honest version of the exercise.
- `build.sh`: builds the binary with the lab flags listed below.
- `vuln`: the built binary, rebuilt by `build.sh`.
- `exploit.py`: my working exploit, plain Python only.
- `WRITEUP.md`: my full solve, with the failed runs included.

## Setup and build

Environment used for the writeup: gcc 13, objdump, strings, file,
Python 3.12, running as root. There is no gdb in this environment and
the exploit uses no pwntools: it packs with `struct` and feeds the
payload through `subprocess`.

```sh
./build.sh
file vuln
```

## The build flags are deliberate

`build.sh` compiles with:

- `-fno-stack-protector`: no stack canary, so nothing checks the
  saved return address before it is used.
- `-no-pie`: the binary loads at fixed addresses, so `win()` is at
  the same address on every run.
- `-z norelro`: the classic relocation setting used for a teaching
  binary.

These flags are here so a first overflow is about the core idea, the
distance from a buffer to a return address, and nothing else. A real
target would not hand you any of this.

## The task

1. Run `./vuln` with a short input and watch it behave normally.
2. Find the address of `win()` with `nm` or `objdump`.
3. Work out the exact offset from the start of the input to the
   saved return address. Guesswork is not enough: show it with
   trials, shorter and longer than your answer.
4. Build the payload: padding up to that offset, then the address
   of `win()`, packed little endian.
5. Run `python3 exploit.py` and collect the flag.

## Hint ladder

Hint 1, small nudge: look at the disassembly of the reading function
and find where its buffer sits relative to `rbp`. That distance is
most of the offset, but it is not the whole offset. One more saved
value sits between your buffer and the return address.

Hint 2, bigger push: the buffer is 64 bytes and sits at `rbp-0x40`.
The saved `rbp` takes 8 more bytes. Try feeding the program padding
of different lengths followed by the same target address, and keep
score: which lengths crash, which lengths return quietly, and which
single length prints the flag. That table is the proof.

Hint 3 is the writeup. If you are stuck after both hints, read
`WRITEUP.md` and then close it and redo the steps yourself.
