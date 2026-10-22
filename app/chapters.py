"""Read an uploaded manuscript file and split it into chapters.

The file is read in memory only; nothing is saved to disk.

A new chapter starts at:
- any line that starts with "Chapter" followed by a number, for example
  "Chapter 1", "Chapter One", "CHAPTER 3: The Ferry" or "Chapter XII"
  for example;
- in .docx files, any paragraph styled as "Heading 1".

PDF files have no heading styles, so they are split on "Chapter" lines
only, like .txt files.

If no chapter headings are found, the whole text becomes one chapter
called "Full manuscript".
"""

import io
import os
import re
import zipfile

from docx import Document
from docx.opc.exceptions import PackageNotFoundError
from pypdf import PdfReader
from pypdf.errors import DependencyError, PdfReadError


MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB
TOO_LARGE_MESSAGE = "The file is too large. The maximum size is 5 MB."

# "Chapter" followed by a number (1, 12), a number word (One, Twenty) or a
# Roman numeral (IV), ignoring case. Checking the word after "Chapter"
# stops sentences like "Chapter and verse, she said" counting as headings.
CHAPTER_HEADING = re.compile(
    r"chapter\s+(\d+|[ivxlc]+|one|two|three|four|five|six|seven|eight|"
    r"nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|"
    r"eighteen|nineteen|twenty|thirty|forty|fifty|sixty|seventy|eighty|"
    r"ninety|hundred)(?![a-z0-9])",
    re.IGNORECASE,
)

# Lines longer than this are treated as normal text, not headings.
MAX_HEADING_LENGTH = 100


class ManuscriptFileError(Exception):
    """Raised when an uploaded file cannot be turned into chapters.

    The message is written so it can be shown straight to the user.
    """

# Manuscripts with no chapter headings are split into parts of about


# this many words, so the reader doesn't get one very long page.
WORDS_PER_PART = 3000

# A part may end after a line that finishes a sentence.
SENTENCE_ENDINGS = (".", "!", "?", '"', "”", "'", "’")


def split_into_parts(text):
    """Split text with no headings into parts of about 3,000 words.

    Parts only end at a blank line or the end of a sentence, so no
    sentence is cut in half. Short texts stay as one "Full manuscript".
    """
    parts = []
    current_lines = []
    word_count = 0

    for line in text.split("\n"):
        current_lines.append(line)
        word_count += len(line.split())
        line_end = line.rstrip()
        at_break = not line_end or line_end.endswith(SENTENCE_ENDINGS)
        if word_count >= WORDS_PER_PART and at_break:
            parts.append("\n".join(current_lines).strip())
            current_lines = []
            word_count = 0

    leftover = "\n".join(current_lines).strip()
    if leftover:
        parts.append(leftover)

    if len(parts) <= 1:
        return [("Full manuscript", text)]
    return [
        (f"Part {number}", part)
        for number, part in enumerate(parts, start=1)
    ]


def is_chapter_heading(line):
    """Return True if a line of text looks like a chapter heading."""
    line = line.strip()
    return (len(line) <= MAX_HEADING_LENGTH
            and CHAPTER_HEADING.match(line) is not None)


def split_into_chapters(paragraphs):
    """Split a list of paragraphs into a list of (title, content) pairs.

    Each item in ``paragraphs`` is a pair of (text, is_heading_1).
    Any text before the first heading is kept as "Opening pages" so
    nothing is lost.
    """
    chapters = [("Opening pages", [])]
    for text, is_heading_1 in paragraphs:
        if (is_heading_1 and text.strip()) or is_chapter_heading(text):
            chapters.append((text.strip(), []))
        else:
            chapters[-1][1].append(text)

    chapters = [
        (title, "\n".join(lines).strip()) for title, lines in chapters
    ]

    if not chapters[0][1]:
        chapters.pop(0)

        # No headings at all: split long texts into parts instead.
    if len(chapters) == 1 and chapters[0][0] == "Opening pages":
        return split_into_parts(chapters[0][1])


def read_txt(data):
    """Return the paragraphs of a .txt file as (text, False) pairs."""
    for encoding in ("utf-8-sig", "cp1252"):
        try:
            text = data.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise ManuscriptFileError(
            "This text file could not be read. Please save it as UTF-8 "
            "and try again."
        )
    return [(line, False) for line in text.splitlines()]


def read_docx(data):
    """Return the paragraphs of a .docx file as (text, is_heading_1)."""
    try:
        document = Document(io.BytesIO(data))
    except (PackageNotFoundError, zipfile.BadZipFile, KeyError, ValueError):
        raise ManuscriptFileError(
            "This file could not be opened as a Word document. Please "
            "check it is a real .docx file."
        )
    return [
        (paragraph.text, paragraph.style.name == "Heading 1")
        for paragraph in document.paragraphs
    ]


def unlock_pdf(reader):
    """Try to open a locked PDF that has an empty password.

    Some PDFs are "encrypted" only to stop editing and open without a
    password. Returns False if a real password is needed.
    """
    try:
        return bool(reader.decrypt(""))
    except DependencyError:
        return False


def read_pdf_page(page):
    """Return the text of one PDF page, with its lines kept together.

    "Layout" mode rebuilds each line from where the words sit on the
    page. Without it, PDFs made by Google Docs and some other programs
    come out with every word on a separate line. If layout mode fails
    on an unusual PDF, fall back to the plain mode.
    """
    try:
        return page.extract_text(extraction_mode="layout") or ""
    except Exception:  # pypdf can raise many kinds of error here.
        return page.extract_text() or ""


def read_pdf(data):
    """Return the lines of a .pdf file's text as (text, False) pairs.

    Only PDFs that contain real text can be read. A scanned PDF is just
    pictures of pages, so it has no text to read.
    """
    try:
        reader = PdfReader(io.BytesIO(data))
        if reader.is_encrypted and not unlock_pdf(reader):
            raise ManuscriptFileError(
                "This PDF is password-protected. Please remove the "
                "password and try again."
            )
        pages = [read_pdf_page(page) for page in reader.pages]
    except (PdfReadError, ValueError, KeyError, TypeError):
        raise ManuscriptFileError(
            "This file could not be opened as a PDF. Please check it is "
            "a real .pdf file."
        )

    text = "\n".join(pages)
    if not text.strip():
        raise ManuscriptFileError(
            "No text could be found in this PDF. It may be a scanned "
            "image; please upload a .docx or .txt version instead."
        )
    # Layout mode pads lines with spaces to copy their position on the
    # page. Remove the padding and squash runs of spaces into one.
    return [(" ".join(line.split()), False) for line in text.splitlines()]


READERS = {".docx": read_docx, ".txt": read_txt, ".pdf": read_pdf}


def read_chapters(uploaded_file):
    """Read an uploaded file and return its chapters.

    ``uploaded_file`` is the file object Flask gives us from the form,
    which has already checked its type and size. Returns a list of
    (title, content) pairs, or raises ManuscriptFileError with a
    message for the user.
    """
    extension = os.path.splitext(uploaded_file.filename or "")[1].lower()
    read = READERS.get(extension)
    if read is None:
        raise ManuscriptFileError(
            "Only .docx, .txt and .pdf files can be uploaded."
        )

    data = uploaded_file.read()
    if not data:
        raise ManuscriptFileError("The file you chose is empty.")

    paragraphs = read(data)
    if not "".join(text for text, _ in paragraphs).strip():
        raise ManuscriptFileError("The file you chose has no text in it.")

    return split_into_chapters(paragraphs)
