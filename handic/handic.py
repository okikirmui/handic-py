# handic/handic.py
from __future__ import annotations

from .paths import PATHS

# 互換用: 旧APIを維持（中身はpathsに委譲）
# Windows ではバックスラッシュがMeCab引数で事故りやすいので / に正規化した文字列も提供
DICDIR = getattr(PATHS, "dicdir_for_mecab", lambda: str(PATHS.dicdir()))()

# VERSIONもpathsに寄せたいなら、paths側に version() を生やしてもOK
VERSION = PATHS.version()
