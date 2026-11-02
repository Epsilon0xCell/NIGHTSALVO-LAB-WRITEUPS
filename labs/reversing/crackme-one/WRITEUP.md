# crackme-one: my writeup

By Gavin Blacklock

This is a static analysis solve. I never attached a debugger and I
never patched a byte. I read the file, I worked out the check on
paper, and the binary handed me the flag when I typed the right
password.

## What I tried first that did not work

I built it and took the obvious guesses first.

```console
$ ./build.sh
$ echo "wrongguess" | ./crackme
Enter the password: Access denied.
```

Exit code on that run was 1. Fine, the binary works, but guessing
was never going to get anywhere.

My next hope was the cheap one: maybe the password is just sitting
in the file and `strings` will hand it to me. It did not. The
relevant lines from the real output were:

```console
$ strings crackme | grep -E "Enter the password|Access|NightSalvo"
%)<$iEnter the password: 
Access denied.
Access granted. Flag: SALVO{st4t1c_4n4lys1s_w1ns}
```

Two things to notice there. One, my search term `NightSalvo` matched
nothing on its own: grep only printed lines matching the other two
terms, so the password is not present as a readable string. Two,
that odd fragment `%)<$i` glued to the front of the prompt is real
data from the binary. It looked like junk at the time. It turned
out to be part of the answer, stored in a form I could not read at
a glance.

## Reading the check in the disassembly

Symbols are kept in this binary, so `main` is easy to find:

```console
$ objdump -d -M intel crackme
```

The early part of `main` told me the shape of the program before I
reached the check. It reads a line with `fgets`, trims it with
`strcspn`, and then, at address `0x1295`, there is this pair:

```asm
1295:  cmp    rax,0xb
1299:  je     12b1 <main+0xa8>
```

`rax` there is the return value of `strlen`, so the password is
exactly 11 characters long. Anything else gets the denial before
the real check even starts, which matched what I saw: my
`wrongguess` guess was 10 characters and still just got denied.

After that length check comes a loop. This is the part that matters,
trimmed to the instructions doing the work:

```asm
12bb:  lea    rdx,[rbp-0x50]            ; my input
12bf:  mov    rax,QWORD PTR [rbp-0x58]  ; i, the loop counter
12c3:  add    rax,rdx
12c6:  movzx  eax,BYTE PTR [rax]        ; input[i]
12c9:  mov    edx,eax
12cb:  mov    rax,QWORD PTR [rbp-0x58]  ; i again
12cf:  xor    eax,edx                   ; i ^ input[i]
12d1:  xor    eax,0x42                  ; then ^ 0x42
12d4:  mov    BYTE PTR [rbp-0x59],al    ; the transformed byte
12d7:  lea    rdx,[rip+0xd2a]           ; 2008 <expected>
12de:  mov    rax,QWORD PTR [rbp-0x58]
12e2:  add    rax,rdx
12e5:  movzx  eax,BYTE PTR [rax]        ; expected[i]
12e8:  cmp    BYTE PTR [rbp-0x59],al    ; transformed vs stored
12eb:  je     1303 <main+0xfa>          ; equal: next character
```

## The breakthrough

That loop is the whole lab. For each position `i`, the program
checks:

```text
input[i] ^ i ^ 0x42 == expected[i]
```

XOR is its own undoing. XOR both sides with the same two values and
the stored byte turns back into the password character:

```text
input[i] == expected[i] ^ i ^ 0x42
```

All I still needed was the stored bytes, and the disassembly names
their home: `expected` at `0x2008`, in `.rodata`. The symbol table
agrees:

```console
$ nm crackme | grep expected
0000000000002008 r expected
```

And the section dump shows the bytes themselves, in the first two
rows. The 11 bytes I need start right after the eight bytes at
`0x2000`:

```console
$ objdump -s -j .rodata crackme

crackme:     file format elf64-x86-64

Contents of section .rodata:
 2000 01000200 00000000 0c2a2729 32142529  .........*')2.%)
 2010 3c246945 6e746572 20746865 20706173  <$iEnter the pas
```

So the stored bytes are:

```text
0x0c, 0x2a, 0x27, 0x29, 0x32, 0x14, 0x25, 0x29, 0x3c, 0x24, 0x69
```

That also explains the junk in the strings output. Bytes like
`0x2a 0x27 0x29` are the characters `*')`, printable by accident,
while the rest of the row is not. The password was never missing.
It was encoded.

## The full solution

Eleven bytes and one short script:

```console
$ python3 -c "
stored = [0x0c, 0x2a, 0x27, 0x29, 0x32, 0x14, 0x25, 0x29, 0x3c, 0x24, 0x69]
password = ''.join(chr(b ^ 0x42 ^ i) for i, b in enumerate(stored))
print(password)
"
NightSalvo!
```

Spot check by hand, first character: `0x0c ^ 0x42 ^ 0` is `0x4e`,
which is `N`. Second: `0x2a ^ 0x42 ^ 1` is `0x69`, which is `i`.
The rest of the row follows the same way, and the result is a
password a person would actually pick, which is usually the sign
that the decoding is right and not a coincidence.

Then the moment the whole exercise exists for:

```console
$ echo "NightSalvo!" | ./crackme
Enter the password: Access granted. Flag: SALVO{st4t1c_4n4lys1s_w1ns}
```

Exit code 0 this time, against 1 for the wrong guess.

## Flag verified

```text
SALVO{st4t1c_4n4lys1s_w1ns}
```

Verified by running the built binary in this session with the
password I derived from the disassembly, not copied from the
source. The lesson I take from this one: when `strings` looks
empty, do not stop. The data is still in the file. Read the loop
that uses it, and the transform tells you how to read the data.
