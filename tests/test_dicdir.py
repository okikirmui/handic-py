import handic


TEXT = "한국어를 공부합니다."


def test_default_dictionary():
    result = handic.pos_tag(TEXT)

    assert result
    assert isinstance(result, list)


def test_explicit_bundled_dictionary():
    default = handic.pos_tag(TEXT)

    explicit = handic.pos_tag(
        TEXT,
        dicdir=handic.DICDIR,
    )

    assert default == explicit


def test_get_tagger_with_dicdir():
    tagger = handic.get_tagger(
        dicdir=handic.DICDIR
    )

    result = handic.pos_tag(
        TEXT,
        tagger=tagger,
    )

    assert result
