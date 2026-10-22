import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Load secret values from env.py when running locally

if os.path.exists(os.path.join(BASE_DIR, "env.py")):
    import env

    os.environ.setdefault("SECRET_KEY", getattr(env, "SECRET_KEY", ""))
    os.environ.setdefault("DATABASE_URL", getattr(env, "DATABASE_URL", ""))
    os.environ.setdefault("DEBUG", getattr(env, "DEBUG", "False"))


def get_database_url():
    """Fix Heroku's postgres:// prefix, which SQLAlchemy doesn't accept."""
    url = os.environ.get("DATABASE_URL", "")
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url


class Config:
    """Settings used by the Flask app."""

    SECRET_KEY = os.environ.get("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = get_database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Debug mode stays off unless DEBUG is set to true
    DEBUG = os.environ.get("DEBUG", "False") == "True"

    #Block very large uploads; the form gives a friendly error over 5 MB.
    MAX_CONTENT_LENGTH = 20 * 1024 * 1024
