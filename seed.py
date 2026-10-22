"""Add a demo publisher and demo manuscripts to the local database.
Run with:  python seed.py
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
        "title": "Pride and Prejudice",
        "author_name": "Jane Austen",
        "genre": "Classic fiction",
        "status": "reading",
        "chapters": [
            (
                "Chapter I",
                "It is a truth universally acknowledged, that a single "
                "man in possession of a good fortune, must be in want "
                "of a wife.",
                True,
                [
                    ("Brilliant first line: confident, funny and sets up "
                     "the whole plot in one sentence.", False),
                    ("Is the narrator being ironic here, or is this "
                     "Mrs Bennet's view? Worth asking the author.", True),
                ],
            ),
            (
                "Chapter II",
                "The astonishment of the ladies was just what he "
                "wished—that of Mrs. Bennet perhaps surpassing the rest; "
                "though when the first tumult of joy was over, she began "
                "to declare that it was what she had expected all the "
                "while.",
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
        "title": "Great Expectations",
        "author_name": "Charles Dickens",
        "genre": "Classic fiction",
        "status": "shortlisted",
        "chapters": [
            (
                "Chapter I",
                "My father's family name being Pirrip, and my Christian "
                "name Philip, my infant tongue could make of both names "
                "nothing longer or more explicit than Pip.",
                True,
                [("Wonderful narrative voice. We know who Pip is "
                  "straight away.", False)],
            ),
            (
                "Chapter II",
                "My sister, Mrs. Joe Gargery, was more than twenty years "
                "older than I, and had established a great reputation "
                "with herself and the neighbours because she had brought "
                "me up \"by hand.\"",
                True,
                [("Mrs Joe is very harsh. Will readers stay with this "
                  "household?", False)],
            ),
            (
                "Chapter III",
                "It was a rimy morning, and very damp.",
                True,
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
                "Call me Ishmael. Some years ago—never mind how long "
                "precisely—having little or no money in my purse, and "
                "nothing particular to interest me on shore, I thought I "
                "would sail about a little and see the watery part of "
                "the world.",
                False,
                [],
            ),
            (
                "CHAPTER 2. The Carpet-Bag.",
                "I stuffed a shirt or two into my old carpet-bag, tucked "
                "it under my arm, and started for Cape Horn and the "
                "Pacific.",
                False,
                [],
            ),
            (
                "CHAPTER 3. The Spouter-Inn.",
                "Entering that gable-ended Spouter-Inn, you found "
                "yourself in a wide, low, straggling entry with "
                "old-fashioned wainscots, reminding one of the bulwarks "
                "of some condemned old craft.",
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


def main():
    """Add any missing demo data without changing what's already there."""
    with create_app().app_context():
        # Create the demo account if it doesn't exist yet.
        owner = User.query.filter_by(email=DEMO_PUBLISHER["email"]).first()
        if owner:
            print(f"Skipped account {owner.email}: it already exists.")
        else:
            owner = User(
                name=DEMO_PUBLISHER["name"],
                email=DEMO_PUBLISHER["email"],
                press_name=DEMO_PUBLISHER["press_name"],
            )
            owner.set_password(DEMO_PUBLISHER["password"])
            db.session.add(owner)
            print(f"Created publisher account {owner.email}.")

        # Add any demo manuscripts that are missing.
        for days_ago, data in enumerate(MANUSCRIPTS, start=1):
            if any(m.title == data["title"] for m in owner.manuscripts):
                print(f"Skipped manuscript '{data['title']}': it already "
                      "exists.")
            else:
                create_manuscript(owner, data, days_ago)
                print(f"Created manuscript '{data['title']}'.")
        db.session.commit()

    print("\nDemo data ready. Log in with:")
    print(f"  email:    {DEMO_PUBLISHER['email']}")
    print(f"  password: {DEMO_PUBLISHER['password']}")


if __name__ == "__main__":
    main()
