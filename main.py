#!/usr/bin/env python3
"""Publish the generated entry.png to the make.fun output directory.

Copies ./entry.png (resolved next to this file, not the CWD) into the
directory named by the MAKEFUN_OUTPUT_DIR environment variable, defaulting
to /output.  The destination directory is created if missing and the
filename is always entry.png.  Prints the size of what was written.

Python 3.13, standard library only.
"""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

DEFAULT_OUTPUT_DIR = "/output"
FILENAME = "entry.png"


def main() -> int:
    src = Path(__file__).resolve().parent / FILENAME
    if not src.is_file():
        print(f"error: missing source {src}", file=sys.stderr)
        return 1

    # MAKEFUN_OUTPUT_DIR unset, empty, or whitespace-only -> DEFAULT_OUTPUT_DIR
    raw = (os.environ.get("MAKEFUN_OUTPUT_DIR") or "").strip()
    out_dir = Path(raw) if raw else Path(DEFAULT_OUTPUT_DIR)
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        print(f"error: cannot create {out_dir}: {exc}", file=sys.stderr)
        return 1

    dst = out_dir / FILENAME
    if src.resolve() == dst.resolve():
        size = src.stat().st_size
        print(f"{dst} ({size} bytes, already in place)")
        return 0

    try:
        shutil.copyfile(src, dst)
    except OSError as exc:
        print(f"error: cannot write {dst}: {exc}", file=sys.stderr)
        return 1

    print(f"{dst} ({dst.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
