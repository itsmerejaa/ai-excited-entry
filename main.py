#!/usr/bin/env python3
"""Salin entry.png ke direktori output make.fun.

Sumber: entry.png di sebelah berkas ini (relatif terhadap __file__).
Tujuan: $MAKEFUN_OUTPUT_DIR (default /output), nama berkas tetap entry.png.
Direktori tujuan dibuat bila belum ada. Deterministik: byte disalin apa adanya.
"""
import os
import shutil
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent / "entry.png"
DST_DIR = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))
DST = DST_DIR / "entry.png"


def main() -> int:
    if not SRC.is_file():
        print(f"error: sumber tidak ditemukan: {SRC}", file=sys.stderr)
        return 1
    DST_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(SRC, DST)
    print(f"{SRC} -> {DST}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
