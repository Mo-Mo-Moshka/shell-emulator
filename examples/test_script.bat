@echo off
rem Startup script: exit from script, stop at first error, missing file.
set "RUN=%~dp0..\run.bat"
set "LOG=%~dp0logs\script.csv"
if exist "%LOG%" del "%LOG%"

echo === 1. Script ends with "exit 3": window closes by itself ===
call "%RUN%" --log "%LOG%" --script "%~dp0startup\exit.txt"
echo exit code: %ERRORLEVEL% (expected 3)

echo === 2. Script with an error: stops at line 4 ===
call "%RUN%" --log "%LOG%" --script "%~dp0startup\error.txt"
echo exit code: %ERRORLEVEL%

echo === 3. Script file does not exist ===
call "%RUN%" --log "%LOG%" --script "%~dp0startup\missing.txt"
echo exit code: %ERRORLEVEL%

echo --- %LOG% ---
type "%LOG%"
