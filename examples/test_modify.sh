#!/bin/sh
# Stage 5 commands (rm, rmdir) on the deep VFS.
# Close the emulator window (or type exit) to go to the next test.
DIR="$(cd "$(dirname "$0")" && pwd)"
RUN="$DIR/../run.sh"
VFS="$DIR/vfs/deep"
LOG="$DIR/logs/modify.csv"
rm -f "$LOG"

echo "=== 1. All modes of rm and rmdir: startup/stage5.txt ==="
"$RUN" --vfs "$VFS" --log "$LOG" --script "$DIR/startup/stage5.txt"

echo "=== 2. Error cases: each script stops at its error ==="
for script in "$DIR"/startup/errors/rm*.txt; do
    echo "--- $(basename "$script") ---"
    "$RUN" --vfs "$VFS" --log "$LOG" --script "$script"
done

echo "=== 3. Files on disk are unchanged (all changes were in memory) ==="
find "$VFS"

echo "--- $LOG ---"
cat "$LOG"
