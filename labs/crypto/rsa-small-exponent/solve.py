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
