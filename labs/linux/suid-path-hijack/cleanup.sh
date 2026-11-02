#!/bin/sh
# cleanup.sh - remove everything setup.sh and a solve attempt create.
# Run as root.
set -eu

if [ "$(id -u)" != "0" ]; then
    echo "cleanup.sh must be run as root" >&2
    exit 1
fi

rm -f /usr/local/lab-helper /tmp/lab-helper
rm -f /root/lab-flag.txt
rm -f /tmp/lab-backup.tgz
rm -rf /tmp/lab-data

echo "Cleanup complete. Remaining lab artifacts:"
ls -l /usr/local/lab-helper /root/lab-flag.txt /tmp/lab-backup.tgz 2>&1 || true
ls -ld /tmp/lab-data 2>&1 || true
