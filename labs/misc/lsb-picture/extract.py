#!/usr/bin/env python3
"""extract.py - pull the hidden message back out of secret.png.

Reads the least significant bit of each channel byte in the same
order gen_image.py wrote them: pixels left to right, top to
bottom, channels in R, G, B order. The first 32 bits are a big
endian length, the next length * 8 bits are the message.
"""

import sys
from pathlib import Path

from PIL import Image


def bits_to_bytes(bits) -> bytes:
    out = bytearray()
    byte = 0
    count = 0
    for bit in bits:
        byte = (byte << 1) | bit
        count += 1
        if count == 8:
            out.append(byte)
            byte = 0
            count = 0
    return bytes(out)


def take(bits, n):
    return [next(bits) for _ in range(n)]


def extract(path: Path) -> bytes:
    img = Image.open(path)
    bits = (byte & 1 for byte in img.convert("RGB").tobytes())

    length = int.from_bytes(bits_to_bytes(take(bits, 32)), "big")
    capacity_bytes = (img.size[0] * img.size[1] * 3 - 32) // 8
    if length <= 0 or length > capacity_bytes:
        raise ValueError(f"implausible length prefix: {length}")

    return bits_to_bytes(take(bits, length * 8))


def main() -> None:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).with_name("secret.png")
    print(extract(path).decode("utf-8"))


if __name__ == "__main__":
    main()
