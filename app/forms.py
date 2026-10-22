"""WTForms for PressDesk."""

from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField, FileRequired, FileSize
from wtforms import (
    PasswordField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import DataRequired, Email, Length

from app.chapters import MAX_FILE_SIZE, TOO_LARGE_MESSAGE
from app.models import MANUSCRIPT_STATUSES


def strip_whitespace(value):
    """Remove spaces from the start and end of text typed into a form."""
    return value.strip() if isinstance(value, str) else value


def text_field(label, *validators):
    """A required text box that ignores spaces around what is typed."""
    return StringField(
        label,
        filters=[strip_whitespace],
        validators=[DataRequired(), *validators],
    )


class RegisterForm(FlaskForm):
    """Registration form for a publisher."""

    name = text_field("Your name", Length(min=2, max=120))
    email = text_field("Email", Email(), Length(max=255))
    password = PasswordField(
        "Password", validators=[DataRequired(), Length(min=8, max=128)]
    )
    press_name = text_field("Press name", Length(max=120))
    submit = SubmitField("Create account")


class LoginForm(FlaskForm):
    """Login form for a publisher."""

    email = text_field("Email", Email(), Length(max=255))
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Log in")


class ManuscriptDetailsForm(FlaskForm):
    """The title, author and genre of a manuscript."""

    title = text_field("Title", Length(max=200))
    author_name = text_field("Author name", Length(max=120))
    genre = text_field("Genre", Length(max=80))
    submit = SubmitField("Save changes")


class UploadForm(ManuscriptDetailsForm):
    """Manuscript details plus the file to upload."""

    manuscript_file = FileField(
        "Manuscript file (.docx, .txt or .pdf, up to 5 MB)",
        validators=[
            FileRequired("Please choose a file to upload."),
            FileAllowed(
                ["docx", "txt", "pdf"],
                "Only .docx, .txt and .pdf files can be uploaded.",
            ),
            FileSize(max_size=MAX_FILE_SIZE, message=TOO_LARGE_MESSAGE),
        ],
    )
    submit = SubmitField("Upload manuscript")


class StatusForm(FlaskForm):
    """Form for changing a manuscript's status."""

    status = SelectField(
        "Status",
        choices=[(s, s.capitalize()) for s in MANUSCRIPT_STATUSES],
        validators=[DataRequired()],
    )
    submit = SubmitField("Change status")


class NoteForm(FlaskForm):
    """Form for adding or editing a note on a chapter."""

    body = TextAreaField(
        "Note",
        filters=[strip_whitespace],
        validators=[
            DataRequired("Please write something in your note."),
            Length(max=2000, message="Notes can be up to 2000 characters."),
        ],
    )
    submit = SubmitField("Save note")
