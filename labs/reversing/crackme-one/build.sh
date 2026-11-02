#!/bin/sh
# Build crackme-one. Symbols are kept on purpose: reading the
# disassembly is part of the lesson.
set -e
cd "$(dirname "$0")"
gcc -O0 -Wall -Wextra -o crackme crackme.c
