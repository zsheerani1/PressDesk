"""Minimal Flask application for PressDesk."""

from urllib.parse import urlparse

from flask import (
    Flask,
    abort,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFError, CSRFProtect
from sqlalchemy import func, or_

from config import Config


db = SQLAlchemy()
migrate = Migrate()
csrf = CSRFProtect()
login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.login_message = "Please log in to see that page."
login_manager.login_message_category = "error"


def create_app():
    """Create the app and register all routes in one place."""
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    login_manager.init_app(app)

    from app.chapters import ManuscriptFileError, read_chapters
    from app.forms import (
        LoginForm,
        ManuscriptDetailsForm,
        NoteForm,
        RegisterForm,
        StatusForm,
        UploadForm,
    )
    from app.models import (
        MANUSCRIPT_STATUSES,
        Chapter,
        Manuscript,
        Note,
        User,
        utc_now,
    )

    # ------------------------------------------------------------------
    # Helpers that make sure publishers only ever reach their own data.
    # Each one returns 404 if the item doesn't exist OR belongs to
    # somebody else, so nobody can tell other publishers' items exist.
    # ------------------------------------------------------------------

    def get_own_manuscript_or_404(manuscript_id):
        """Return the current publisher's manuscript, or abort with 404."""
        manuscript = db.session.get(Manuscript, manuscript_id)
        if manuscript is None or manuscript.owner_id != current_user.id:
            abort(404)
        return manuscript

    def get_own_chapter_or_404(chapter_id):
        """Return a chapter from the publisher's own manuscript, or 404."""
        chapter = db.session.get(Chapter, chapter_id)
        if (chapter is None
                or chapter.manuscript.owner_id != current_user.id):
            abort(404)
        return chapter

    def get_own_note_or_404(note_id):
        """Return a note on the publisher's own manuscript, or 404."""
        note = db.session.get(Note, note_id)
        if (note is None
                or note.chapter.manuscript.owner_id != current_user.id):
            abort(404)
        return note

    def chapter_url(chapter):
        """Return the web address of a chapter's page."""
        return url_for(
            "view_chapter",
            manuscript_id=chapter.manuscript_id,
            chapter_id=chapter.id,
        )

    def wants_json():
        """Return True if the request came from our upload JavaScript."""
        return request.headers.get("X-Requested-With") == "XMLHttpRequest"

    app.jinja_env.globals["chapter_url"] = chapter_url

    # ------------------------------------------------------------------
    # Public pages and accounts
    # ------------------------------------------------------------------

    @app.route("/")
    def index():
        """Render the landing page, or the dashboard if logged in."""
        if current_user.is_authenticated:
            return redirect(url_for("dashboard"))
        return render_template("index.html")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        """Log a publisher in."""
        if current_user.is_authenticated:
            return redirect(url_for("dashboard"))

        form = LoginForm()

        if form.validate_on_submit():
            email = form.email.data.lower()
            user = User.query.filter_by(email=email).first()
            if user and user.check_password(form.password.data):
                login_user(user, remember=True)
                flash(f"Welcome back, {user.name}.", "success")
                next_page = request.args.get("next")
                if next_page and is_safe_url(next_page):
                    return redirect(next_page)
                return redirect(url_for("dashboard"))

            flash("Invalid email or password.", "error")

        return render_template("auth/login.html", form=form)

    @app.route("/register", methods=["GET", "POST"])
    def register():
        """Register a new publisher account."""
        if current_user.is_authenticated:
            return redirect(url_for("dashboard"))

        form = RegisterForm()

        if form.validate_on_submit():
            email = form.email.data.lower()
            if User.query.filter_by(email=email).first():
                flash("An account with that email already exists.", "error")
                return render_template("auth/register.html", form=form)

            new_user = User(
                name=form.name.data,
                email=email,
                press_name=form.press_name.data,
            )
            new_user.set_password(form.password.data)
            db.session.add(new_user)
            db.session.commit()

            flash("Your account has been created. Please log in.", "success")
            return redirect(url_for("login"))

        return render_template("auth/register.html", form=form)

    @app.route("/logout", methods=["POST"])
    @login_required
    def logout():
        """Log the current publisher out."""
        logout_user()
        flash("You have been logged out.", "success")
        return redirect(url_for("index"))

    # ------------------------------------------------------------------
    # Dashboard and upload
    # ------------------------------------------------------------------

    def render_dashboard(upload_form, status_code=200):
        """Build the dashboard page for the current publisher.

        Shows a count for each status, and the list of manuscripts,
        filtered by status and searched by title or author if asked.
        """
        own_manuscripts = Manuscript.query.filter_by(
            owner_id=current_user.id
        )

        # Count how many manuscripts have each status.
        counts = {status: 0 for status in MANUSCRIPT_STATUSES}
        rows = (
            db.session.query(Manuscript.status, func.count(Manuscript.id))
            .filter_by(owner_id=current_user.id)
            .group_by(Manuscript.status)
            .all()
        )
        for status, count in rows:
            counts[status] = count
        total = sum(counts.values())

        # Apply the filter and search from the address bar, if any.
        status_filter = request.args.get("status", "")
        search = request.args.get("q", "").strip()
        query = own_manuscripts
        if status_filter in MANUSCRIPT_STATUSES:
            query = query.filter_by(status=status_filter)
        else:
            status_filter = ""
        if search:
            pattern = f"%{search}%"
            query = query.filter(or_(
                Manuscript.title.ilike(pattern),
                Manuscript.author_name.ilike(pattern),
            ))
        manuscripts = query.order_by(Manuscript.uploaded_at.desc()).all()

        return render_template(
            "dashboard.html",
            upload_form=upload_form,
            counts=counts,
            total=total,
            manuscripts=manuscripts,
            statuses=MANUSCRIPT_STATUSES,
            status_filter=status_filter,
            search=search,
        ), status_code

    @app.route("/dashboard")
    @login_required
    def dashboard():
        """Show the publisher's dashboard."""
        return render_dashboard(UploadForm())

    @app.route("/manuscripts/upload", methods=["POST"])
    @login_required
    def upload_manuscript():
        """Upload a .docx, .txt or .pdf file and split it into chapters.

        Works both as a normal form post and from the upload JavaScript,
        which shows a progress bar and expects a JSON reply.
        """
        form = UploadForm()
        errors = []
        chapters = []

        if form.validate_on_submit():
            try:
                chapters = read_chapters(form.manuscript_file.data)
            except ManuscriptFileError as error:
                errors.append(str(error))
        else:
            for field_errors in form.errors.values():
                errors.extend(field_errors)

        if errors:
            if wants_json():
                return jsonify(ok=False, errors=errors), 400
            for message in errors:
                flash(message, "error")
            return render_dashboard(form, status_code=400)

        manuscript = Manuscript(
            title=form.title.data,
            author_name=form.author_name.data,
            genre=form.genre.data,
            status="received",
            owner_id=current_user.id,
        )
        for number, (title, content) in enumerate(chapters, start=1):
            manuscript.chapters.append(
                Chapter(number=number, title=title, content=content)
            )
        db.session.add(manuscript)
        db.session.commit()

        word = "chapter" if len(chapters) == 1 else "chapters"
        flash(
            f"Uploaded '{manuscript.title}' — {len(chapters)} {word} found.",
            "success",
        )
        if wants_json():
            return jsonify(ok=True, redirect=url_for("dashboard"))
        return redirect(url_for("dashboard"))

    # ------------------------------------------------------------------
    # Manuscript page
    # ------------------------------------------------------------------

    def render_chapter_page(manuscript, chapter, note_form=None,
                            status_code=200):
        """Build the manuscript page with one chapter open.

        Opening a manuscript that is still "received" moves it to
        "reading" automatically.
        """
        if manuscript.status == "received":
            manuscript.status = "reading"
            db.session.commit()
            flash(
                f"'{manuscript.title}' is now marked as Reading.",
                "success",
            )

        # Work out the chapters either side of this one, for the
        # Previous / Next buttons.
        position = previous_chapter = next_chapter = None
        if chapter is not None:
            chapters = manuscript.chapters
            index = chapters.index(chapter)
            position = index + 1
            if index > 0:
                previous_chapter = chapters[index - 1]
            if index < len(chapters) - 1:
                next_chapter = chapters[index + 1]

        return render_template(
            "manuscript.html",
            manuscript=manuscript,
            chapter=chapter,
            position=position,
            previous_chapter=previous_chapter,
            next_chapter=next_chapter,
            status_form=StatusForm(status=manuscript.status),
            note_form=note_form or NoteForm(),
        ), status_code

    @app.route("/manuscripts/<int:manuscript_id>")
    @login_required
    def view_manuscript(manuscript_id):
        """Show a manuscript with its first chapter open."""
        manuscript = get_own_manuscript_or_404(manuscript_id)
        first_chapter = manuscript.chapters[0] if manuscript.chapters else None
        return render_chapter_page(manuscript, first_chapter)

    @app.route("/manuscripts/<int:manuscript_id>/chapters/<int:chapter_id>")
    @login_required
    def view_chapter(manuscript_id, chapter_id):
        """Show a manuscript with the chosen chapter open."""
        manuscript = get_own_manuscript_or_404(manuscript_id)
        chapter = get_own_chapter_or_404(chapter_id)
        if chapter.manuscript_id != manuscript.id:
            abort(404)
        return render_chapter_page(manuscript, chapter)

    @app.route("/manuscripts/<int:manuscript_id>/status", methods=["POST"])
    @login_required
    def change_status(manuscript_id):
        """Change a manuscript's status."""
        manuscript = get_own_manuscript_or_404(manuscript_id)
        form = StatusForm()
        if form.validate_on_submit():
            manuscript.status = form.status.data
            db.session.commit()
            flash(
                f"'{manuscript.title}' is now marked as "
                f"{manuscript.status.capitalize()}.",
                "success",
            )
        else:
            flash("Please choose a valid status.", "error")
        # Go back to the chapter the publisher was reading, if we know it.
        back = request.form.get("back", "")
        if not is_safe_url(back):
            back = url_for("view_manuscript", manuscript_id=manuscript.id)
        return redirect(back)

    @app.route(
        "/manuscripts/<int:manuscript_id>/edit", methods=["GET", "POST"]
    )
    @login_required
    def edit_manuscript(manuscript_id):
        """Edit a manuscript's title, author and genre."""
        manuscript = get_own_manuscript_or_404(manuscript_id)
        form = ManuscriptDetailsForm(obj=manuscript)

        if form.validate_on_submit():
            manuscript.title = form.title.data
            manuscript.author_name = form.author_name.data
            manuscript.genre = form.genre.data
            db.session.commit()
            flash(f"'{manuscript.title}' was updated.", "success")
            return redirect(
                url_for("view_manuscript", manuscript_id=manuscript.id)
            )

        return render_template(
            "manuscript_edit.html", form=form, manuscript=manuscript
        )

    @app.route(
        "/manuscripts/<int:manuscript_id>/delete", methods=["GET", "POST"]
    )
    @login_required
    def delete_manuscript(manuscript_id):
        """Ask for confirmation, then delete a manuscript.

        Its chapters and notes are deleted with it.
        """
        manuscript = get_own_manuscript_or_404(manuscript_id)

        if request.method == "POST":
            title = manuscript.title
            db.session.delete(manuscript)
            db.session.commit()
            flash(f"'{title}' and all its chapters and notes were deleted.",
                  "success")
            return redirect(url_for("dashboard"))

        return render_template(
            "confirm_delete.html",
            heading="Delete this manuscript?",
            message=(
                f"'{manuscript.title}' by {manuscript.author_name}, with "
                f"its {manuscript.chapter_count} chapters and "
                f"{manuscript.note_count} notes, will be permanently "
                "deleted."
            ),
            action_url=url_for(
                "delete_manuscript", manuscript_id=manuscript.id
            ),
            cancel_url=url_for(
                "view_manuscript", manuscript_id=manuscript.id
            ),
        )

    # ------------------------------------------------------------------
    # Chapters and notes
    # ------------------------------------------------------------------

    @app.route("/chapters/<int:chapter_id>/read", methods=["POST"])
    @login_required
    def mark_chapter(chapter_id):
        """Mark a chapter as read or unread."""
        chapter = get_own_chapter_or_404(chapter_id)
        chapter.is_read = request.form.get("read") == "yes"
        db.session.commit()
        state = "read" if chapter.is_read else "unread"
        flash(f"'{chapter.title}' marked as {state}.", "success")
        return redirect(chapter_url(chapter))

    @app.route("/chapters/<int:chapter_id>/notes", methods=["POST"])
    @login_required
    def add_note(chapter_id):
        """Add a note to a chapter."""
        chapter = get_own_chapter_or_404(chapter_id)
        form = NoteForm()

        if form.validate_on_submit():
            chapter.notes.append(Note(body=form.body.data))
            db.session.commit()
            flash(f"Note added to '{chapter.title}'.", "success")
            return redirect(chapter_url(chapter))

        for message in form.body.errors:
            flash(message, "error")
        return render_chapter_page(
            chapter.manuscript, chapter, note_form=form, status_code=400
        )

    @app.route("/notes/<int:note_id>/edit", methods=["GET", "POST"])
    @login_required
    def edit_note(note_id):
        """Edit a note."""
        note = get_own_note_or_404(note_id)
        form = NoteForm(obj=note)

        if form.validate_on_submit():
            note.body = form.body.data
            note.updated_at = utc_now()
            db.session.commit()
            flash("Your note was updated.", "success")
            return redirect(chapter_url(note.chapter))

        for message in form.body.errors:
            flash(message, "error")
        return render_template("note_edit.html", form=form, note=note)

    @app.route("/notes/<int:note_id>/delete", methods=["GET", "POST"])
    @login_required
    def delete_note(note_id):
        """Ask for confirmation, then delete a note."""
        note = get_own_note_or_404(note_id)
        chapter = note.chapter

        if request.method == "POST":
            db.session.delete(note)
            db.session.commit()
            flash("Your note was deleted.", "success")
            return redirect(chapter_url(chapter))

        preview = note.body if len(note.body) <= 120 else (
            note.body[:120] + "…"
        )
        return render_template(
            "confirm_delete.html",
            heading="Delete this note?",
            message=f"Your note on '{chapter.title}': \"{preview}\"",
            action_url=url_for("delete_note", note_id=note.id),
            cancel_url=chapter_url(chapter),
        )

    # ------------------------------------------------------------------
    # Accounts and errors
    # ------------------------------------------------------------------

    @login_manager.user_loader
    def load_user(user_id):
        """Load a user from the database for the session."""
        return db.session.get(User, int(user_id))

    @app.errorhandler(CSRFError)
    def csrf_error(error):
        """Explain an expired or missing form token instead of crashing."""
        flash("Your session has expired. Please try that again.", "error")
        return redirect(url_for("dashboard"))

    @app.errorhandler(413)
    def file_too_large(error):
        """Handle uploads far bigger than the size limit."""
        message = "The file is too large. The maximum size is 5 MB."
        if wants_json():
            return jsonify(ok=False, errors=[message]), 413
        flash(message, "error")
        return redirect(url_for("dashboard"))

    @app.errorhandler(404)
    def page_not_found(error):
        """Show the custom 404 page with a 404 status code."""
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def internal_error(error):
        """Show the custom 500 page with a 500 status code."""
        db.session.rollback()
        return render_template("errors/500.html"), 500

    return app


def is_safe_url(target):
    """Allow only relative next URLs on this site."""
    if not target or "\\" in target or not target.startswith("/"):
        return False
    parsed = urlparse(target)
    return parsed.scheme == "" and parsed.netloc == ""
