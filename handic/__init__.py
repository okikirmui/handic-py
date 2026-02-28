# handic/__init__.py
from __future__ import annotations

# Low-level / compatibility
from .handic import DICDIR, VERSION

# Paths (New canonical way)
from .paths import PATHS

# High-level APIs
from .highlevel import (
    MECAB_ARGS,
    get_tagger,
    mecab_args,
    parse,
    pos,
    pos_tag,
    tokenize,
    tokenize_hangul,
    to_jamo,
    convert_text_to_hanja_hangul,
)

__all__ = [
    # Compatibility / low-level
    "DICDIR",
    "VERSION",

    # Paths
    "PATHS",

    # High-level
    "MECAB_ARGS",
    "get_tagger",
    "mecab_args",
    "parse",
    "pos",
    "pos_tag",
    "tokenize",
    "tokenize_hangul",
    "to_jamo",
    "convert_text_to_hanja_hangul",
]
