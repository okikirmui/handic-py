from __future__ import annotations

import csv
from functools import lru_cache
from typing import List, Tuple, Optional
import os
import sys
# from io import StringIO

from .paths import PATHS

try:
    import MeCab  # mecab-python3
except ImportError as e:
    raise ImportError("mecab-python3 is required. Install with: pip install mecab-python3") from e

try:
    import jamotools
except ImportError as e:
    raise ImportError("jamotools is required. Install with: pip install jamotools") from e


def to_jamo(text: str) -> str:
    """Convert Hangul syllables to Jamo string (JAMO) for HanDic."""
    return jamotools.split_syllables(text, jamo_type="JAMO")


def _quote_arg(p: str) -> str:
    """
    Quote/normalize an argument value for MeCab option string.

    - Always wrap with double quotes (handles spaces safely)
    - On Windows, convert backslashes to forward slashes to avoid escape issues
    """
    s = str(p)
    if os.name == "nt":
        s = s.replace("\\", "/")
    if not (s.startswith('"') and s.endswith('"')):
        s = f'"{s}"'
    return s


def mecab_args(dicdir: Optional[str] = None, extra_args: str = "", disable_rc: bool = True) -> str:
    """
    Build MeCab option string for HanDic (cross-platform stable).

    - disable_rc=True: disable default rc file by pointing -r to OS null device
      (Windows: nul, Linux/macOS: /dev/null)
    - dicdir is quoted and normalized to be robust on Windows + conda environments
    """
    parts: List[str] = []

    if disable_rc:
        parts += ["-r", _quote_arg(os.devnull)]

    if dicdir is None:
        dicdir = str(PATHS.dicdir())
    parts += ["-d", _quote_arg(dicdir)]

    if extra_args:
        parts.append(extra_args.strip())

    return " ".join(parts)
# A stable, user-friendly constant (many people will copy-paste this)
MECAB_ARGS = mecab_args()  # cross-platf@lru_cache(maxsize=8)
def get_tagger(extra_args: str = "", disable_rc: bool = True):
    """
    Cached MeCab.Tagger (cross-platform stable).

    - On Windows, /dev/null does not exist; we use os.devnull ("nul").
    - Quote/normalize dictionary path to avoid backslash/space issues in conda.
    - Call tagger.parse("") to prevent GC-related issues in some bindings.
    """
    args = mecab_args(extra_args=extra_args, disable_rc=disable_rc)

    try:
        tagger = MeCab.Tagger(args)
        # Prevent GC-related issues in some bindings (common MeCab Python workaround)
        tagger.parse("")
        return tagger
    except Exception as e:
        # Provide helpful diagnostics without leaking too much noise
        msg = (
            "Failed to create MeCab.Tagger.\n"
            f"Args: {args}\n"
            f"os.name={os.name}, platform={sys.platform}\n"
            "Hints:\n"
            "- Verify the dictionary directory exists and is a MeCab dictionary (often contains dicrc).\n"
            "- If using conda on Windows, ensure mecab/dictionary binaries match Python architecture (64-bit vs 32-bit).\n"
            "- Paths with spaces must be quoted; this module quotes them automatically.\n"
        )
        raise RuntimeError(msg) from e
    return tagger


def parse(text: str, *, tagger=None, extra_args: str = "", jamo: bool = True) -> str:
    """
    Return MeCab raw output.
    """
    if tagger is None:
        tagger = get_tagger(extra_args=extra_args)
    src = to_jamo(text) if jamo else text
    return tagger.parse(src)


def pos(text: str, *, tagger=None, extra_args: str = "", jamo: bool = True) -> List[Tuple[str, str]]:
    """
    Return list of (surface, pos).
    Assumes MeCab feature format where the first CSV field is coarse POS.
    """
    out = parse(text, tagger=tagger, extra_args=extra_args, jamo=jamo)
    res: List[Tuple[str, str]] = []

    for line in out.splitlines():
        if not line or line == "EOS":
            continue
        if "\t" not in line:
            continue
        surface, feat = line.split("\t", 1)
        coarse = feat.split(",", 1)[0]
        res.append((surface, coarse))
    return res


def _parse_feature_csv(feat: str) -> List[str]:
    return next(csv.reader([feat], delimiter=",", quotechar='"', escapechar="\\"))

def _is_missing(x: str) -> bool:
    # HanDic/MeCab系でよくある欠損表現をまとめて判定
    return (x is None) or (x == "") or (x == "*")

def _to_hangul_best_effort(surface: str) -> str:
    """
    Jamoっぽい場合は join_jamos で復元。無理ならそのまま返す。
    """
    try:
        # join_jamos は非Jamo文字列にも基本的に無害（そのままに近い）
        return jamotools.join_jamos(surface)
    except Exception:
        return surface

