@echo off
rem VFS variants: minimal, several files, 3+ levels of directories.
rem Close the emulator window (or type exit) to go to the next test.
set "RUN=%~dp0..\run.bat"
set "INFO=%~dp0startup\vfs_info.txt"
set "LOG=%~dp0logs\vfs.csv"
if exist "%LOG%" del "%LOG%"

echo === 1. Minimal VFS: a single file ===
call "%RUN%" --vfs "%~dp0vfs\minimal" --script "%INFO%"

echo === 2. VFS with several files ===
call "%RUN%" --vfs "%~dp0vfs\several" --script "%INFO%"

echo === 3. Deep VFS (4 levels): all commands of stages 1-3 ===
call "%RUN%" --vfs "%~dp0vfs\deep" --log "%LOG%" ^
    --script "%~dp0startup\stage3.txt"
echo --- %LOG% ---
type "%LOG%"
