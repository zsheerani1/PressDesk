import os

   # Load secret values from env.py when running locally.
   # env.py is in .gitignore, so it's never uploaded.
try:
    import env
except ImportError:
    env = None

if env:
    os.environ.setdefault("SECRET_KEY", env.SECRET_KEY)
    os.environ.setdefault("DATABASE_URL", env.DATABASE_URL)
    os.environ.setdefault("DEBUG", env.DEBUG)


class Config:
    """Settings used by the Flask app."""

    SECRET_KEY = os.environ.get("SECRET_KEY")
    # Heroku gives a postgres:// address, which SQLAlchemy doesn't accept.
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "").replace(
        "postgres://", "postgresql://", 1
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Debug mode stays off unless DEBUG is set to True
    DEBUG = os.environ.get("DEBUG") == "True"

    # Block very large uploads; the form gives a friendly error over 5 MB.
    MAX_CONTENT_LENGTH = 20 * 1024 * 1024
