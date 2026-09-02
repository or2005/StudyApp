"""שומר תאימות: python tools/build_exe.py → build_release.py"""
from __future__ import annotations

import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


if __name__ == "__main__":
    raise SystemExit(subprocess.call([sys.executable, os.path.join(HERE, "build_release.py"), *sys.argv[1:]]))
