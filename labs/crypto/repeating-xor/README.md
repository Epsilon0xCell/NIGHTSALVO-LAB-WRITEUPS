# Repeating-Key XOR

Author: Gavin Blacklock
Category: Crypto
Difficulty: Easy

## Objective

Recover the plaintext from a ciphertext in `cipher.hex`. The
plaintext was XORed with a short key that repeats for the whole
message. The key is not given. The flag format is known, and that
known format is the way in.

Flag format: `SALVO{...}`

## Files

- `gen.py`: generator. XORs the flag with the key and writes
  `cipher.hex`. It prints the key for the lab author only.
- `cipher.hex`: the challenge. One line of hex, the ciphertext.
- `solve.py`: my solution. See `WRITEUP.md` for the full walkthrough.
- `WRITEUP.md`: the writeup, with the failed first attempt included.

## Setup

You need Python 3.12. Nothing else. The generator and the solver use
the standard library only.

```bash
cd labs/crypto/repeating-xor
python3 gen.py      # regenerate cipher.hex (same flag, same key)
cat cipher.hex
```

## The Task

Given only the hex ciphertext in `cipher.hex`, recover the key and
the plaintext, and submit the plaintext as the flag.

## Hint Ladder

Hint 1: XOR has a habit worth remembering: if you know a piece of
plaintext, XORing it against the matching ciphertext gives you the
key bytes for those positions, because `cipher = plain XOR key`
means `key = cipher XOR plain`. You already know how every flag in
this series starts.

Hint 2: The known prefix is 6 bytes long: `SALVO{`. XOR it against
the first 6 ciphertext bytes and look at the result as a stream. If
the key is shorter than the window, the key must start repeating
inside the window, and the same byte shows up twice. Test each
candidate period for consistency, take the smallest one that fits,
use those bytes as the full key, and XOR the whole ciphertext. Then
check your answer by re-encrypting it and comparing with
`cipher.hex`.
