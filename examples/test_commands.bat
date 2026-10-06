@echo off
rem Stage 4 commands (ls, cd, rev, tac, date) on the deep VFS.
rem Close the emulator window (or type exit) to go to the next test.
set "RUN=%~dp0..\run.bat"
set "VFS=%~dp0vfs\deep"
set "LOG=%~dp0logs\commands.csv"
if exist "%LOG%" del "%LOG%"

echo === 1. All command modes: startup\stage4.txt ===
call "%RUN%" --vfs "%VFS%" --log "%LOG%" --script "%~dp0startup\stage4.txt"

echo === 2. Error cases: each script stops at its error ===
for %%f in ("%~dp0startup\errors\*.txt") do (
    echo --- %%~nxf ---
    call "%RUN%" --vfs "%VFS%" --log "%LOG%" --script "%%~ff"
)

echo --- %LOG% ---
type "%LOG%"
