@echo off
rem Command line parameters: none, only --vfs, all three together.
rem Close the emulator window (or type exit) to go to the next test.
set "RUN=%~dp0..\run.bat"
set "LOG=%~dp0logs\params.csv"
if exist "%LOG%" del "%LOG%"

echo === 1. No parameters: default VFS name, no log, no script ===
call "%RUN%"
echo exit code: %ERRORLEVEL%

echo === 2. Only --vfs: VFS name in the window title ===
call "%RUN%" --vfs "%~dp0vfs\minimal"
echo exit code: %ERRORLEVEL%

echo === 3. --vfs, --log and --script together ===
call "%RUN%" --vfs "%~dp0vfs\deep" --log "%LOG%" ^
    --script "%~dp0startup\demo.txt"
echo exit code: %ERRORLEVEL%
echo --- %LOG% ---
type "%LOG%"
