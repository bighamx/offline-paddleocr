import argparse
import contextlib
import importlib
import logging
import os
import sys
import warnings
from pathlib import Path

from common import dumps_pretty, run_online_ocr


@contextlib.contextmanager
def suppress_stdout_stderr_fd():
    null_fd = os.open(os.devnull, os.O_RDWR)
    old_stdout, old_stderr = sys.stdout, sys.stderr
    sys.stdout = open(os.devnull, "w")
    sys.stderr = open(os.devnull, "w")

    try:
        save_fd_out = os.dup(1)
        save_fd_err = os.dup(2)
        os.dup2(null_fd, 1)
        os.dup2(null_fd, 2)
    except OSError:
        save_fd_out = save_fd_err = None

    try:
        yield
    finally:
        sys.stdout.flush()
        sys.stderr.flush()
        old_stdout.flush()
        old_stderr.flush()
        if save_fd_out is not None:
            os.dup2(save_fd_out, 1)
            os.close(save_fd_out)
        if save_fd_err is not None:
            os.dup2(save_fd_err, 2)
            os.close(save_fd_err)
        os.close(null_fd)
        sys.stdout.close()
        sys.stderr.close()
        sys.stdout, sys.stderr = old_stdout, old_stderr


def suppress_logs() -> None:
    os.environ["GLOG_minloglevel"] = "2"
    warnings.filterwarnings("ignore")
    logging.getLogger().setLevel(logging.ERROR)
    try:
        import paddlex.utils.logging as px_logging

        px_logging.setup_logging("ERROR")
    except ImportError:
        pass


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Baidu Online OCR CLI")
    parser.add_argument("-i", "--input", required=True, help="Input image path")
    parser.add_argument("-o", "--output", default=None, help="Output file path")
    parser.add_argument("--json", action="store_true", help="Output raw JSON instead of plain text")
    parser.add_argument("--debug", action="store_true", help="Enable debug output")
    parser.add_argument("--api-key", default=None, help="Baidu OCR API key. Defaults to BAIDU_OCR_API_KEY.")
    parser.add_argument(
        "--api-secret",
        default=None,
        help="Baidu OCR API secret. Defaults to BAIDU_OCR_API_SECRET.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if not args.debug:
        suppress_logs()

    with suppress_stdout_stderr_fd() if not args.debug else contextlib.nullcontext():
        payload = run_online_ocr(args.input, api_key=args.api_key, api_secret=args.api_secret)
        default_text = payload.get("text", "")

    text = dumps_pretty(payload) if args.json else default_text
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(text, encoding="utf-8")
        print(f"Saved result to: {output_path}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())