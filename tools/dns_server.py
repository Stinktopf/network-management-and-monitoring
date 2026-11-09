#!/usr/bin/env python3
"""Minimal DNS responder for data.oceanresearch.test."""

import ipaddress
import select
import socket
import struct

NAME = "data.oceanresearch.test."
A = ipaddress.ip_address("198.51.100.10").packed
AAAA = ipaddress.ip_address("2001:db8:100::10").packed


def parse_qname(data: bytes, off: int = 12):
    labels = []
    while True:
        if off >= len(data):
            raise ValueError("truncated qname")
        length = data[off]
        off += 1
        if length == 0:
            break
        if length & 0xC0:
            raise ValueError("compressed question names are not supported")
        labels.append(data[off : off + length].decode("ascii"))
        off += length
    return ".".join(labels) + ".", off


def answer(query: bytes) -> bytes:
    if len(query) < 12:
        return b""

    ident = query[:2]
    try:
        qname, off = parse_qname(query)
        qtype, qclass = struct.unpack("!HH", query[off : off + 4])
    except (UnicodeDecodeError, ValueError, struct.error):
        return b""

    question = query[12 : off + 4]
    if qclass != 1 or qname.lower() != NAME:
        return ident + b"\x81\x83" + struct.pack("!HHHH", 1, 0, 0, 0) + question

    if qtype == 1:
        rdata, rtype = A, 1
    elif qtype == 28:
        rdata, rtype = AAAA, 28
    else:
        return ident + b"\x81\x80" + struct.pack("!HHHH", 1, 0, 0, 0) + question

    record = b"\xc0\x0c" + struct.pack("!HHIH", rtype, 1, 30, len(rdata)) + rdata
    return ident + b"\x81\x80" + struct.pack("!HHHH", 1, 1, 0, 0) + question + record


def main() -> None:
    sockets = []

    sock4 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock4.bind(("0.0.0.0", 53))
    sockets.append(sock4)

    sock6 = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
    sock6.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 1)
    sock6.bind(("::", 53))
    sockets.append(sock6)

    while True:
        readable, _, _ = select.select(sockets, [], [])
        for sock in readable:
            query, peer = sock.recvfrom(4096)
            response = answer(query)
            if response:
                sock.sendto(response, peer)


if __name__ == "__main__":
    main()
