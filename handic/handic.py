# handic/handic.py
from __future__ import annotations

from .paths import PATHS

# 互換用: 旧APIを維持（中身はpathsに委譲）
DICDIR = str(PATHS.dicdir())

# VERSIONもpathsに寄せたいなら、paths側に version() を生やしてもOK
VERSION = PATHS.version()
