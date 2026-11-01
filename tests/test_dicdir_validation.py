from pathlib import Path

import pytest

import handic
import handic.highlevel as highlevel


TEXT = "한국어를 공부합니다."

# Cover all six APIs, including both tokenize_hangul modes.
API_CASES = [
    ("parse", {}),
    ("pos", {}),
    ("pos_tag", {}),
    ("tokenize", {}),
    ("tokenize_hangul", {"mode": "base"}),
    ("tokenize_hangul", {"mode": "surface"}),
    ("convert_text_to_hanja_hangul", {}),
]


@pytest.fixture(autouse=True)
def reset_tagger_cache():
    """Prevent cached Taggers from leaking between tests."""
    handic.clear_tagger_cache()
    yield
    handic.clear_tagger_cache()


@pytest.mark.parametrize("name,kwargs", API_CASES)
def test_bundled_dictionary_matches_explicit_path(name, kwargs):
    """All APIs must accept an explicit bundled dictionary path."""
    api = getattr(handic, name)

    expected = api(TEXT, **kwargs)
    actual = api(
        TEXT,
        dicdir=Path(handic.DICDIR),
        **kwargs,
    )

    assert actual == expected


@pytest.mark.parametrize("name,kwargs", API_CASES)
def test_supplied_tagger_takes_priority(
    name, kwargs, monkeypatch, tmp_path
):
    """A supplied Tagger must bypass dicdir and extra_args."""
    api = getattr(handic, name)
    tagger = handic.get_tagger()
    expected = api(TEXT, tagger=tagger, **kwargs)

    def unexpected_get_tagger(*args, **kwargs):
        pytest.fail("get_tagger() was called despite supplied tagger")

    monkeypatch.setattr(
        highlevel, "get_tagger", unexpected_get_tagger
    )

    actual = api(
        TEXT,
        tagger=tagger,
        dicdir=tmp_path / "missing-dictionary",
        extra_args="--invalid-option-for-priority-test",
        **kwargs,
    )

    assert actual == expected


@pytest.fixture(params=["missing", "file", "empty", "broken"])
def invalid_dicdir(request, tmp_path):
    """Prepare several invalid dictionary locations."""
    path = tmp_path / request.param

    if request.param == "file":
        path.write_text("not a directory", encoding="utf-8")

    elif request.param == "empty":
        path.mkdir()

    elif request.param == "broken":
        path.mkdir()
        for filename in (
            "dicrc",
            "sys.dic",
            "unk.dic",
            "matrix.bin",
            "char.bin",
        ):
            (path / filename).write_bytes(b"invalid dictionary data")

    return path


def test_invalid_dictionary_has_diagnostic_information(invalid_dicdir):
    """Failures must identify the path and preserve the original error."""
    with pytest.raises(RuntimeError) as exc_info:
        handic.get_tagger(dicdir=invalid_dicdir)

    assert str(invalid_dicdir.resolve()) in str(exc_info.value)
    assert exc_info.value.__cause__ is not None


@pytest.mark.parametrize("name,kwargs", API_CASES)
def test_apis_reject_invalid_dictionary(name, kwargs, tmp_path):
    """APIs must not silently fall back to the bundled dictionary."""
    api = getattr(handic, name)

    with pytest.raises(RuntimeError):
        api(
            TEXT,
            dicdir=tmp_path / "missing-dictionary",
            **kwargs,
        )


def test_equivalent_paths_share_cached_tagger(monkeypatch):
    """Path objects, strings and relative paths select the same cache entry."""
    dicdir = Path(handic.DICDIR).resolve()
    monkeypatch.chdir(dicdir.parent)

    expected = handic.get_tagger(dicdir=dicdir)

    assert handic.get_tagger(dicdir=str(dicdir)) is expected
    assert handic.get_tagger(dicdir=Path(dicdir.name)) is expected
    assert handic.get_tagger(dicdir=f"./{dicdir.name}/") is expected


def test_relative_path_is_resolved_after_chdir(tmp_path, monkeypatch):
    """
    The same relative path must be reinterpreted after chdir.

    A fake Tagger isolates path/cache behavior from dictionary loading.
    """
    class FakeTagger:
        def __init__(self, args):
            self.args = args

        def parse(self, text):
            return "EOS\n"

    monkeypatch.setattr(highlevel.MeCab, "Tagger", FakeTagger)

    first_dir = tmp_path / "first"
    second_dir = tmp_path / "second"

    for directory in (first_dir, second_dir):
        (directory / "dictionary").mkdir(parents=True)

    monkeypatch.chdir(first_dir)
    first = handic.get_tagger(dicdir="dictionary")

    monkeypatch.chdir(second_dir)
    second = handic.get_tagger(dicdir="dictionary")

    assert first is not second
    assert highlevel._quote_arg(
        str((first_dir / "dictionary").resolve())
    ) in first.args
    assert highlevel._quote_arg(
        str((second_dir / "dictionary").resolve())
    ) in second.args


def test_clear_cache_creates_new_tagger():
    """Clearing the cache must affect subsequent get_tagger calls."""
    first = handic.get_tagger()
    assert handic.get_tagger() is first

    handic.clear_tagger_cache()
    second = handic.get_tagger()

    assert second is not first
    assert handic.get_tagger() is second

    # Existing references remain usable after cache clearing.
    assert first.parse(highlevel.to_jamo(TEXT)) == second.parse(
        highlevel.to_jamo(TEXT)
    )


def test_positional_extra_args():
    """Preserve the positional extra_args calling convention."""
    tagger = handic.get_tagger("-Owakati")

    output = tagger.parse(highlevel.to_jamo(TEXT))

    assert output.strip()
    assert "\t" not in output
    assert "EOS" not in output.splitlines()


@pytest.mark.parametrize("mode", ["surfase", "", "BASE", None])
def test_invalid_tokenize_hangul_mode(mode):
    """Reject invalid modes before creating a Tagger."""
    with pytest.raises(ValueError, match="mode"):
        handic.tokenize_hangul(TEXT, mode=mode)
