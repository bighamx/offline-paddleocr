@echo off
setlocal
set "APP_DIR=%~dp0"
set "OCR_DEVICE=gpu:0"
if defined OCR_PYTHON (
  set "PYTHON_EXE=%OCR_PYTHON%"
) else if exist "%APP_DIR%.venv-gpu\Scripts\python.exe" (
  set "PYTHON_EXE=%APP_DIR%.venv-gpu\Scripts\python.exe"
) else if exist "%APP_DIR%..\..\runtime\.venv-gpu\Scripts\python.exe" (
  set "PYTHON_EXE=%APP_DIR%..\..\runtime\.venv-gpu\Scripts\python.exe"
) else (
  echo Python environment not found.
  echo Please create .venv-gpu in the repository root, or set OCR_PYTHON manually.
  exit /b 1
)
"%PYTHON_EXE%" "%APP_DIR%app.py" %*
