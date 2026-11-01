import os
from pathlib import Path

import pytest

import handic


TEXT = "총비서동지께서 말씀하시였다."

API_CASES = [
    ("parse", {}),
    ("pos", {}),
    ("pos_tag", {}),
    ("tokenize", {}),
    ("tokenize_hangul", {"mode": "base"}),
    ("tokenize_hangul", {"mode": "surface"}),
    ("convert_text_to_hanja_hangul", {}),
]


@pytest.fixture(scope="module")
def nk_dicdir():
    value = os.environ.get("NKHANDIC_DICDIR")

    # Explicit integration runs must fail instead of silently skipping.
    if not value:
        pytest.fail("Set NKHANDIC_DICDIR before running integration tests")

    path = Path(value).expanduser().resolve()
    if not (path / "sys.dic").is_file():
        pytest.fail(f"sys.dic was not found in: {path}")

    return path


@pytest.fixture(autouse=True)
def reset_cache():
    handic.clear_tagger_cache()
    yield
    handic.clear_tagger_cache()


def test_nk_dictionary_is_actually_loaded(nk_dicdir):
    tagger = handic.get_tagger(dicdir=nk_dicdir)
    info = tagger.dictionary_info()

    # MeCab dictionary type 0 denotes the system dictionary.
    system_dictionaries = []
    while info is not None:
        if info.type == 0:
            system_dictionaries.append(Path(info.filename).resolve())
        info = info.next

    assert system_dictionaries == [
        (nk_dicdir / "sys.dic").resolve()
    ]


@pytest.mark.parametrize("name,kwargs", API_CASES)
def test_nk_dicdir_matches_explicit_tagger(nk_dicdir, name, kwargs):
    api = getattr(handic, name)
    tagger = handic.get_tagger(dicdir=nk_dicdir)

    expected = api(TEXT, tagger=tagger, **kwargs)
    actual = api(TEXT, dicdir=nk_dicdir, **kwargs)

    assert actual == expected
    assert actual


@pytest.mark.parametrize("name,kwargs", API_CASES)
def test_dictionary_switching(nk_dicdir, name, kwargs):
    api = getattr(handic, name)

    han_before = api(TEXT, **kwargs)
    nk_result = api(TEXT, dicdir=nk_dicdir, **kwargs)
    han_after = api(TEXT, **kwargs)

    assert han_after == han_before

    # Returning to HanDic must not change the NK-HanDic result either.
    assert api(TEXT, dicdir=nk_dicdir, **kwargs) == nk_result


def test_nk_expected_pos_tags(nk_dicdir):
    """Expected values checked against the raw dictionary features."""
    expected = [
        ("총비서", "NNG"),
        ("동지006", "NNG"),
        ("께서", "JKS"),
        ("말씀", "NNG"),
        ("하다02", "XSV"),
        ("시", "EP"),
        ("ㅆ", "EP"),
        ("다06", "EF"),
        (".", "SF"),
    ]

    assert handic.pos_tag(TEXT, dicdir=nk_dicdir) == expected


def test_nk_expected_surface_tokens(nk_dicdir):
    """Expected Hangul composition of each raw surface token."""
    expected = [
        "총비서",
        "동지",
        "께서",
        "말씀",
        "하",
        "시여",
        "ㅆ",
        "다",
        ".",
    ]

    assert handic.tokenize_hangul(
        TEXT,
        mode="surface",
        dicdir=nk_dicdir,
    ) == expected
