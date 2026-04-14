import argparse

from common import (
    dumps_pretty,
    ensure_runtime_env,
    get_demo_ocr_input,
    get_demo_structure_input,
    normalize_device,
    run_ocr,
    run_structure,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Prefetch PaddleOCR models for offline use")
    parser.add_argument("--device", default=None, help="cpu or gpu:0")
    parser.add_argument(
        "--skip-structure",
        action="store_true",
        help="Only prefetch the general OCR pipeline",
    )
    args = parser.parse_args()

    ensure_runtime_env()
    device = normalize_device(args.device)

    print(f"Prefetching OCR models on {device} ...")
    ocr_payload = run_ocr(get_demo_ocr_input(), device=device)
    print(dumps_pretty({"pipeline": ocr_payload["pipeline"], "device": device, "text_preview": ocr_payload["text"][:200]}))

    if not args.skip_structure:
        print(f"Prefetching PP-StructureV3 models on {device} ...")
        structure_payload = run_structure(get_demo_structure_input(), device=device)
        print(dumps_pretty({"pipeline": structure_payload["pipeline"], "device": device, "result_count": len(structure_payload["results"])}))

    print("Model prefetch complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
