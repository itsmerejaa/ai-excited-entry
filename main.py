#!/usr/bin/env python3
"""ai-excited-01 — salin entry.png ke direktori output.

Menyalin file entry.png yang berada di sebelah file ini ke direktori yang
ditunjuk env MAKEFUN_OUTPUT_DIR (default: /output), dengan nama entry.png.
Deterministik, stdlib saja, jalan jauh di bawah 60 detik.
"""
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "entry.png")
NAME = "entry.png"


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    out_dir = os.path.abspath(os.path.expanduser(out_dir))

    if not os.path.isfile(SRC):
        print("error: %s tidak ditemukan" % SRC, file=sys.stderr)
        return 1

    os.makedirs(out_dir, exist_ok=True)
    dst = os.path.join(out_dir, NAME)
    shutil.copyfile(SRC, dst)

    print("%s -> %s (%d bytes)" % (SRC, dst, os.path.getsize(dst)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
