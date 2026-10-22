"""Run the PressDesk Flask application."""

from app import create_app


app = create_app()


if __name__ == "__main__":
    # Port 5000 is used by AirPlay on macOS, so use 5001 instead.
    # Debug (and auto-reload) follows the DEBUG setting from env.py.
    app.run(port=5001, debug=app.config["DEBUG"])
