#!/usr/bin/env sh
DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
exec python3 "$DIR/msx.py" "$@"
