#!/bin/sh
# VFS variants: minimal, several files, 3+ levels of directories.
# Close the emulator window (or type exit) to go to the next test.
DIR="$(cd "$(dirname "$0")" && pwd)"
RUN="$DIR/../run.sh"
INFO="$DIR/startup/vfs_info.txt"
LOG="$DIR/logs/vfs.csv"
rm -f "$LOG"

echo "=== 1. Minimal VFS: a single file ==="
"$RUN" --vfs "$DIR/vfs/minimal" --script "$INFO"

echo "=== 2. VFS with several files ==="
"$RUN" --vfs "$DIR/vfs/several" --script "$INFO"

echo "=== 3. Deep VFS (4 levels): all commands of stages 1-3 ==="
"$RUN" --vfs "$DIR/vfs/deep" --log "$LOG" \
    --script "$DIR/startup/stage3.txt"
echo "--- $LOG ---"
cat "$LOG"
