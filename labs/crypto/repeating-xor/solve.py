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
