"""Read an uploaded manuscript file and split it into chapters.

The file is read in memory only; nothing is saved to disk.

A new chapter starts at:
- any line that starts with "Chapter" followed by a number, for example
  "Chapter 1", "Chapter One", "CHAPTER 3: The Ferry" or "Chapter XII";
- in .docx files, any paragraph styled as "Heading 1".

PDF files have no heading styles, so they are split on "Chapter" lines
only, like .txt files.

If no chapter headings are found, the whole text becomes one chapter
called "Full manuscript".
"""

import io
import re
import zipfile

from docx import Document
from docx.opc.exceptions import PackageNotFoundError
from pypdf import PdfReader
from pypdf.errors import DependencyError, PdfReadError


MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB

# Matches "Chapter" + the next word, ignoring upper/lower case.
CHAPTER_LINE = re.compile(r"^chapter\s+([a-z0-9]+)", re.IGNORECASE)

# Lines longer than this are treated as normal text, not headings.
MAX_HEADING_LENGTH = 100

NUMBER_WORDS = {
    "one", "two", "three", "four", "five", "six", "seven", "eight",
    "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen",
    "sixteen", "seventeen", "eighteen", "nineteen", "twenty", "thirty",
    "forty", "fifty", "sixty", "seventy", "eighty", "ninety", "hundred",
}

ROMAN_NUMERAL = re.compile(r"^[ivxlc]+$", re.IGNORECASE)


class ManuscriptFileError(Exception):
    """Raised when an uploaded file cannot be turned into chapters.

    The message is written so it can be shown straight to the user.
    """


def is_chapter_heading(line):
    """Return True if a line of text looks like a chapter heading.

    The word after "Chapter" must be a number (1, 12), a number word
    (One, Twenty) or a Roman numeral (IV). This stops sentences like
    "Chapter and verse, she said" from being treated as headings.
    """
    line = line.strip()
    if not line or len(line) > MAX_HEADING_LENGTH:
        return False

    match = CHAPTER_LINE.match(line)
    if match is None:
        return False

    word = match.group(1).lower()
    return (
        word.isdigit()
        or word in NUMBER_WORDS
        or ROMAN_NUMERAL.match(word) is not None
    )


def split_into_chapters(paragraphs):
    """Split a list of paragraphs into a list of (title, content) pairs.

    Each item in ``paragraphs`` is a pair of (text, is_heading_1).
    Any text before the first heading is kept as "Opening pages" so
    nothing is lost.
    """
    chapters = []
    current_title = None
    current_lines = []

    for text, is_heading_1 in paragraphs:
        is_styled_heading = is_heading_1 and bool(text.strip())
        is_heading = is_styled_heading or is_chapter_heading(text)
        if is_heading:
            # Save the chapter we were building before starting a new one.
            if current_title is not None or "".join(current_lines).strip():
                chapters.append(
                    (current_title or "Opening pages", current_lines)
                )
            current_title = text.strip()
            current_lines = []
        else:
            current_lines.append(text)

    if current_title is not None or "".join(current_lines).strip():
        chapters.append((current_title or "Opening pages", current_lines))

    # Turn each chapter's lines into a single block of text.
    chapters = [
        (title, "\n".join(lines).strip()) for title, lines in chapters
    ]

    # No headings at all: keep everything as one chapter.
    if len(chapters) == 1 and chapters[0][0] == "Opening pages":
        return [("Full manuscript", chapters[0][1])]
    return chapters


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


def read_chapters(uploaded_file):
    """Read an uploaded file and return its chapters.

    ``uploaded_file`` is the file object Flask gives us from the form.
    Returns a list of (title, content) pairs, or raises
    ManuscriptFileError with a message for the user.
    """
    filename = (uploaded_file.filename or "").lower()
    data = uploaded_file.read()

    if len(data) == 0:
        raise ManuscriptFileError("The file you chose is empty.")
    if len(data) > MAX_FILE_SIZE:
        raise ManuscriptFileError(
            "The file is too large. The maximum size is 5 MB."
        )

    if filename.endswith(".docx"):
        paragraphs = read_docx(data)
    elif filename.endswith(".txt"):
        paragraphs = read_txt(data)
    elif filename.endswith(".pdf"):
        paragraphs = read_pdf(data)
    else:
        raise ManuscriptFileError(
            "Only .docx, .txt and .pdf files can be uploaded."
        )

    if not "".join(text for text, _ in paragraphs).strip():
        raise ManuscriptFileError("The file you chose has no text in it.")

    return split_into_chapters(paragraphs)
