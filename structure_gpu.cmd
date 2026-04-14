@echo off
setlocal
set "APP_DIR=%~dp0"
set "OCR_DEVICE=gpu:0"
"%APP_DIR%..\..\runtime\.venv-gpu\Scripts\python.exe" "%APP_DIR%cli.py" structure %*
