# Writeup: Repeating-Key XOR

Author: Gavin Blacklock
Category: Crypto
Lab: `repeating-xor`

## The Challenge

I was given one line of hex in `cipher.hex`:

```text
187235777630414a510a7f47484f5e14584a5866390009120d3f4026104d3800154744
```

That is 35 bytes of ciphertext. I knew the plaintext was a flag in
the usual format, so it starts with `SALVO{` and ends with `}`. I
did not know the key, its length, or anything else.

## What I Tried First, and Why It Did Not Work

I started with the cheapest idea: maybe it is a single-byte XOR.
One byte keys are quick to brute force, all 256 of them, so I tried
every one and scored the results by how many printable characters
came out:

```python
with open("cipher.hex") as f:
    cipher = bytes.fromhex(f.read().strip())
best = []
for k in range(256):
    plain = bytes(b ^ k for b in cipher)
    printable = sum(1 for b in plain if 32 <= b < 127)
    best.append((printable, k, plain))
best.sort(reverse=True)
for printable, k, plain in best[:3]:
    print(f"key {k:#04x}: printable {printable}/{len(cipher)} -> {plain!r}")
print("any single-byte key gives the flag:",
      any(p == b"SALVO{r3p34t1ng_k3y_r3p34ts_1ts3lf}" for _, _, p in best))
```

Real output from that run:

```text
key 0x7e: printable 30/35 -> b'f\x0cK\t\x08N?4/t\x01961 j&4&\x18G~wlsA>Xn3F~k9:'
key 0x7d: printable 30/35 -> b'e\x0fH\n\x0bM<7,w\x02:52#i%7%\x1bD}topB=[m0E}h:9'
key 0x7c: printable 30/35 -> b'd\x0eI\x0b\nL=6-v\x03;43"h$6$\x1aE|unqC<Zl1D|i;8'
any single-byte key gives the flag: False
```

Garbage, all of it. The printable counts look tempting at a glance,
30 out of 35, but there is no English and no flag prefix anywhere in
the full 256 results. A single repeated byte would also have made
the first ciphertext byte XOR to `S`, the second to `A`, and so on
with the same key byte, which is impossible unless the key stream
changes. So the key changes position by position. That pointed at a
multi-byte key repeating on a cycle.

## The Breakthrough

XOR undoes itself, and that gives away key bytes wherever the
plaintext is known:

```text
cipher = plain XOR key   means   key = cipher XOR plain
```

I know the first 6 plaintext bytes: `SALVO{`. XORing them against
the first 6 ciphertext bytes gives the first 6 bytes of the key
stream, no guessing involved. Then I tested which periods fit that
stream:

```python
with open("cipher.hex") as f:
    cipher = bytes.fromhex(f.read().strip())
known = b"SALVO{"
stream = bytes(c ^ p for c, p in zip(cipher[:6], known))
print("key stream from known prefix:", stream)
for period in range(1, 7):
    ok = all(stream[i] == stream[i % period] for i in range(len(stream)))
    print(f"period {period}: consistent with the 6 known bytes -> {ok}")
```

Real output from that run:

```text
key stream from known prefix: b'K3y!9K'
period 1: consistent with the 6 known bytes -> False
period 2: consistent with the 6 known bytes -> False
period 3: consistent with the 6 known bytes -> False
period 4: consistent with the 6 known bytes -> False
period 5: consistent with the 6 known bytes -> True
period 6: consistent with the 6 known bytes -> True
```

That stream, `K3y!9K`, is the breakthrough on one line. The sixth
byte repeats the first: position 0 and position 5 both give `K`
(0x4b). Periods 1 to 4 all contradict the stream. Period 5 fits, and
it is the smallest period that does.

One honest note on period 6: it shows `True` for a boring reason.
A period equal to the window length makes no prediction inside the
window, so nothing can contradict it. It carries no evidence. The
evidence is the repeat at distance 5, and the proof is what comes
next: if period 5 were wrong, decrypting the remaining 29 bytes
with it would produce junk. It did not.

