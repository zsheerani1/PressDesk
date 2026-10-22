# This script creates demo data (one publisher with a few manuscripts,
# chapters and notes) for testing PressDesk locally. It never deletes or
# changes existing data: anything that already exists is skipped, so it
# is safe to run more than once.

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
    "press_name": "Hollow Tree Press",
}

# Each chapter is (title, content, is_read, [notes]).
# Each note is (body, was_edited).
MANUSCRIPTS = [
    {
        "title": "The Lamplighter's Apprentice",
        "author_name": "Ines Calloway",
        "genre": "Historical fiction",
        "status": "reading",
        "chapters": [
            (
                "Chapter 1: Oil and Wick",
                "In the winter of 1851, Tobias Reed was eleven years old and "
                "could light forty-two street lamps between dusk and the "
                "first bell from St Anne's. Mr Halloran, who had lit them "
                "for thirty years, said he was too quick by half.",
                True,
                [
                    ("Strong opening line. The number of lamps gives us "
                     "Tobias's pride straight away.", False),
                    ("Check the date: were gas lamps lit by hand on this "
                     "street in 1851? Ask the author for a source.", True),
                ],
            ),
            (
                "Chapter 2: The Dark Street",
                "One lamp on Tanner's Row would not light. Tobias tried it "
                "three nights running, and on the fourth he climbed the "
                "post and found a folded letter where the wick should be.",
                True,
                [],
            ),
            (
                "Chapter 3: Halloran's Secret",
                "The letter was addressed to Mr Halloran, in a hand Tobias "
                "did not know, and it was dated twenty years before he was "
                "born.",
                False,
                [],
            ),
        ],
    },
    {
        "title": "Small Hours",
        "author_name": "Rowan Achebe",
        "genre": "Short stories",
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
                "Chapter 3: Hospital Car Park",
                "Ticket machines, Dev decided, were the loneliest objects "
                "in the world, and he had now spent four nights talking "
                "to one.",
                True,
                [],
            ),
        ],
    },
    {
        "title": "North of the Orchard",
        "author_name": "Marta Lindqvist",
        "genre": "Literary fiction",
        "status": "received",
        "chapters": [
            (
                "Chapter 1",
                "The orchard had been sold, but nobody had told the "
                "apple trees, and so in September they fruited as if "
                "nothing had changed.",
                False,
                [],
            ),
            (
                "Chapter 2",
                "Elin came back for the harvest because her brother asked "
                "her to, and because she had nowhere better to be.",
                False,
                [],
            ),
            (
                "Chapter 3",
                "The new owner arrived on the last day of picking, with a "
                "surveyor and a dog that ate every windfall it could find.",
                False,
                [],
            ),
        ],
    },
]


def get_or_create_publisher():
    """Return the demo publisher, creating the account if it is missing.

    Returns the user and True if it was created, False if it existed.
    An existing account is left exactly as it is, including its password.
    """
    user = User.query.filter_by(email=DEMO_PUBLISHER["email"]).first()
    if user:
        print(f"Skipped account {user.email}: it already exists.")
        return user, False

    user = User(
        name=DEMO_PUBLISHER["name"],
        email=DEMO_PUBLISHER["email"],
        press_name=DEMO_PUBLISHER["press_name"],
    )
    user.set_password(DEMO_PUBLISHER["password"])
    db.session.add(user)
    db.session.flush()
    print(f"Created publisher account {user.email}.")
    return user, True


def create_manuscript(owner, data, days_ago):
    """Create one demo manuscript with its chapters and notes."""
    uploaded_at = utc_now() - timedelta(days=days_ago)
    manuscript = Manuscript(
        title=data["title"],
        author_name=data["author_name"],
        genre=data["genre"],
        status=data["status"],
        owner_id=owner.id,
        uploaded_at=uploaded_at,
    )
    for number, chapter_data in enumerate(data["chapters"], start=1):
        title, content, is_read, notes = chapter_data
        chapter = Chapter(
            number=number, title=title, content=content, is_read=is_read
        )
        for position, (body, was_edited) in enumerate(notes):
            created_at = uploaded_at + timedelta(hours=number + position)
            note = Note(body=body, created_at=created_at)
            if was_edited:
                note.updated_at = created_at + timedelta(hours=2)
            chapter.notes.append(note)
        manuscript.chapters.append(chapter)
    db.session.add(manuscript)


def create_manuscripts(owner):
    """Create any demo manuscripts the publisher does not already have."""
    for days_ago, data in enumerate(MANUSCRIPTS, start=1):
        existing = Manuscript.query.filter_by(
            owner_id=owner.id, title=data["title"]
        ).first()
        if existing:
            print(f"Skipped manuscript '{data['title']}': it already "
                  "exists.")
            continue
        create_manuscript(owner, data, days_ago)
        print(f"Created manuscript '{data['title']}' "
              f"({data['status']}).")


def print_login(created):
    """Print the demo login details."""
    print("\nDemo data ready. Log in at http://127.0.0.1:5001 with:\n")
    print(f"  email:    {DEMO_PUBLISHER['email']}")
    if created:
        print(f"  password: {DEMO_PUBLISHER['password']}\n")
    else:
        print("  password: unchanged (account already existed; the seed "
              f"password is {DEMO_PUBLISHER['password']})\n")


def main():
    """Add any missing demo data without touching existing rows."""
    app = create_app()
    with app.app_context():
        owner, created = get_or_create_publisher()
        create_manuscripts(owner)
        db.session.commit()
    print_login(created)


if __name__ == "__main__":
    main()
