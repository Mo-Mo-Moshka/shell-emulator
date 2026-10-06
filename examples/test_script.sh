#!/bin/sh
# Startup script: exit from script, stop at first error, missing file.
DIR="$(cd "$(dirname "$0")" && pwd)"
RUN="$DIR/../run.sh"
LOG="$DIR/logs/script.csv"
rm -f "$LOG"

echo '=== 1. Script ends with "exit 3": window closes by itself ==='
"$RUN" --log "$LOG" --script "$DIR/startup/exit.txt"
echo "exit code: $? (expected 3)"

echo "=== 2. Script with an error: stops at line 4 ==="
"$RUN" --log "$LOG" --script "$DIR/startup/error.txt"
echo "exit code: $?"

echo "=== 3. Script file does not exist ==="
"$RUN" --log "$LOG" --script "$DIR/startup/missing.txt"
echo "exit code: $?"

echo "--- $LOG ---"
cat "$LOG"
