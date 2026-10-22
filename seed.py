"""Add a demo publisher and demo manuscripts to the local database.

Anything that already exists is skipped, so it is safe to run more than
once. Run with:  python seed.py
"""

from datetime import timedelta

from app import create_app, db
from app.models import Chapter, Manuscript, Note, User, utc_now


DEMO_PUBLISHER = {
    "name": "Alex Morgan",
    "email": "demo@pressdesk.example.com",
    "password": "DemoPress2026!",
    "press_name": "Chapter House Press",
}

# Each chapter is (title, content, is_read, [notes]).
# Each note is (body, was_edited).
MANUSCRIPTS = [
    {
        "title": "Pride & Prejudice",
        "author_name": "Jane Austen",
        "genre": "classical literature",
        "status": "reading",
        "chapters": [
            (
                "Chapter I",
                "It is a truth universally acknowledged, that a single man in possession of a good fortune, must be in want of a wife.",
                True,
                [
                    ("Brilliant first line: confident, funny and sets up "
                     "the whole plot in one sentence", False),
                    ("Is the narrator being ironic here, or is this"
                     "Mrs Bennet's view? Worth asking the author", True),
                ],
            ),
            (
                "Chapter II",
                "The astonishment of the ladies was just what he wished—that of Mrs. Bennet perhaps surpassing the rest;"
                "though when the first tumult of joy was over, "
                "she began to declare that it was what she had expected all the while. "
                True,
                [],
            ),
            (
                "Chapter III",
                "Not all that Mrs. Bennet, however, with the assistance "
                "of her five daughters, could ask on the subject, was "
                "sufficient to draw from her husband any satisfactory "
                "description of Mr. Bingley.",
                False,
                [],
            ),
        ],
    },
    {
        "title": "Great expectations",
        "author_name": "Charles Dickens",
        "genre": "Classic literature",
        "status": "shortlisted",
        "chapters": [
            (
                "Chapter 1: Night Bus",
                "The N29 driver had a rule: anyone still on board at the "
                "last stop got a cup of tea from his flask. Most nights "
                "nobody was. Tonight there were three of them.",
                True,
                [("Lovely, warm voice. This is the story to lead the "
                  "collection with.", False)],
            ),
            (
                "Chapter 2: The Baker's Alarm",
                "Mira's alarm went off at 3:40 every morning, and every "
                "morning for six years she had been awake a minute before "
                "it, waiting.",
                True,
                [("Ending feels rushed; would one more page help?",
                  False)],
            ),
            (
                "Chapter III",
                "Not all that Mrs. Bennet, however, with the assistance "
                "of her five daughters, could ask on the subject, was "
                "sufficient to draw from her husband any satisfactory "
                "description of Mr. Bingley.",
                False,
                [],
            ),
        ],
    },
    {
        "title": "Moby Dick",
        "author_name": "Herman Melville",
        "genre": "Adventure fiction",
        "status": "received",
        "chapters": [
            (
                "CHAPTER 1. Loomings.",
                "Call me Ishmael. "
                "Some years ago—never mind how long precisely—"
                "having little or no money in my purse",
                "and nothing particular to interest me on shore"
                "I thought I would sail about a little and see the watery part of the world. ",
                False,
                [],
            ),
            (
                "CHAPTER 2. The Carpet-Bag.",
                "I stuffed a shirt or two into my old carpet-bag,"
                "tucked it under my arm, and started for Cape Horn and the Pacific",
                False,
                [],
            ),
            (
                "CHAPTER 3. The Spouter-Inn.",
                "Entering that gable-ended Spouter-Inn"
                "you found yourself in a wide, low, straggling entry with old-fashioned wainscots"
                "reminding one of the bulwarks of some condemned old craft."
                False,
                [],
            ),
        ],
    },
]


def create_manuscript(owner, data, days_ago):
    """Make one demo manuscript, with its chapters and notes."""
    uploaded_at = utc_now() - timedelta(days=days_ago)
    manuscript = Manuscript(
        title=data["title"],
        author_name=data["author_name"],
        genre=data["genre"],
        status=data["status"],
        owner=owner,
        uploaded_at=uploaded_at,
    )

    for number, chapter_data in enumerate(data["chapters"], start=1):
        title, content, is_read, notes = chapter_data
        chapter = Chapter(
            number=number, title=title, content=content, is_read=is_read
        )

        for body, was_edited in notes:
            note = Note(body=body)
            # Mark some notes as edited so the demo shows both kinds.
            if was_edited:
                note.updated_at = utc_now()
            chapter.notes.append(note)

        manuscript.chapters.append(chapter)

    db.session.add(manuscript)