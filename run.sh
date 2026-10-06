#!/bin/sh
# Usage: ./run.sh         - start the emulator
#        ./run.sh test    - run unit tests
DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON="${PYTHON:-python3}"
export PYTHONPATH="$DIR/src"
if [ "$1" = "test" ]; then
    "$PYTHON" -m unittest discover -s "$DIR/tests" -v
else
    "$PYTHON" "$DIR/src/main.py" "$@"
fi
