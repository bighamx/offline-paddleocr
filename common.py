import json
import os
import tempfile
import base64
import urllib.error
import urllib.parse
import urllib.request
from functools import lru_cache
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent
WORKSPACE_DIR = BASE_DIR.parent.parent
PADDLEOCR_REPO_DIR = WORKSPACE_DIR / "PaddleOCR"
MODELS_DIR = BASE_DIR / "models"
PADDLEX_CACHE_DIR = MODELS_DIR / "paddlex_cache"
UPLOAD_DIR = BASE_DIR / "uploads"
DEFAULT_MODEL_SOURCE = "modelscope"
SUPPORTED_MODEL_SOURCES = {"modelscope", "huggingface", "aistudio"}
BAIDU_OCR_TOKEN_URL = "https://aip.baidubce.com/oauth/2.0/token"
BAIDU_OCR_ACCURATE_URL = "https://aip.baidubce.com/rest/2.0/ocr/v1/accurate_basic"


def ensure_runtime_env() -> None:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    PADDLEX_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("PADDLE_PDX_CACHE_HOME", str(PADDLEX_CACHE_DIR))
    os.environ.setdefault(
        "PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK",
        os.environ.get("OCR_DISABLE_SOURCE_CHECK", "True"),
    )
    os.environ.setdefault("PADDLE_PDX_MODEL_SOURCE", get_model_source())


def normalize_device(device: str | None) -> str:
    if not device:
        return os.environ.get("OCR_DEVICE", "cpu")
    return device


def get_baidu_api_key() -> str:
    return os.environ.get("BAIDU_OCR_API_KEY", "")


def get_baidu_api_secret() -> str:
    return os.environ.get("BAIDU_OCR_API_SECRET", "")


def _http_json_request(url: str, data: bytes | None = None, headers: dict[str, str] | None = None) -> dict[str, Any]:
    request = urllib.request.Request(url, data=data, headers=headers or {}, method="POST" if data is not None else "GET")
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            payload = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        error_text = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"HTTP {exc.code} from {url}: {error_text or exc.reason}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Failed to call {url}: {exc.reason}") from exc
    return json.loads(payload)


def get_baidu_access_token(api_key: str | None = None, api_secret: str | None = None) -> str:
    key = api_key or get_baidu_api_key()
    secret = api_secret or get_baidu_api_secret()
    if not key or not secret:
        raise ValueError(
            "Baidu OCR credentials are missing. Set BAIDU_OCR_API_KEY and BAIDU_OCR_API_SECRET."
        )
    query = urllib.parse.urlencode(
        {
            "grant_type": "client_credentials",
            "client_id": key,
            "client_secret": secret,
        }
    )
    response = _http_json_request(f"{BAIDU_OCR_TOKEN_URL}?{query}")
    token = response.get("access_token")
    if not token:
        raise RuntimeError(f"Baidu token response did not include access_token: {response}")
    return str(token)


def run_online_ocr(
    input_path: str | Path,
    api_key: str | None = None,
    api_secret: str | None = None,
) -> dict[str, Any]:
    file_path = Path(input_path)
    image_bytes = file_path.read_bytes()
    encoded_image = base64.b64encode(image_bytes).decode("ascii")
    access_token = get_baidu_access_token(api_key=api_key, api_secret=api_secret)
    request_body = urllib.parse.urlencode({"image": encoded_image}).encode("utf-8")
    response = _http_json_request(
        f"{BAIDU_OCR_ACCURATE_URL}?access_token={urllib.parse.quote(access_token)}",
        data=request_body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    words_result = response.get("words_result", [])
    text_lines = []
    if isinstance(words_result, list):
        for item in words_result:
            if isinstance(item, dict):
                word = item.get("words")
                if word:
                    text_lines.append(str(word))
    response["text"] = "\n".join(text_lines)
    return {
        "pipeline": "baidu_accurate_basic",
        "input_path": str(file_path),
        "text": response["text"],
        "result": response,
    }


def get_model_source() -> str:
    source = (
        os.environ.get("OCR_MODEL_SOURCE")
        or os.environ.get("PADDLE_PDX_MODEL_SOURCE")
        or DEFAULT_MODEL_SOURCE
    ).lower()
    if source not in SUPPORTED_MODEL_SOURCES:
        raise ValueError(
            f"Unsupported model source: {source}. "
            f"Supported values: {sorted(SUPPORTED_MODEL_SOURCES)}"
        )
    return source


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
