#!/bin/sh
# Build ret2win-overflow with protections deliberately off for the lab:
#   -fno-stack-protector  no stack canary to stop the overwrite
#   -no-pie               fixed addresses, so win() stays in one place
#   -z norelro            classic RELRO setting for a teaching binary
set -e
cd "$(dirname "$0")"
gcc -O0 -Wall -fno-stack-protector -no-pie -z norelro -o vuln vuln.c
