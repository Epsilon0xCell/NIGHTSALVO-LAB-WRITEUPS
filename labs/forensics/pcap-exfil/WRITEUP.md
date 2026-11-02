# Writeup: pcap-exfil

By Gavin Blacklock

Someone on a home network sent data out of the house inside DNS queries, and I had the capture. Twelve packets, 1275 bytes. My job was to find what left, put it back together in the right order, and decode it.

One honesty note before anything else: I did this with no `tshark` and no `tcpdump` on the box. They are not installed here, and pretending I ran them would be lying about the method. What I had was `strings` and Python 3.12, standard library only. That turned out to be plenty, and it forced me to actually understand the file format instead of clicking through a protocol tree.

## What I tried first, and why it did not work

First I checked for the tools I would normally reach for:

```text
$ which tshark tcpdump; echo exit:$?
exit:1
```

Nothing. No output, exit 1. Fine, I thought, `strings` will tell me most of it anyway. I ran it raw:

```text
$ strings capture.pcap | head -n 20
"3DU
example
"3DU
KNAUYVSPPN
exfil
example
"3DU
www	wikipedia
"3DU
SG4427GN4G
exfil
example
"3DU
GET /index.html HTTP/1.1
Host: example.org
User-Agent: Mozilla/5.0 (X11; Linux x86_64)
Accept: text/html
"3DU
MMLML5UDCZ
exfil
```

Two problems with that. The first is noise: the `"3DU` lines are binary header bytes that happen to be printable, and they sit between everything I care about. The second problem is worse. DNS does not store a hostname as one piece of text. It stores it as length prefixed labels, so `strings` chops every name into fragments, one label per line, and the dots never appear. I could see something was there, but I could not read a single full query name off that output.

My next idea was worse. I filtered for the one word that looked guilty:

```text
$ strings capture.pcap | grep exfil
exfil
exfil
exfil
exfil
exfil
exfil
```

Six identical lines. Technically a hit, practically useless. The filter kept the label I searched for and threw away the label next to it, which was the actual data. Filtering on the suffix alone cut the payload out of my own results.

## The breakthrough

The labels sit side by side in the packet, in order. In the `strings` output, that means the chunk I want is on the line directly before each `exfil` line. One flag to `grep` fixes the whole view:

```text
$ strings capture.pcap | grep -B 1 exfil
KNAUYVSPPN
exfil
--
SG4427GN4G
exfil
--
MMLML5UDCZ
exfil
--
BTONPTC3S7
exfil
--
OBWDIMLOL5
exfil
--
ZTCZ3IOR6Q
exfil
```

There it was. Six chunks of uppercase letters and digits, each ten characters, each sent as a label in front of `exfil.example.com`. Uppercase plus digits in that range, with that even, padded look, reads as base32 to me. The normal traffic around it was plain: lookups for `example.org`, `www.wikipedia.org`, `pypi.org`, `github.com`, and `news.ycombinator.com`, plus one HTTP GET for a page on `example.org`. Noise to make the odd queries blend in, and it nearly works if you only skim.

That gave me a hypothesis I could test by hand: join the six chunks in capture order, restore the base32 padding, decode. But joining lines out of `strings` output by hand is fragile and proves nothing about order, so I wrote a real parser instead.

## The full solution

`solve.py`, sitting next to this writeup, does the job properly, and it only uses the standard library:

1. It reads the whole file and checks the first four bytes are the pcap magic, `0xa1b2c3d4`. If they are not, it stops instead of guessing.
2. It steps past the 24 byte global header, then walks each packet record: timestamp, captured length, then that many bytes of frame.
3. Inside each frame it skips the 14 byte Ethernet header, reads the IPv4 header length, and checks the protocol byte. Only UDP packets headed for port 53 count as DNS here. The HTTP GET rides TCP, so it falls out at this step on its own.
4. For each DNS packet it reads the question count, then walks the query name label by label, which is exactly the structure that made `strings` chop the names up, and rebuilds the full dotted name.
5. It keeps every name that ends in `.exfil.example.com`, cuts that suffix off, and keeps the labels in the order the packets appear in the file.
6. It joins the labels, adds back `=` padding until the length is a multiple of eight, and base32 decodes the result.

Running it:

```text
$ python3 solve.py
all DNS query names, in capture order:
  example.org
  KNAUYVSPPN.exfil.example.com
  www.wikipedia.org
  SG4427GN4G.exfil.example.com
  MMLML5UDCZ.exfil.example.com
  pypi.org
  BTONPTC3S7.exfil.example.com
  github.com
  OBWDIMLOL5.exfil.example.com
  news.ycombinator.com
  ZTCZ3IOR6Q.exfil.example.com

exfil chunks (6): ['KNAUYVSPPN', 'SG4427GN4G', 'MMLML5UDCZ', 'BTONPTC3S7', 'OBWDIMLOL5', 'ZTCZ3IOR6Q']
joined:  KNAUYVSPPNSG4427GN4GMMLML5UDCZBTONPTC3S7OBWDIMLOL5ZTCZ3IOR6Q
decoded: SALVO{dns_3xf1l_h1d3s_1n_pl41n_s1ght}
```

The interleaving matters. Notice the exfil queries are not bunched at the end: they sit between the normal lookups, second packet, fourth packet, and so on. Capture order is the only order that decodes. Shuffle those six chunks and base32 gives you garbage, which is the whole trick of this exfil channel: each query looks small and forgettable, the sequence is the message.

## Verified

I do not trust a decode just because it prints something readable, so I checked the solver output against the expected flag value directly:

```text
decoded : SALVO{dns_3xf1l_h1d3s_1n_pl41n_s1ght}
expected: SALVO{dns_3xf1l_h1d3s_1n_pl41n_s1ght}
match   : True
```

Exact match, character for character.

The lesson I took from this one is unglamorous and worth keeping: DNS is a terrible place to hide anything. A query name is logged by the resolver, kept in captures, and readable with the cheapest tool on the system. Whoever sent this flag out hid it in plain sight, and plain sight is exactly where it stayed.

Flag: `SALVO{dns_3xf1l_h1d3s_1n_pl41n_s1ght}`
