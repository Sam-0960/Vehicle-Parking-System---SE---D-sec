# Vehicle Parking System

SE Mini Project (UE23CS341A), PES University.

A web application for users to register vehicles, check slot availability, park, exit and pay, and for administrators to manage slots, rates, reservations and reports.

## Architecture

Layered architecture, as justified in `Documents/Architecture Justification.pdf`:

| Layer | Folder | Contents |
|---|---|---|
| Presentation | `app/presentation/` | Flask blueprints, Jinja templates, CSS |
| Business Logic | `app/services/` | One service per component in the component diagram |
| Data | `app/data/` | SQLite schema and repositories (parameterised queries only) |

## Run locally

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
flask --app run init-db
flask --app run run
```

Open http://127.0.0.1:5000

## Tests

```bash
pytest -q
```

CI runs the same suite on every push and pull request (`.github/workflows/ci.yml`).
