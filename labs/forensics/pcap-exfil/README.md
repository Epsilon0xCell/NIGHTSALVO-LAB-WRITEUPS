# pcap-exfil

A short packet capture from a home network. Most of it is boring: a few name lookups, one web page fetch. Something in it does not belong, and the thing that left this network did not leave through the web page.

Author: Gavin Blacklock

## Objective

Find the data that was smuggled out of this capture, decode it, and recover the flag. The flag format is `SALVO{...}`.

## Files

- `capture.pcap`: the capture you have to work. Twelve packets, 1275 bytes.
- `gen_pcap.py`: the generator that built the capture, in case you want to rebuild it or vary it. Python 3.12 standard library only.
- `solve.py`: my solver. Try the lab by hand first, then compare.

## Setup

No installs. You need Python 3.12 and the `strings` utility, both already present on a normal Linux box. I did this lab in an environment with no `tshark` and no `tcpdump`, so the whole method is `strings` plus a small Python parser. That is a feature: you have to actually read the bytes.

```bash
cd labs/forensics/pcap-exfil
python3 gen_pcap.py   # rebuilds capture.pcap, optional
ls -l capture.pcap
```

## The task

1. Look at the capture with `strings` and work out which traffic is normal and which traffic is not.
2. Extract the suspicious pieces in the order they appear in the capture. Order matters.
3. Work out the encoding, decode it, and recover the flag.

## Hint ladder

Hint 1, a nudge: count how many distinct hostnames are being looked up, and look closely at the ones you do not recognise. Normal lookups have names a person would type. The others share a suffix.

Hint 2, more specific: DNS query names are not private. Anything put in front of a domain you control leaves with the query. The odd queries in this capture are labels under `exfil.example.com`, and each label is a piece of one encoded string, in capture order.

Hint 3, nearly the answer: the pieces, joined in order, are base32 with the padding stripped. Put back enough `=` characters to make the length a multiple of eight, decode, and read the flag.
