@echo off
rem Usage: run.bat         - start the emulator
rem        run.bat test    - run unit tests
set "PYTHONPATH=%~dp0src"
if /I "%~1"=="test" (
    python -m unittest discover -s "%~dp0tests" -v
) else (
    python "%~dp0src\main.py" %*
)
