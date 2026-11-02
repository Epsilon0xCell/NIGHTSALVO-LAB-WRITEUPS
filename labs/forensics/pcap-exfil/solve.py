#!/usr/bin/env python3
"""Solve the pcap-exfil lab. Python 3.12 standard library only.

Parses capture.pcap record by record, walks Ethernet plus IPv4 plus UDP,
reads each DNS query name in capture order, keeps the labels sent to
exfil.example.com, joins them, restores base32 padding, and decodes.
Author: Gavin Blacklock
"""

import base64
import os
import struct
import sys


def parse_dns_name(packet: bytes, offset: int) -> tuple[str, int]:
    labels = []
    while True:
        length = packet[offset]
        offset += 1
        if length == 0:
            break
        labels.append(packet[offset : offset + length].decode("ascii"))
        offset += length
    return ".".join(labels), offset


def query_names(path: str) -> list[str]:
    names = []
    with open(path, "rb") as handle:
        data = handle.read()
    magic = struct.unpack("!I", data[0:4])[0]
    if magic != 0xA1B2C3D4:
        raise ValueError(f"not a pcap file I recognise, magic is {magic:#x}")
    offset = 24  # pcap global header is 24 bytes
    while offset + 16 <= len(data):
        _ts_sec, _ts_usec, incl_len, _orig_len = struct.unpack("!IIII", data[offset : offset + 16])
        offset += 16
        frame = data[offset : offset + incl_len]
        offset += incl_len

        if len(frame) < 14 or struct.unpack("!H", frame[12:14])[0] != 0x0800:
            continue
        ip = frame[14:]
        ihl = (ip[0] & 0x0F) * 4
        if ip[9] != 17:  # not UDP, so not DNS in this capture (the HTTP GET rides TCP)
            continue
        udp = ip[ihl:]
        dst_port = struct.unpack("!H", udp[2:4])[0]
        if dst_port != 53:
            continue
        dns = udp[8:]
        qdcount = struct.unpack("!H", dns[4:6])[0]
        cursor = 12  # DNS header is 12 bytes
        for _ in range(qdcount):
            name, cursor = parse_dns_name(dns, cursor)
            names.append(name)
            cursor += 4  # qtype plus qclass
    return names


def main() -> None:
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "capture.pcap"
    )
    names = query_names(path)
    print("all DNS query names, in capture order:")
    for name in names:
        print(f"  {name}")

    suffix = ".exfil.example.com"
    chunks = [name[: -len(suffix)] for name in names if name.endswith(suffix)]
    print(f"\nexfil chunks ({len(chunks)}): {chunks}")

    joined = "".join(chunks)
    padded = joined + "=" * ((8 - len(joined) % 8) % 8)
    decoded = base64.b32decode(padded).decode("ascii")
    print(f"joined:  {joined}")
    print(f"decoded: {decoded}")


if __name__ == "__main__":
    main()
