from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from .dictparser import DictParser


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Read and resolve dictionary/JSON/YAML configuration files.")
    parser.add_argument("file", help="Input configuration file (.json, .yaml, .yml)")
    parser.add_argument("-k", "--key", help="Dot-separated key path to resolve")
    parser.add_argument("-o", "--output", help="Output file path to save the result")
    parser.add_argument(
        "-f",
        "--format",
        choices=["json", "yaml"],
        help="Force output format. If omitted, infer from output file extension; default is json.",
    )
    return parser


def _to_text(value: Any) -> str:
    if isinstance(value, (dict, list, tuple, set)):
        parser = DictParser({})
        return parser.to_json(value)
    return str(value)


def main() -> int:
    args = _build_parser().parse_args()
    parser = DictParser(args.file)

    value = parser.get(args.key) if args.key else parser.get_all()

    if args.output:
        parser.save(Path(args.output), data=value, format=args.format)
    else:
        print(_to_text(value))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
