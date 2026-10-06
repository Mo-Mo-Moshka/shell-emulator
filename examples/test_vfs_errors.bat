@echo off
rem VFS loading errors: the error is shown and vfs-info reports it.
set "RUN=%~dp0..\run.bat"
set "INFO=%~dp0startup\vfs_info.txt"

echo === 1. VFS directory does not exist ===
call "%RUN%" --vfs "%~dp0vfs\no_such_vfs" --script "%INFO%"

echo === 2. VFS path is a file, not a directory ===
call "%RUN%" --vfs "%~dp0vfs\minimal\hello.txt" --script "%INFO%"

echo === 3. No --vfs parameter at all ===
call "%RUN%" --script "%INFO%"