def pos_tag(
    text: str, *, tagger=None, extra_args: str = "", jamo: bool = True,
    unknown_fallback: str = "hangul_surface",  # "surface" | "hangul_surface" | "keep_base_*"
) -> List[Tuple[str, str]]:
    """
    Return list of (base_or_surface, pos-tag).

    - base is fields[5]
    - pos  is fields[10] (your HanDic format)
    - If base is missing ('*' etc.), fallback to surface.
      Optionally convert surface Jamo -> Hangul.

    unknown_fallback:
      - "surface": return raw surface (may be Jamo)
      - "hangul_surface": return surface converted to Hangul when possible
      - "keep_base_*": keep '*' as-is (no fallback)
    """
    out = parse(text, tagger=tagger, extra_args=extra_args, jamo=jamo)
    res: List[Tuple[str, str]] = []

    for line in out.splitlines():
        if not line or line == "EOS":
            continue
        if "\t" not in line:
            continue

        surface, feat = line.split("\t", 1)
        fields = _parse_feature_csv(feat)

        base = fields[5] if len(fields) > 5 else "*"
        pos  = fields[10] if len(fields) > 10 else "*"

        if _is_missing(base):
            if unknown_fallback == "keep_base_*":
                token = base
            elif unknown_fallback == "surface":
                token = surface
            else:  # "hangul_surface"
                token = _to_hangul_best_effort(surface)
        else:
            token = base

        res.append((token, pos))

    return res


def tokenize(text: str, *, tagger=None, extra_args: str = "", jamo: bool = True) -> List[str]:
    """Return token list (surface only)."""
    return [w for (w, _) in pos(text, tagger=tagger, extra_args=extra_args, jamo=jamo)]


def tokenize_hangul(text: str, *, tagger=None, extra_args: str = "", mode: str = "base") -> List[str]:
    if mode == "base":
        return [tok for (tok, _pos) in pos_tag(
            text, tagger=tagger, extra_args=extra_args, jamo=True, unknown_fallback="hangul_surface"
        )]
    else:
        toks = tokenize(text, tagger=tagger, extra_args=extra_args, jamo=True)
        return [_to_hangul_best_effort(t) for t in toks]


def convert_text_to_hanja_hangul(
    text: str, *,
    tagger=None,
    extra_args: str = "",
    jamo_input: bool = True,
) -> str:
    """
    HanDicのfeature[7]（8番目）を使って、可能なものは漢字表記へ置換し、
    それ以外はsurfaceを使い、空白等も保持したまま連結。
    最後に join_jamos() で「漢字＋完成形ハングル」に整形して返す。

    - index 7 が '*'（欠損）なら surface を採用
    - index 7 があるならそれを採用（例: '眞짜'）
    - 入力全文を一度に解析するので、空白分割による連接変化を回避
    """
    if tagger is None:
        tagger = get_tagger(extra_args=extra_args)

    src = to_jamo(text) if jamo_input else text  # ここはあなたの現行設計に合わせる
    node = tagger.parseToNode(src)

    out_parts: List[str] = []
    idx = 0  # src上の現在位置

    while node:
        # BOS/EOSは飛ばす
        if node.stat in (2, 3):  # 2=BOS, 3=EOS (mecab-python3)
            node = node.next
            continue

        surface = node.surface or ""
        feat = node.feature or ""

        # 1) 次のトークンの前にある空白（+必要なら他の文字）をそのままコピーして位置合わせ
        #    通常、MeCabは空白をノードにしないのでここで補完する
        while idx < len(src) and src[idx].isspace():
            out_parts.append(src[idx])
            idx += 1

        # 2) 期待位置にsurfaceが来ていない場合の救済（まれにズレる環境対策）
        if surface and not src.startswith(surface, idx):
            found = src.find(surface, idx)
            if found != -1:
                # 間にある空白や記号などを一応コピー
                out_parts.append(src[idx:found])
                idx = found
            # 見つからない場合は無理に合わせず、そのまま進める（最悪でもトークン連結は可能）

        # 3) feature[7] を優先、欠損なら surface
        fields = _parse_feature_csv(feat)
        hanja_mix = fields[7] if len(fields) > 7 else "*"

        token = hanja_mix if not _is_missing(hanja_mix) else surface
        out_parts.append(token)

        # 4) src上の位置を進める（surface分だけ）
        if surface and src.startswith(surface, idx):
            idx += len(surface)

        node = node.next

    # 5) 末尾の空白などを追加
    if idx < len(src):
        out_parts.append(src[idx:])

    # 6) 最後にまとめて「Jamo部分だけ」完成形ハングルへ（漢字や空白は保持される）
    try:
        return jamotools.join_jamos("".join(out_parts))
    except Exception:
        return "".join(out_parts)
