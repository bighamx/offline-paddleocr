import argparse
from pathlib import Path

from common import dumps_pretty, run_ocr, run_structure


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Offline PaddleOCR CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    for name in ("ocr", "structure"):
        sub = subparsers.add_parser(name)
        sub.add_argument("-i", "--input", required=True, help="Input image or PDF path")
        sub.add_argument(
            "--device",
            default=None,
            help="Device such as cpu or gpu:0. Defaults to OCR_DEVICE env or cpu.",
        )
        sub.add_argument("-o", "--output", default=None, help="Output JSON path")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "ocr":
        payload = run_ocr(args.input, device=args.device)
    else:
        payload = run_structure(args.input, device=args.device)

    text = dumps_pretty(payload)
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
