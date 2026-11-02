# RSA: Small Exponent

Author: Gavin Blacklock
Category: Crypto
Difficulty: Easy

## Objective

Recover the plaintext message from an RSA ciphertext in
`challenge.txt`. The public exponent is unusually small, and the
message is short. No private key is given, and factoring the modulus
is not the intended path.

Flag format: `SALVO{...}`

## Files

- `gen.py`: generator. Builds a keypair from two 512-bit primes, sets
  `e = 3`, encrypts the flag, and writes `challenge.txt`. It prints
  the primes for the lab author only.
- `challenge.txt`: the challenge. It contains only `n`, `e`, and `c`.
- `solve.py`: my solution. See `WRITEUP.md` for the full walkthrough.
- `WRITEUP.md`: the writeup, with the failed first attempt included.

## Setup

You need Python 3.12. Nothing else. The generator and the solver use
the standard library only.

```bash
cd labs/crypto/rsa-small-exponent
python3 gen.py      # regenerate challenge.txt (new primes each run)
cat challenge.txt
```

Note: regenerating makes a fresh modulus and a fresh ciphertext for
the same flag. The numbers in `WRITEUP.md` match the committed
`challenge.txt`, not a regenerated one.

## The Task

Given `n`, `e = 3`, and `c`, recover the original message and submit
it as the flag.

## Hint Ladder

Hint 1: Look at the sizes before you reach for factoring. Compare the
bit length of `c` with the bit length of `n`. The ciphertext is much
smaller than the modulus. Ask yourself what that says about whether
the modular reduction in `c = m^e mod n` ever actually happened.

Hint 2: If `m^3` never reached `n`, then `c` is just `m^3` as a plain
integer, and the problem is a cube root, not RSA. But take the root
with integer arithmetic. A float root will look close and still be
wrong, because a float cannot hold a number this size exactly. Write
an exact integer nth root (Newton steps on integers work well), check
that `root ** 3 == c`, and only then convert the root back to bytes.
