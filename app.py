from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile

from common import (
    PADDLEX_CACHE_DIR,
    dumps_pretty,
    ensure_runtime_env,
    get_model_source,
    normalize_device,
    run_ocr,
    run_structure,
    save_upload,
)

ensure_runtime_env()

app = FastAPI(title="Offline PaddleOCR", version="1.0.0")


@app.get("/health")
def health(device: str | None = None):
    return {
        "ok": True,
        "device": normalize_device(device),
        "model_source": get_model_source(),
        "cache_dir": str(PADDLEX_CACHE_DIR),
    }


@app.post("/ocr")
async def ocr(
    file: UploadFile = File(...),
    device: str | None = Form(default=None),
):
    try:
        local_path = save_upload(file.filename or "input.bin", await file.read())
        return run_ocr(local_path, device=device)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/structure")
async def structure(
    file: UploadFile = File(...),
    device: str | None = Form(default=None),
):
    try:
        local_path = save_upload(file.filename or "input.bin", await file.read())
        return run_structure(local_path, device=device)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


if __name__ == "__main__":
    import os

    import uvicorn

    host = os.environ.get("OCR_HOST", "127.0.0.1")
    port = int(os.environ.get("OCR_PORT", "18080"))
    uvicorn.run("app:app", host=host, port=port, reload=False)
