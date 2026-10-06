@echo off
rem Stage 5 commands (rm, rmdir) on the deep VFS.
rem Close the emulator window (or type exit) to go to the next test.
set "RUN=%~dp0..\run.bat"
set "VFS=%~dp0vfs\deep"
set "LOG=%~dp0logs\modify.csv"
if exist "%LOG%" del "%LOG%"

echo === 1. All modes of rm and rmdir: startup\stage5.txt ===
call "%RUN%" --vfs "%VFS%" --log "%LOG%" --script "%~dp0startup\stage5.txt"

echo === 2. Error cases: each script stops at its error ===
for %%f in ("%~dp0startup\errors\rm*.txt") do (
    echo --- %%~nxf ---
    call "%RUN%" --vfs "%VFS%" --log "%LOG%" --script "%%~ff"
)

echo === 3. Files on disk are unchanged (all changes were in memory) ===
dir /s /b "%VFS%"

echo --- %LOG% ---
type "%LOG%"
