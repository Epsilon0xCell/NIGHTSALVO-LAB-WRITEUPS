# Writeup: RSA, Small Exponent

Author: Gavin Blacklock
Category: Crypto
Lab: `rsa-small-exponent`

## The Challenge

I was given `challenge.txt` with three values and nothing else:

```text
n = 83019530536392896221650836162095003212132627070327687231182639560686810180587566093615131270403754434207763422753207127627795287447627902926839945716074380351117432185136657848493533703320344516205221201062605585078795667290312532533814301743955488337945840564772409098211089994373387482135086733355791335429
e = 3
c = 2394580744572758485664382078864430589081107938818619818847232653896896055892043210120884609992299242415105981742606013436008867608368852517444141394024820747542186260700353986223537409125
```

The generator (`gen.py`) built the keypair from two 512-bit primes,
so `n` is 1023 bits. The plaintext is the flag itself, 26 bytes, so
`m` is 207 bits. I did not need the primes. I mention their size
because the size comparison is the whole lab.

## What I Tried First, and Why It Did Not Work

My first thought was the right shape and the wrong tool. If the
message is short and `e` is 3, then maybe `c` is close to a plain
cube and I can just take a cube root. So I took the float cube root:

```python
values = {}
with open("challenge.txt") as f:
    for line in f:
        name, _, value = line.strip().partition("=")
        values[name.strip()] = int(value.strip())
c = values["c"]
approx = int(c ** (1 / 3))
print("float cube root as int:", approx)
print("approx ** 3 == c:", approx ** 3 == c)
print("difference (approx ** 3 - c):", approx ** 3 - c)
for guess in (approx - 2, approx - 1, approx, approx + 1, approx + 2):
    text = guess.to_bytes((guess.bit_length() + 7) // 8, "big")
    print(guess, "->", text)
```

Real output from that run:

```text
float cube root as int: 133785741067774314962072939763169910540187653071697305791365120
approx ** 3 == c: False
difference (approx ** 3 - c): -57455477225302823120798961800040313210920319459456751151965051784093856000045342123970660074386478335402535329738954613354326671489532542071666149267479648461741150567681125
133785741067774314962072939763169910540187653071697305791365118 -> b'SALVOz\xb7\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xfe'
133785741067774314962072939763169910540187653071697305791365119 -> b'SALVOz\xb7\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'
133785741067774314962072939763169910540187653071697305791365120 -> b'SALVOz\xb8\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
133785741067774314962072939763169910540187653071697305791365121 -> b'SALVOz\xb8\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01'
133785741067774314962072939763169910540187653071697305791365122 -> b'SALVOz\xb8\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02'
```

Frustrating output, that. The first five letters look right, which
told me the idea was sound, but the rest is junk and nudging the
guess by one or two changes nothing that matters. The reason is
precision. A float has 53 bits of mantissa. The true root is a
207-bit number. The float root I got was off from the true message
by 1070016622104113855774971363991263165487779114365, which I only
learned after solving it properly. No amount of plus-or-minus
fiddling around a float was going to cross a gap that size.

## The Breakthrough

I went back to the sizes. The generator output for the committed
challenge says it plainly:

```text
p bits = 512, q bits = 512
n bits = 1023
m bits = 207, m ** 3 bits = 620
m ** 3 < n: True
```

RSA encryption is `c = m^3 mod n`. But a mod never changes a number
that is already smaller than the modulus. Here `m^3` is 620 bits and
`n` is 1023 bits, so `m^3` never reached `n`, no wraparound happened,
and `c` is not modular at all. It is exactly `m^3` over the plain
integers.

So the problem was never factoring. It was arithmetic: find the
exact integer whose cube is `c`. Floats cannot do it. Integer Newton
steps can, and they can prove it, because an exact root must satisfy
`root ** 3 == c` with no remainder and no apology.

## The Full Solution

`solve.py`:

```python
#!/usr/bin/env python3
"""Solver for the rsa-small-exponent lab.

Because m ** 3 < n, the ciphertext is not really modular at all:
c = m ** 3 over the plain integers. So recovering m is just an
exact integer cube root of c. The catch is doing that root exactly.
Floats do not have enough precision for a number this size.

Pure standard library only.
"""


def integer_nth_root(x, n):
    """Return the exact floor of the nth root of x, using Newton steps
    on integers only. No floats anywhere near the value itself."""
    if x < 0:
        raise ValueError("x must be non-negative")
    if x == 0:
        return 0
    # Starting guess: a power of two just above the true root.
    guess = 1 << ((x.bit_length() + n - 1) // n + 1)
    while True:
        nxt = ((n - 1) * guess + x // pow(guess, n - 1)) // n
        if nxt >= guess:
            break
        guess = nxt
    # Correct any remaining off-by-one in either direction.
    while pow(guess, n) > x:
        guess -= 1
    while pow(guess + 1, n) <= x:
        guess += 1
    return guess


def load_challenge(path="challenge.txt"):
    values = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            name, _, value = line.partition("=")
            values[name.strip()] = int(value.strip())
    return values["n"], values["e"], values["c"]


def main():
    n, e, c = load_challenge()
    print(f"e = {e}")
    print(f"n bits = {n.bit_length()}")
    print(f"c bits = {c.bit_length()}")

    m = integer_nth_root(c, e)
    print(f"cube root is exact: {pow(m, e) == c}")

    flag = m.to_bytes((m.bit_length() + 7) // 8, "big")
    print(f"recovered: {flag.decode()}")

    # Verification: re-encrypt the recovered message and compare to c.
    check = pow(m, e, n)
    print(f"re-encryption matches c: {check == c}")
    assert check == c
    assert pow(m, e) == c, "root was not exact, so c was not a perfect cube"


if __name__ == "__main__":
    main()
```

Two details in that script carried the result. First, the starting
guess is a power of two sized from the bit length of `c`, so Newton
steps converge from above and stay in integers the whole way.
Second, after Newton stops, I correct any off-by-one in both
directions and then assert exactness. If the root were not exact,
the script would fail loudly instead of printing a near miss.

## Running It

```bash
$ python3 solve.py
e = 3
n bits = 1023
c bits = 620
cube root is exact: True
recovered: SALVO{sm4ll_e_b1g_pr0bl3m}
re-encryption matches c: True
```

## Verification and Flag

The solve verifies itself two ways. It checks that the root cubed
is exactly `c`, with no modulus involved, and it re-encrypts the
recovered message the real RSA way, `pow(m, 3, n)`, and compares
that against the `c` in `challenge.txt`. Both checks printed `True`.

Flag: `SALVO{sm4ll_e_b1g_pr0bl3m}`

The lesson I took from this one: a small exponent is not a problem
by itself. A small exponent plus a short, unpadded message is. The
padding is not decoration. It is what pushes the message up to the
size of the modulus and makes the mod step mean something.
