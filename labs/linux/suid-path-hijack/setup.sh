#!/bin/sh
# setup.sh - build and install the setuid backup helper for this lab.
# Run as root, on a throwaway machine or VM only.
#
# The helper is installed at /usr/local/lab-helper, on the root
# filesystem, on purpose: many systems mount /tmp with the nosuid
# option, which silently ignores the setuid bit on binaries there.
# The root filesystem normally honors setuid, so the lab works.
set -eu

LAB_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
FLAG='SALVO{su1d_p4th_h1j4ck}'
HELPER=/usr/local/lab-helper

if [ "$(id -u)" != "0" ]; then
    echo "setup.sh must be run as root" >&2
    exit 1
fi

# Sample data the helper is supposed to back up.
mkdir -p /tmp/lab-data
cat > /tmp/lab-data/notes.txt <<'EOF'
Shopping list for the lab box: coffee, cables, and a spare drive.
Nothing secret in here. The secret lives somewhere else entirely.
EOF
chmod 755 /tmp/lab-data
chmod 644 /tmp/lab-data/notes.txt

# Compile the helper and install it setuid root.
gcc -O2 -Wall -o "$HELPER" "$LAB_DIR/helper.c"
chown root:root "$HELPER"
chmod 4755 "$HELPER"

# The flag: root only, mode 600.
printf '%s\n' "$FLAG" > /root/lab-flag.txt
chown root:root /root/lab-flag.txt
chmod 600 /root/lab-flag.txt

echo "Setup complete:"
ls -l "$HELPER" /root/lab-flag.txt
ls -ld /tmp/lab-data
