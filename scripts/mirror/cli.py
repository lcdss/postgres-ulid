import argparse
import json
from pathlib import Path
from typing import Any


def matrix_payload(plan: list[dict[str, Any]]) -> str:
    return json.dumps({"include": plan}, sort_keys=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plan postgres-ulid mirror builds.")
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path to write the matrix payload.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = matrix_payload([])
    if args.output:
        args.output.write_text(payload, encoding="utf-8")
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
