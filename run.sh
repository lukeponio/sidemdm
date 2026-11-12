#!/usr/bin/env sh
# Thin wrapper so `./run.sh` just works. All logic is in sidemdm.py.
exec python3 "$(dirname "$0")/sidemdm.py" "$@"
