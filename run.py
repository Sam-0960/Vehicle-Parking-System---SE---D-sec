"""Entry point.

Development:  flask --app run run            (debug stays off unless you pass --debug)
Production:   gunicorn "run:app"
"""
from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
