#!/usr/bin/env python3
"""Generator for the repeating-xor lab.

XORs the flag with a short repeating key and writes the result as
hex to cipher.hex. Pure standard library only.

The key is printed for the lab author only. It never goes into
cipher.hex.
"""

FLAG = b"SALVO{r3p34t1ng_k3y_r3p34ts_1ts3lf}"
KEY = b"K3y!9"  # 5 bytes: upper, digit, lower, symbol, digit


def xor_with_key(data, key):
    return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))


def main():
    assert len(KEY) == 5
    cipher = xor_with_key(FLAG, KEY)
    with open("cipher.hex", "w") as f:
        f.write(cipher.hex() + "\n")
    # Lab author only: printed, never written to cipher.hex.
    print(f"key = {KEY!r} (length {len(KEY)})")
    print(f"flag length = {len(FLAG)} bytes")
    print(f"cipher length = {len(cipher)} bytes")
    print(f"cipher.hex = {cipher.hex()}")
    print("wrote cipher.hex")


if __name__ == "__main__":
    main()
