@echo off
setlocal
set "APP_DIR=%~dp0"

if not defined BAIDU_OCR_API_KEY set "BAIDU_OCR_API_KEY=xglZsyO373kGLQ6Ckw9CMVeT"
if not defined BAIDU_OCR_API_SECRET set "BAIDU_OCR_API_SECRET=tON1hwT2dfysLmkRqQm7gcOzhWxURV9f"

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

"%PYTHON_EXE%" "%APP_DIR%online_ocr.py" %*