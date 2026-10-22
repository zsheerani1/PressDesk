from app.chapters import is_chapter_heading, split_into_parts


def test_numbered_heading():
    assert is_chapter_heading("Chapter 1")


def test_roman_numeral_heading():
    assert is_chapter_heading("CHAPTER XII")


def test_sentence_is_not_heading():
    assert not is_chapter_heading("Chapter and verse, she said")

def test_short_text_stays_whole():
    assert split_into_parts("A short story.") == [
        ("Full manuscript", "A short story.")
    ]


def test_long_text_is_split_into_parts():
    text = "\n\n".join(["word " * 99 + "end."] * 100)  # 10,000 words
    parts = split_into_parts(text)
    assert len(parts) == 4
    assert parts[0][0] == "Part 1"