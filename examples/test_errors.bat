@echo off
rem Invalid command line parameters.
set "RUN=%~dp0..\run.bat"

echo === 1. Help on parameters ===
call "%RUN%" --help
echo exit code: %ERRORLEVEL%

echo === 2. Unknown parameter: emulator does not start ===
call "%RUN%" --color red
echo exit code: %ERRORLEVEL% (expected 2)

echo === 3. Parameter without a value ===
call "%RUN%" --log
echo exit code: %ERRORLEVEL% (expected 2)

echo === 4. Log path is a directory: error shown, emulator works ===
call "%RUN%" --log "%~dp0startup"
echo exit code: %ERRORLEVEL%
