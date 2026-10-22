from app.chapters import is_chapter_heading


def test_numbered_heading():
    assert is_chapter_heading("Chapter 1")


def test_roman_numeral_heading():
    assert is_chapter_heading("CHAPTER XII")


def test_sentence_is_not_heading():
    assert not is_chapter_heading("Chapter and verse, she said")
