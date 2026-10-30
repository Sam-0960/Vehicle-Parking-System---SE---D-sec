# Vehicle Parking System

SE Mini Project (UE23CS341A), PES University, D section.

Users register vehicles, check slot availability, reserve, park, exit and pay. Administrators manage slots and rates, record entries at the desk, search vehicles, and read the dashboard and reports.

## Features

| SRS | Feature | Where |
|---|---|---|
| FR-01 | Registration and login with lockout | `/register`, `/login` |
| FR-02 | Vehicle registration and management | `/vehicles/` |
| FR-03 | Slot management (admin) | `/admin/slots/` |
| FR-04 | Live slot availability | `/availability/` |
| FR-05, FR-06 | Vehicle entry and exit | `/parking/` |
| FR-07 | Slot reservations | `/reservations/` |
| FR-08 | Fee calculation, editable rates | `/rates`, `/admin/rates` |
| FR-09 | Card / UPI / cash payments, receipts | `/payments/` |
| FR-10 | Parking history | `/history/` |
| FR-11 | Notifications | `/notifications/` |
| FR-12 | Admin dashboard | `/admin/` |
| FR-13 | Vehicle search | `/admin/search/` |
| FR-14 | Reports with CSV export | `/admin/reports/` |

Full mapping from requirements to code and tests: [`docs/TRACEABILITY.md`](docs/TRACEABILITY.md).

## Architecture

Layered architecture, as justified in `Documents/Architecture Justification.pdf`. Each layer calls only the layer below it.

```
app/
├── presentation/      Presentation Layer: Flask blueprints (routes/), Jinja templates, CSS
├── services/          Business Logic Layer: one service per component in the component diagram
├── data/              Data Layer: schema.sql and repositories (parameterised SQL only)
├── security.py        Role checks, CSRF, rate limiting, audit logging
├── config.py          Settings; secrets come from environment variables
└── clock.py           Single source of "now" (keeps fee and expiry logic testable)
tests/                 pytest suite, one file per requirement
.github/workflows/     CI and pull-request checks
```

| Component (diagram) | Service |
|---|---|
| Authentication & User Management | `auth_service.py` |
| Vehicle Management | `vehicle_service.py` |
| Parking Slot Management | `slot_service.py` |
| Parking Availability Service | `availability_service.py` |
| Entry & Exit Management | `parking_service.py` |
| Parking Reservation Service | `reservation_service.py` |
| Fee Calculation / Billing Service | `fee_service.py` |
| Payment Management + Payment Gateway | `payment_service.py`, `payment_gateway.py` |
| Parking History Service | `history_service.py` |
| Notification Service | `notification_service.py` |
| Admin Dashboard & Reporting | `dashboard_service.py`, `search_service.py`, `report_service.py` |

## Run locally

Requires Python 3.11 or newer.

```bash
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt
flask --app run seed-demo            # optional: test-plan data (slots A01-A04, M01-M02, T01)
flask --app run run
```

Open http://127.0.0.1:5000. Demo logins (password `Park@123`): `ravi@test.com` and `admin@test.com`.

Other commands:

```bash
flask --app run create-admin         # create an administrator (there is no default admin)
flask --app run promote <email>      # make an existing account an administrator
flask --app run backup               # timestamped copy of the database in backups/
```

Environment variables: `VPS_SECRET_KEY`, `VPS_DATABASE`, `VPS_GATEWAY_SECRET`, `VPS_SECURE_COOKIES=1` (behind HTTPS).

## Payments (test mode)

| Input | Result |
|---|---|
| Card `4111 1111 1111 1111`, any future expiry, any CVV | Success |
| Card `4000 0000 0000 0002` | Declined |
| UPI `name@okbank` | Success |
| UPI starting with `fail` | Declined |

Card numbers and CVVs are never stored; only a masked reference is kept.

## Fees

Every started hour is charged at the hourly rate, each day is capped, and the first 10 minutes are free. Defaults: car ₹50/h (cap ₹400), bike ₹20/h (cap ₹150), truck ₹100/h (cap ₹800). Admins change them at `/admin/rates`.

## Tests

```bash
pytest -q
```

Each test file covers one requirement and names the Test Plan cases it checks (TC01–TC20, NFT01–NFT06, T-01–T-15). GitHub Actions runs the suite on every push and pull request, and the PR check requires each PR to link its backlog issue.

## Project documents

- `Documents/` — SRS, Security Log, use cases, architecture justification, component diagram, test plan
- `docs/SPRINTS.md` — sprint backlog with story points and owners
- `docs/TRACEABILITY.md` — requirement → issue → code → test
- `docs/DEVIATIONS.md` — differences from the submitted documents
- `docs/DEMO_SCRIPT.md` — script for the sprint demo videos
