#!/usr/bin/env python3
"""Build capture.pcap by hand with struct. Python 3.12 standard library only.

Traffic mix:
  - a few plain DNS lookups for ordinary domains
  - one HTTP GET over TCP
  - DNS exfiltration: a flag, base32 encoded with padding stripped,
    split into 10 character chunks, one chunk per query label, like
    <chunk>.exfil.example.com

No scapy, no tshark, no tcpdump. Just bytes packed in the right order.
Author: Gavin Blacklock
"""

import base64
import os
import socket
import struct

FLAG = b"SALVO{dns_3xf1l_h1d3s_1n_pl41n_s1ght}"

CLIENT_IP = "192.168.1.50"
RESOLVER_IP = "8.8.8.8"
WEB_IP = "93.184.216.34"

CLIENT_MAC = bytes.fromhex("001122334455")
RESOLVER_MAC = bytes.fromhex("66778899aabb")

BASE_TS = 1761700000  # fixed base time, so rebuilds are byte identical apart from nothing


def checksum(data: bytes) -> int:
    """Standard 16 bit Internet checksum (RFC 1071)."""
    if len(data) % 2:
        data += b"\x00"
    total = 0
    for i in range(0, len(data), 2):
        total += (data[i] << 8) + data[i + 1]
    while total >> 16:
        total = (total & 0xFFFF) + (total >> 16)
    return (~total) & 0xFFFF


def ethernet(dst_mac: bytes, src_mac: bytes, ethertype: int, payload: bytes) -> bytes:
    return dst_mac + src_mac + struct.pack("!H", ethertype) + payload


def ipv4(src_ip: str, dst_ip: str, protocol: int, payload: bytes, ident: int) -> bytes:
    version_ihl = 0x45
    total_length = 20 + len(payload)
    header_no_sum = struct.pack(
        "!BBHHHBBH4s4s",
        version_ihl,
        0,
        total_length,
        ident,
        0,
        64,
        protocol,
        0,
        socket.inet_aton(src_ip),
        socket.inet_aton(dst_ip),
    )
    csum = checksum(header_no_sum)
    header = struct.pack(
        "!BBHHHBBH4s4s",
        version_ihl,
        0,
        total_length,
        ident,
        0,
        64,
        protocol,
        csum,
        socket.inet_aton(src_ip),
        socket.inet_aton(dst_ip),
    )
    return header + payload


def udp(src_ip: str, dst_ip: str, src_port: int, dst_port: int, payload: bytes) -> bytes:
    length = 8 + len(payload)
    pseudo = (
        socket.inet_aton(src_ip)
        + socket.inet_aton(dst_ip)
        + struct.pack("!BBH", 0, 17, length)
    )
    header_no_sum = struct.pack("!HHHH", src_port, dst_port, length, 0)
    csum = checksum(pseudo + header_no_sum + payload)
    if csum == 0:
        csum = 0xFFFF
    return struct.pack("!HHHH", src_port, dst_port, length, csum) + payload


def tcp(src_ip: str, dst_ip: str, src_port: int, dst_port: int, payload: bytes, seq: int) -> bytes:
    offset_flags = (5 << 12) | 0x18  # data offset 5 words, PSH + ACK
    window = 64240
    pseudo = (
        socket.inet_aton(src_ip)
        + socket.inet_aton(dst_ip)
        + struct.pack("!BBH", 0, 6, 20 + len(payload))
    )
    header_no_sum = struct.pack("!HHIIHHHH", src_port, dst_port, seq, 1, offset_flags, window, 0, 0)
    csum = checksum(pseudo + header_no_sum + payload)
    header = struct.pack("!HHIIHHHH", src_port, dst_port, seq, 1, offset_flags, window, csum, 0)
    return header + payload


def dns_query(txid: int, qname: str, qtype: int = 1) -> bytes:
    header = struct.pack("!HHHHHH", txid, 0x0100, 1, 0, 0, 0)
    question = b""
    for label in qname.strip(".").split("."):
        encoded = label.encode("ascii")
        question += struct.pack("!B", len(encoded)) + encoded
    question += b"\x00" + struct.pack("!HH", qtype, 1)
    return header + question


def dns_frame(src_port: int, txid: int, qname: str, ident: int) -> bytes:
    payload = dns_query(txid, qname)
    segment = udp(CLIENT_IP, RESOLVER_IP, src_port, 53, payload)
    packet = ipv4(CLIENT_IP, RESOLVER_IP, 17, segment, ident)
    return ethernet(RESOLVER_MAC, CLIENT_MAC, 0x0800, packet)


def http_frame(ident: int) -> bytes:
    payload = (
        b"GET /index.html HTTP/1.1\r\n"
        b"Host: example.org\r\n"
        b"User-Agent: Mozilla/5.0 (X11; Linux x86_64)\r\n"
        b"Accept: text/html\r\n"
        b"\r\n"
    )
    segment = tcp(CLIENT_IP, WEB_IP, 49152, 80, payload, seq=1000)
    packet = ipv4(CLIENT_IP, WEB_IP, 6, segment, ident)
    return ethernet(RESOLVER_MAC, CLIENT_MAC, 0x0800, packet)


def pcap_record(ts_sec: int, ts_usec: int, frame: bytes) -> bytes:
    return struct.pack("!IIII", ts_sec, ts_usec, len(frame), len(frame)) + frame


def main() -> None:
    encoded = base64.b32encode(FLAG).decode("ascii").rstrip("=")
    chunks = [encoded[i : i + 10] for i in range(0, len(encoded), 10)]
    print(f"base32 (padding stripped): {encoded}")
    print(f"chunks: {chunks}")

    normal_domains = [
        "example.org",
        "www.wikipedia.org",
        "pypi.org",
        "github.com",
        "news.ycombinator.com",
    ]

    # Interleave noise and exfil so the capture reads like real traffic.
    plan = [
        ("dns", normal_domains[0]),
        ("dns", f"{chunks[0]}.exfil.example.com"),
        ("dns", normal_domains[1]),
        ("dns", f"{chunks[1]}.exfil.example.com"),
        ("http", None),
        ("dns", f"{chunks[2]}.exfil.example.com"),
        ("dns", normal_domains[2]),
        ("dns", f"{chunks[3]}.exfil.example.com"),
        ("dns", normal_domains[3]),
        ("dns", f"{chunks[4]}.exfil.example.com"),
        ("dns", normal_domains[4]),
        ("dns", f"{chunks[5]}.exfil.example.com"),
    ]

    frames = []
    for index, (kind, value) in enumerate(plan):
        if kind == "http":
            frames.append(http_frame(ident=2000 + index))
        else:
            frames.append(
                dns_frame(
                    src_port=53000 + index,
                    txid=0x1000 + index,
                    qname=value,
                    ident=1000 + index,
                )
            )

    global_header = struct.pack(
        "!IHHiIII",
        0xA1B2C3D4,  # magic
        2,  # version major
        4,  # version minor
        0,  # thiszone
        0,  # sigfigs
        65535,  # snaplen
        1,  # network: Ethernet
    )

    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "capture.pcap")
    with open(out_path, "wb") as handle:
        handle.write(global_header)
        for index, frame in enumerate(frames):
            handle.write(pcap_record(BASE_TS + index * 2, index * 137000 % 1000000, frame))

    print(f"wrote {out_path}: {len(frames)} packets, {os.path.getsize(out_path)} bytes")


if __name__ == "__main__":
    main()
