#!/usr/bin/env python3
"""Generator for the rsa-small-exponent lab.

Builds a real RSA keypair from two 512-bit primes, sets e = 3, and
encrypts the flag itself as the plaintext message. The flag is short
enough (26 bytes, 207 bits) that m ** 3 (620 bits) is far below n
(1023 bits here), so the encryption never wraps around the modulus.

Pure standard library only. Run it to regenerate challenge.txt.
The primes are printed for the lab author only. They never go into
challenge.txt.
"""

import secrets

FLAG = b"SALVO{sm4ll_e_b1g_pr0bl3m}"
E = 3
PRIME_BITS = 512


def is_probable_prime(n, rounds=40):
    """Miller-Rabin primality test, pure Python."""
    if n < 2:
        return False
    small_primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37]
    for p in small_primes:
        if n % p == 0:
            return n == p
    # Write n - 1 as (2 ** r) * d with d odd.
    r = 0
    d = n - 1
    while d % 2 == 0:
        d //= 2
        r += 1
    for _ in range(rounds):
        a = 2 + secrets.randbelow(n - 3)
        x = pow(a, d, n)
        if x == 1 or x == n - 1:
            continue
        for _ in range(r - 1):
            x = pow(x, 2, n)
            if x == n - 1:
                break
        else:
            return False
    return True


def gen_prime(bits):
    """Generate a prime with exactly `bits` bits and prime % 3 == 2.

    The remainder condition matters: if a prime were 1 mod 3, then
    3 would divide p - 1, and gcd(e, phi(n)) would not be 1, so
    e = 3 would have no valid private exponent at all.
    """
    while True:
        candidate = secrets.randbits(bits)
        candidate |= (1 << (bits - 1))  # force the top bit: exact size
        candidate |= 1  # force odd
        if candidate % 3 != 2:
            continue
        if is_probable_prime(candidate):
            return candidate


def main():
    p = gen_prime(PRIME_BITS)
    q = gen_prime(PRIME_BITS)
    while q == p:
        q = gen_prime(PRIME_BITS)

    n = p * q
    phi = (p - 1) * (q - 1)
    import math

    assert math.gcd(E, phi) == 1, "e and phi(n) must be coprime"
    d = pow(E, -1, phi)

    m = int.from_bytes(FLAG, "big")
    assert m < n, "message must be smaller than n"
    assert m ** 3 < n, "this lab needs m ** 3 < n, no wraparound"

    c = pow(m, E, n)
    # Sanity check with the real private key before writing anything.
    assert pow(c, d, n) == m, "decryption with d failed"

    with open("challenge.txt", "w") as f:
        f.write(f"n = {n}\n")
        f.write(f"e = {E}\n")
        f.write(f"c = {c}\n")

    # Lab author only: these lines are printed, never written to the file.
    print(f"p = {p}")
    print(f"q = {q}")
    print(f"p bits = {p.bit_length()}, q bits = {q.bit_length()}")
    print(f"n bits = {n.bit_length()}")
    print(f"m bits = {m.bit_length()}, m ** 3 bits = {(m ** 3).bit_length()}")
    print("m ** 3 < n:", m ** 3 < n)
    print("wrote challenge.txt with n, e, c only")


if __name__ == "__main__":
    main()
