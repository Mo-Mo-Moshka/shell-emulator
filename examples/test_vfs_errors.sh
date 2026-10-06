#!/bin/sh
# VFS loading errors: the error is shown and vfs-info reports it.
DIR="$(cd "$(dirname "$0")" && pwd)"
RUN="$DIR/../run.sh"
INFO="$DIR/startup/vfs_info.txt"

echo "=== 1. VFS directory does not exist ==="
"$RUN" --vfs "$DIR/vfs/no_such_vfs" --script "$INFO"

echo "=== 2. VFS path is a file, not a directory ==="
"$RUN" --vfs "$DIR/vfs/minimal/hello.txt" --script "$INFO"

echo "=== 3. No --vfs parameter at all ==="
"$RUN" --script "$INFO"
