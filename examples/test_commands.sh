#!/bin/sh
# Stage 4 commands (ls, cd, rev, tac, date) on the deep VFS.
# Close the emulator window (or type exit) to go to the next test.
DIR="$(cd "$(dirname "$0")" && pwd)"
RUN="$DIR/../run.sh"
VFS="$DIR/vfs/deep"
LOG="$DIR/logs/commands.csv"
rm -f "$LOG"

echo "=== 1. All command modes: startup/stage4.txt ==="
"$RUN" --vfs "$VFS" --log "$LOG" --script "$DIR/startup/stage4.txt"

echo "=== 2. Error cases: each script stops at its error ==="
for script in "$DIR"/startup/errors/*.txt; do
    echo "--- $(basename "$script") ---"
    "$RUN" --vfs "$VFS" --log "$LOG" --script "$script"
done

echo "--- $LOG ---"
cat "$LOG"
