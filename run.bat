@echo off
REM Thin wrapper so double-clicking or `run.bat` just works. Logic is in sidemdm.py.
python "%~dp0sidemdm.py" %*
