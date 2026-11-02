#!/usr/bin/env python3
"""gen_image.py - create secret.png and hide a flag in its LSBs.

Picture: a simple generated scene, a vertical sky gradient, a low
sun disc, and a dark hill band along the bottom. Plain PIL drawing,
no external assets.

Framing: a 32 bit big endian length prefix (the message length in
bytes), followed by the message bytes. Bits are written one per
channel byte, into the least significant bit, walking pixels left
to right and top to bottom, and channels in R, G, B order inside
each pixel. Each channel byte changes by at most 1.
"""

from pathlib import Path

from PIL import Image, ImageDraw

FLAG = b"SALVO{lsb_h1d3s_1n_th3_p1x3ls}"
WIDTH = 480
HEIGHT = 320
OUT = Path(__file__).with_name("secret.png")


def build_base_image() -> Image.Image:
    img = Image.new("RGB", (WIDTH, HEIGHT))
    px = img.load()
    for y in range(HEIGHT):
        # Sky: deep blue at the top fading to warm orange at the horizon.
        t = y / (HEIGHT - 1)
        r = int(32 + (238 - 32) * t)
        g = int(64 + (166 - 64) * t)
        b = int(140 + (92 - 140) * t)
        for x in range(WIDTH):
            px[x, y] = (r, g, b)

    draw = ImageDraw.Draw(img)
    # Sun: a pale disc sitting a little left of centre.
    draw.ellipse([190, 96, 290, 196], fill=(250, 226, 150))
    # Hills: two overlapping dark bands along the bottom.
    draw.ellipse([-120, 232, 320, 400], fill=(44, 78, 52))
    draw.ellipse([220, 248, 640, 410], fill=(30, 58, 40))
    return img


def message_bits(data: bytes):
    for byte in data:
        for shift in range(7, -1, -1):
            yield (byte >> shift) & 1


def embed(img: Image.Image, message: bytes) -> Image.Image:
    framed = len(message).to_bytes(4, "big") + message
    bits = list(message_bits(framed))
    capacity = WIDTH * HEIGHT * 3
    if len(bits) > capacity:
        raise ValueError(f"message needs {len(bits)} bits, image holds {capacity}")

    flat = bytearray(img.tobytes())
    for i, bit in enumerate(bits):
        flat[i] = (flat[i] & 0xFE) | bit
    return Image.frombytes("RGB", img.size, bytes(flat))


def main() -> None:
    img = embed(build_base_image(), FLAG)
    img.save(OUT)
    print(f"wrote {OUT.name}: {img.size[0]}x{img.size[1]} RGB PNG")
    print(f"embedded {len(FLAG)} message bytes plus a 4 byte length prefix")
    print(f"bits used: {(len(FLAG) + 4) * 8} of {WIDTH * HEIGHT * 3} available")


if __name__ == "__main__":
    main()
