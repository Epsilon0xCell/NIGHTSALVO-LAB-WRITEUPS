# Lab: LSB Picture

- **Category:** misc
- **Difficulty:** beginner
- **Author:** Gavin Blacklock

## Objective

A small generated picture of a sunset over hills looks completely
ordinary, and it is carrying a flag in the one place nobody looks: the
least significant bit of every pixel channel. Find the framing, read
the bits back out, and recover the message.

## Files

- `gen_image.py`: builds the picture with PIL (a sky gradient, a sun
  disc, two hill bands) and embeds the flag before saving.
- `secret.png`: the generated picture, 480 by 320, with the flag
  already hidden in it. This is your challenge file.
- `extract.py`: the reference extractor, for checking your own work
  after you have solved it by hand.

## Setup

You need Python 3 with PIL:

```sh
python3 gen_image.py   # regenerates secret.png if you ever lose it
```

## The task

1. Look at `secret.png` the obvious ways first: open it, run `strings`
   on it, check its metadata. Convince yourself the easy doors are
   locked.
2. Work out where the data is hiding and in what order it was written.
3. Write your own extractor and print the flag.

## Hint ladder

**Hint 1:** The picture is 480 by 320 pixels, 3 channel bytes each.
That is 460,800 channel bytes, and the file is only about 3 KB. The
message is not appended to the file or written in any text chunk.
Think about what can change in a pixel without your eye noticing.

**Hint 2:** Changing a channel byte by 1 is invisible. If you read one
specific bit from each channel byte in a fixed order, left to right,
top to bottom, R then G then B, the bits form a byte stream. A sane
format for that stream tells you how long the message is before the
message starts.

**Hint 3:** The first 32 bits are a big endian length prefix: the
message length in bytes. Read that many bytes after it, and you are
done. If your first decode is garbage, check your bit order inside
each byte before you blame the framing.

## Safety note

This lab is an original exercise built for authorized local practice.
The picture, the flag, and the method were all made here for learning.
