#!/bin/sh
# Command line parameters: none, only --vfs, all three together.
# Close the emulator window (or type exit) to go to the next test.
DIR="$(cd "$(dirname "$0")" && pwd)"
RUN="$DIR/../run.sh"
LOG="$DIR/logs/params.csv"
rm -f "$LOG"

echo "=== 1. No parameters: default VFS name, no log, no script ==="
"$RUN"
echo "exit code: $?"

echo "=== 2. Only --vfs: VFS name in the window title ==="
"$RUN" --vfs "$DIR/vfs/minimal"
echo "exit code: $?"

echo "=== 3. --vfs, --log and --script together ==="
"$RUN" --vfs "$DIR/vfs/deep" --log "$LOG" \
    --script "$DIR/startup/demo.txt"
echo "exit code: $?"
echo "--- $LOG ---"
cat "$LOG"
