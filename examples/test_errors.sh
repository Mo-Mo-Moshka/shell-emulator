#!/bin/sh
# Invalid command line parameters.
DIR="$(cd "$(dirname "$0")" && pwd)"
RUN="$DIR/../run.sh"

echo "=== 1. Help on parameters ==="
"$RUN" --help
echo "exit code: $?"

echo "=== 2. Unknown parameter: emulator does not start ==="
"$RUN" --color red
echo "exit code: $? (expected 2)"

echo "=== 3. Parameter without a value ==="
"$RUN" --log
echo "exit code: $? (expected 2)"

echo "=== 4. Log path is a directory: error shown, emulator works ==="
"$RUN" --log "$DIR/startup"
echo "exit code: $?"
