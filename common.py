import json
import os
import tempfile
from functools import lru_cache
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent
WORKSPACE_DIR = BASE_DIR.parent.parent
PADDLEOCR_REPO_DIR = WORKSPACE_DIR / "PaddleOCR"
MODELS_DIR = BASE_DIR / "models"
PADDLEX_CACHE_DIR = MODELS_DIR / "paddlex_cache"
UPLOAD_DIR = BASE_DIR / "uploads"


def ensure_runtime_env() -> None:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    PADDLEX_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("PADDLE_PDX_CACHE_HOME", str(PADDLEX_CACHE_DIR))
    os.environ.setdefault("PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK", "True")
    os.environ.setdefault("PADDLE_PDX_MODEL_SOURCE", "huggingface")


def normalize_device(device: str | None) -> str:
    if not device:
        return os.environ.get("OCR_DEVICE", "cpu")
    return device


def get_demo_ocr_input() -> Path:
    return PADDLEOCR_REPO_DIR / "tests" / "test_files" / "book.jpg"


def get_demo_structure_input() -> Path:
    return PADDLEOCR_REPO_DIR / "tests" / "test_files" / "table.jpg"


def save_upload(filename: str, data: bytes) -> Path:
    suffix = Path(filename or "upload.bin").suffix or ".bin"
    fd, path = tempfile.mkstemp(prefix="ocr_", suffix=suffix, dir=UPLOAD_DIR)
    with os.fdopen(fd, "wb") as handle:
        handle.write(data)
    return Path(path)


def _jsonify(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _jsonify(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonify(v) for v in value]
    if hasattr(value, "tolist"):
        return value.tolist()
    if isinstance(value, Path):
        return str(value)
    return value


def result_to_payload(result: Any) -> Any:
    if hasattr(result, "json"):
        return _jsonify(result.json)
    return _jsonify(result)


def extract_ocr_text(payload: Any) -> str:
    if isinstance(payload, list):
        return "\n".join(filter(None, (extract_ocr_text(item) for item in payload)))
    if not isinstance(payload, dict):
        return ""
    if "res" in payload:
        return extract_ocr_text(payload["res"])
    texts = payload.get("rec_texts")
    if isinstance(texts, list):
        return "\n".join(str(item) for item in texts)
    return ""


@lru_cache(maxsize=4)
def get_ocr_pipeline(device: str):
    ensure_runtime_env()
    from paddleocr import PaddleOCR

    return PaddleOCR(
        device=device,
        lang="ch",
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
        use_textline_orientation=False,
    )


@lru_cache(maxsize=4)
def get_structure_pipeline(device: str):
    ensure_runtime_env()
    from paddleocr import PPStructureV3

    return PPStructureV3(
        device=device,
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
    )


def run_ocr(input_path: str | Path, device: str | None = None) -> dict[str, Any]:
    device = normalize_device(device)
    pipeline = get_ocr_pipeline(device)
    results = pipeline.predict(str(input_path))
    payload = [result_to_payload(item) for item in results]
    return {
        "pipeline": "ocr",
        "device": device,
        "input_path": str(input_path),
        "text": extract_ocr_text(payload),
        "results": payload,
    }


def run_structure(input_path: str | Path, device: str | None = None) -> dict[str, Any]:
    device = normalize_device(device)
    pipeline = get_structure_pipeline(device)
    results = pipeline.predict(str(input_path))
    payload = [result_to_payload(item) for item in results]
    return {
        "pipeline": "pp_structurev3",
        "device": device,
        "input_path": str(input_path),
        "results": payload,
    }


def dumps_pretty(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2)