Because the key is 5 bytes and the known prefix is 6 bytes, the
prefix covered the whole key with one byte to spare, and that spare
byte was the consistency check. No bytes were left to hunt for. If
the key had been longer than the prefix, I would have had key bytes
still missing after this stage, and I would have gone after them
with frequency counts on each remaining key position and printable
continuation tests. Here the period check closed that gap before it
opened.

## The Full Solution

`solve.py` does both stages: derive the key from the known prefix,
find the smallest consistent period, then decrypt everything and
verify by re-encryption.

```python
#!/usr/bin/env python3
"""Solver for the repeating-xor lab.

Stage 1: use the known flag prefix b"SALVO{" as known plaintext.
XORing it against the first ciphertext bytes gives the key stream
for those positions. If the key repeats inside that window, the
repeated key byte shows up twice and identical, which pins the
key length down.

Stage 2: with the full key known, XOR the whole ciphertext with
the repeating key and read the flag.

Pure standard library only.
"""

KNOWN_PREFIX = b"SALVO{"


def xor_with_key(data, key):
    return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))


def find_period(key_stream):
    """Smallest period p such that key_stream repeats with period p
    everywhere the window lets us check, or None if no p smaller
    than the window works."""
    for p in range(1, len(key_stream)):
        if all(
            key_stream[i] == key_stream[i % p]
            for i in range(len(key_stream))
        ):
            return p
    return None


def main():
    with open("cipher.hex") as f:
        cipher = bytes.fromhex(f.read().strip())
    print(f"cipher length = {len(cipher)} bytes")

    # Stage 1: known plaintext gives the key stream for 6 positions.
    key_stream = bytes(
        c ^ p for c, p in zip(cipher[: len(KNOWN_PREFIX)], KNOWN_PREFIX)
    )
    print(f"known prefix     = {KNOWN_PREFIX!r}")
    print(f"key stream[0:6]  = {key_stream!r}")
    print(f"key stream hex   = {key_stream.hex()}")

    period = find_period(key_stream)
    print(f"smallest consistent period = {period}")
    print(
        "position 0 and position 5 use the same key byte: "
        f"{key_stream[0]:#04x} == {key_stream[5]:#04x} -> "
        f"{key_stream[0] == key_stream[5]}"
    )
    assert period is not None, "no repeating period found in the window"

    key = key_stream[:period]
    print(f"recovered key    = {key!r} (length {len(key)})")

    # Stage 2: decrypt everything with the repeating key.
    plain = xor_with_key(cipher, key)
    print(f"recovered: {plain.decode()}")

    # Verification: re-encrypting must reproduce the exact ciphertext.
    check = xor_with_key(plain, key)
    print(f"re-encryption matches cipher.hex: {check == cipher}")
    assert check == cipher
    assert plain.startswith(KNOWN_PREFIX) and plain.endswith(b"}")


if __name__ == "__main__":
    main()
```

## Running It

```bash
$ python3 solve.py
cipher length = 35 bytes
known prefix     = b'SALVO{'
key stream[0:6]  = b'K3y!9K'
key stream hex   = 4b337921394b
smallest consistent period = 5
position 0 and position 5 use the same key byte: 0x4b == 0x4b -> True
recovered key    = b'K3y!9' (length 5)
recovered: SALVO{r3p34t1ng_k3y_r3p34ts_1ts3lf}
re-encryption matches cipher.hex: True
```

The recovered key is `K3y!9`, 5 bytes: an uppercase letter, a digit,
a lowercase letter, a symbol, and a digit.

## Verification and Flag

The solve re-encrypts the recovered plaintext with the recovered
key and compares it byte for byte with the ciphertext from
`cipher.hex`. That check printed `True`. It also asserts the
plaintext starts with `SALVO{` and ends with `}`, and it does.

Flag: `SALVO{r3p34t1ng_k3y_r3p34ts_1ts3lf}`

The lesson I took from this one: a repeating key is only as strong
as its shortest unknown stretch. Six known bytes at the front were
enough to hand me the entire key, repeat included. Known plaintext
is not a small leak in a system like this. It is the whole key,
delivered in order.
