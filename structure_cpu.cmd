@echo off
setlocal
set "APP_DIR=%~dp0"
set "OCR_DEVICE=cpu"
"%APP_DIR%..\..\runtime\.venv-cpu\Scripts\python.exe" "%APP_DIR%cli.py" structure %*
