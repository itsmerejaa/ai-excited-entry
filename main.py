#!/usr/bin/env python3
"""Copy entry.png from this directory into the make.fun output directory.

The source is resolved relative to this file, the destination comes from the
MAKEFUN_OUTPUT_DIR environment variable and defaults to /output.  The output
directory is created if it does not exist yet.
"""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

DEFAULT_OUTPUT_DIR = "/output"
ARTIFACT_NAME = "entry.png"


def main() -> int:
    src = Path(__file__).resolve().parent / ARTIFACT_NAME
    if not src.is_file():
        print(f"error: missing source file {src}", file=sys.stderr)
        return 1

    out_dir = Path(os.environ.get("MAKEFUN_OUTPUT_DIR") or DEFAULT_OUTPUT_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)

    dst = out_dir / ARTIFACT_NAME
    shutil.copyfile(src, dst)
    print(f"copied {src} -> {dst} ({dst.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
