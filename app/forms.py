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

from app.chapters import MAX_FILE_SIZE
from app.models import MANUSCRIPT_STATUSES


def strip_whitespace(value):
    """Remove spaces from the start and end of text typed into a form."""
    return value.strip() if isinstance(value, str) else value


class RegisterForm(FlaskForm):
    """Registration form for a publisher."""

    name = StringField(
        "Your name",
        filters=[strip_whitespace],
        validators=[DataRequired(), Length(min=2, max=120)],
    )
    email = StringField(
        "Email",
        filters=[strip_whitespace],
        validators=[DataRequired(), Email(), Length(max=255)],
    )
    password = PasswordField(
        "Password", validators=[DataRequired(), Length(min=8, max=128)]
    )
    press_name = StringField(
        "Press name",
        filters=[strip_whitespace],
        validators=[DataRequired(), Length(max=120)],
    )
    submit = SubmitField("Create account")


class LoginForm(FlaskForm):
    """Login form for a publisher."""

    email = StringField(
        "Email",
        filters=[strip_whitespace],
        validators=[DataRequired(), Email(), Length(max=255)],
    )
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Log in")


class ManuscriptDetailsForm(FlaskForm):
    """The title, author and genre of a manuscript."""

    title = StringField(
        "Title",
        filters=[strip_whitespace],
        validators=[DataRequired(), Length(max=200)],
    )
    author_name = StringField(
        "Author name",
        filters=[strip_whitespace],
        validators=[DataRequired(), Length(max=120)],
    )
    genre = StringField(
        "Genre",
        filters=[strip_whitespace],
        validators=[DataRequired(), Length(max=80)],
    )
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
            FileSize(
                max_size=MAX_FILE_SIZE,
                message="The file is too large. The maximum size is 5 MB.",
            ),
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
            Length(
                min=1,
                max=2000,
                message="Notes must be between 1 and 2000 characters.",
            ),
        ],
    )
    submit = SubmitField("Save note")
