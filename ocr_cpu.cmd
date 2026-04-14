@echo off
setlocal
set "APP_DIR=%~dp0"
set "OCR_DEVICE=cpu"
if defined OCR_PYTHON (
  set "PYTHON_EXE=%OCR_PYTHON%"
) else if exist "%APP_DIR%.venv-cpu\Scripts\python.exe" (
  set "PYTHON_EXE=%APP_DIR%.venv-cpu\Scripts\python.exe"
) else if exist "%APP_DIR%..\..\runtime\.venv-cpu\Scripts\python.exe" (
  set "PYTHON_EXE=%APP_DIR%..\..\runtime\.venv-cpu\Scripts\python.exe"
) else (
  echo Python environment not found.
  echo Please create .venv-cpu in the repository root, or set OCR_PYTHON manually.
  exit /b 1
)
"%PYTHON_EXE%" "%APP_DIR%cli.py" ocr %*
