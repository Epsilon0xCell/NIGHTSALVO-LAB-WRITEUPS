# crackme-one

A first reversing lab: recover a password from a binary when the
password itself is nowhere in the file in plain text.

Author: Gavin Blacklock

## Objective

Run the binary, work out what password it wants using only static
analysis, and get it to print the flag: `SALVO{st4t1c_4n4lys1s_w1ns}`

Static analysis means you read the binary, you do not debug it live.
No debugger is needed for this lab, and none is used in the writeup.

## Files

- `crackme.c`: the source. Reading it defeats the point, so try the
  binary first and come back here after.
- `build.sh`: builds the binary.
- `crackme`: the built binary, rebuilt by `build.sh`.
- `WRITEUP.md`: my full solve, with the commands I ran and the output
  I actually got.

## Setup and build

Environment used for the writeup: gcc 13, objdump, strings, file,
Python 3.12, running as root.

```sh
./build.sh
file crackme
```

That produces a normal, not stripped ELF. Symbols are kept on
purpose, because reading the disassembly is the lesson here.

## The task

1. Run `./crackme` and try a guess. Note what it tells you.
2. Look for the password with `strings`. Notice what is missing.
3. Disassemble the binary and find the check: what does the program
   do to each character you type before it compares it?
4. Find the stored bytes it compares against, undo the transform,
   and recover the password.
5. Run the binary with that password and collect the flag.

## Hint ladder

Hint 1, small nudge: `strings` shows you the prompt and the verdict
lines, but not the password. The password check still has to live
somewhere in the file. Look at the raw bytes in the `.rodata`
section with `objdump -s -j .rodata crackme` and ask yourself which
bytes are not readable text.

Hint 2, bigger push: in `objdump -d -M intel crackme`, read `main`
until you find a short loop. One instruction in that loop XORs your
character with a fixed number, and another XORs it with something
that changes on every pass through the loop. The loop compares the
result against bytes loaded from a fixed address. Write down that
fixed number, that changing value, and those bytes, in order.

Hint 3 is the writeup. If you are stuck after both hints, read
`WRITEUP.md` and then close it and redo the steps yourself.
