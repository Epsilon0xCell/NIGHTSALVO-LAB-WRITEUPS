# Writeup: LSB Picture

I made this picture, hid a flag inside it, and then solved it back
the way a stranger would, checking the obvious doors first and
writing down what each one showed. Steganography labs are mostly
about discipline: prove the data is not in the easy places, then
think clearly about the one bit per channel nobody can see.

## Generate the challenge

```
$ python3 gen_image.py
wrote secret.png: 480x320 RGB PNG
embedded 30 message bytes plus a 4 byte length prefix
bits used: 272 of 460800 available
```

That last line is the one to sit with. The picture offers 460,800
channel bytes and the message uses 272 bits of them. Whatever is
hidden here is a whisper in a stadium.

## What I tried first that did not work

The file itself is unremarkable:

```
$ file secret.png
secret.png: PNG image data, 480 x 320, 8-bit/color RGB, non-interlaced
$ ls -l secret.png
-rw-rw---- 1 root root 3118 Nov  2 15:47 secret.png
```

Three kilobytes, no appended archive, no suspicious trailing bulk.
Next, strings, the first tool everyone reaches for with a picture:

```
$ strings secret.png | head -12
IHDR
IDATx
(S*R*S
V.~oY
H)-|
5*\#
@P&h
4@PNq
@P&h
@P&h
4@P*
D^aE
```

Compressed pixel noise, nothing readable. And the direct test:

```
$ strings secret.png | grep -i salvo
grep exit code: 1
```

No hit. The flag is not sitting in the file as text. Metadata was
the last easy door:

```
format: PNG | size: (480, 320) | mode: RGB
info dict: {}
text chunks: {}
```

Empty. No comment chunk, no author field, nothing. Three locked
doors in a row is information: the data lives in the pixels
themselves.

## The breakthrough

A channel byte of 200 and a channel byte of 201 are the same color
to any human eye. That last bit is free real estate, 460,800 bits of
it in this picture. If the hider walked the pixels in the obvious
order, left to right, top to bottom, channels R then G then B, and
wrote one bit per channel byte, then reading the least significant
bits in that same order rebuilds the byte stream. The only question
is framing, and the friendly convention is a length prefix: 32 bits
of big endian length, then the message.

## The solution

`extract.py` does exactly that read:

```python
img = Image.open(path)
bits = (byte & 1 for byte in img.convert("RGB").tobytes())
length = int.from_bytes(bits_to_bytes(take(bits, 32)), "big")
return bits_to_bytes(take(bits, length * 8))
```

and the run is short:

```
$ python3 extract.py
SALVO{lsb_h1d3s_1n_th3_p1x3ls}
```

First try, clean decode. When an LSB extraction works on the first
attempt it is because the framing guess was right, and the length
prefix check inside the extractor (it refuses implausible lengths)
never complained, which is its own confirmation.

## Verification

I compared the embedded picture against the clean base image that
`build_base_image()` draws, byte by byte:

```
channel bytes compared: 460800
bytes changed: 130
max change in any channel byte: 1
```

Exactly 130 channel bytes differ, none by more than 1. That is the
whole trick measured: the picture a viewer sees is, pixel for pixel,
at most one step of color away from the original, and the extracted
text matches the flag the generator embedded, byte for byte.

## Flag

```
SALVO{lsb_h1d3s_1n_th3_p1x3ls}
```

## The lesson I keep

Check the boring places first and write down that they were empty.
Strings, metadata, trailing data: three quick no answers turn "the
file must be hiding something in the pixels" from a guess into a
conclusion, and from there the LSB read is just careful bookkeeping.
