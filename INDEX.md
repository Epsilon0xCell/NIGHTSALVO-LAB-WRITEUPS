# Index of Labs

Every lab, by category. Each entry links to the lab folder, which
holds its README (the task) and its WRITEUP (the full solution).

## Web

- [sqli-login-bypass](labs/web/sqli-login-bypass/): a stdlib Python
  login app whose SQL query is built by string formatting. Log in as
  admin without the password and reach the flag page.
- [xss-comment-board](labs/web/xss-comment-board/): a comment board
  that stores and renders comments with no sanitizing, plus a Node
  bot that plays the visiting admin. Steal the admin session cookie
  with a stored payload.

## Crypto

- [rsa-small-exponent](labs/crypto/rsa-small-exponent/): RSA with
  e = 3 and a short message, so the cube never wraps the modulus.
  Recover the plaintext with an exact integer cube root.
- [repeating-xor](labs/crypto/repeating-xor/): a flag XORed with a
  short repeating key. Recover the key from the known flag format,
  prove its period, and decrypt.

## Reversing

- [crackme-one](labs/reversing/crackme-one/): a C crackme whose
  password check XORs each character against a stored byte array.
  Derive the password from the disassembly and the bytes in .rodata.

## Pwn

- [ret2win-overflow](labs/pwn/ret2win-overflow/): a gets() overflow
  in a binary built with protections off, and a hidden win function
  that is never called. Find the offset, aim the return address,
  print the flag.

## Forensics

- [pcap-exfil](labs/forensics/pcap-exfil/): a hand-built packet
  capture where ordinary traffic hides DNS queries that carry an
  encoded flag out one subdomain at a time. Pull the chunks out and
  decode them.
- [auth-log-hunt](labs/forensics/auth-log-hunt/): a generated sshd
  auth log. One IP brute-forces its way in exactly once. With grep
  and awk only, name the attacker IP, the compromised account, and
  the minute it happened.

## Linux

- [suid-path-hijack](labs/linux/suid-path-hijack/): a setuid root
  backup helper that calls tar by its bare name. Plant a fake tar
  first in PATH and have the helper run your code as root.

## Misc

- [lsb-picture](labs/misc/lsb-picture/): a generated sunset picture
  with a flag written into the least significant bits of its pixels.
  Rule out the easy hiding places, then read the bits back out.
