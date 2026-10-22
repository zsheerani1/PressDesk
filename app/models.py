"""Database models for PressDesk."""

from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app import db

# The only statuses a manuscript may have, in workflow order.
MANUSCRIPT_STATUSES = [
    "received",
    "reading",
    "shortlisted",
    "accepted",
    "declined",
]


def utc_now():
    """Return the current date and time in UTC."""
    return datetime.now(timezone.utc)


class User(UserMixin, db.Model):
    """A publisher account. Each publisher owns their own manuscripts."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    press_name = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    manuscripts = db.relationship(
        "Manuscript",
        backref="owner",
        cascade="all, delete-orphan",
        lazy=True,
    )

    def set_password(self, password):
        """Hash a plain-text password before storing it."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check a candidate password against the stored hash."""
        return check_password_hash(self.password_hash, password)


class Manuscript(db.Model):
    """A manuscript uploaded by a publisher, split into chapters."""

    __tablename__ = "manuscripts"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author_name = db.Column(db.String(120), nullable=False)
    genre = db.Column(db.String(80), nullable=False)
    status = db.Column(db.String(40), default="received", nullable=False)
    uploaded_at = db.Column(db.DateTime, default=utc_now, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=utc_now, onupdate=utc_now, nullable=False
    )
    owner_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False
    )

    # Deleting a manuscript also deletes its chapters (and their notes).
    chapters = db.relationship(
        "Chapter",
        backref="manuscript",
        cascade="all, delete-orphan",
        order_by="Chapter.number",
        lazy=True,
    )

    @property
    def chapter_count(self):
        """Return how many chapters this manuscript has."""
        return len(self.chapters)

    @property
    def read_count(self):
        """Return how many chapters have been marked as read."""
        return sum(1 for chapter in self.chapters if chapter.is_read)

    @property
    def note_count(self):
        """Return the total number of notes across all chapters."""
        return sum(len(chapter.notes) for chapter in self.chapters)


class Chapter(db.Model):
    """One chapter of a manuscript."""

    __tablename__ = "chapters"

    id = db.Column(db.Integer, primary_key=True)
    manuscript_id = db.Column(
        db.Integer, db.ForeignKey("manuscripts.id"), nullable=False
    )
    number = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False, default="")
    is_read = db.Column(db.Boolean, default=False, nullable=False)

    # Deleting a chapter also deletes its notes. Newest notes come first.
    notes = db.relationship(
        "Note",
        backref="chapter",
        cascade="all, delete-orphan",
        order_by="Note.created_at.desc()",
        lazy=True,
    )


class Note(db.Model):
    """A publisher's note about one chapter."""

    __tablename__ = "notes"

    id = db.Column(db.Integer, primary_key=True)
    chapter_id = db.Column(
        db.Integer, db.ForeignKey("chapters.id"), nullable=False
    )
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)
    # Stays empty until the note is edited, so we can show "edited".
    updated_at = db.Column(db.DateTime, nullable=True)

    @property
    def is_edited(self):
        """Return True if the note has been changed since it was added."""
        return self.updated_at is not None
