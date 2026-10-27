"""Business Logic: Payment Management (FR-09).

Controls: C-06 (no card data stored, gateway response verified, no duplicate
processing), SO-03 / T-07 (idempotency key), T-06 (amount from server only).
"""
import re
import secrets
from datetime import date

from app.data import payment_repo, session_repo
from app.data.db import transaction
from app.services import ConflictError, ServiceError, payment_gateway

USER_METHODS = ("card", "upi")
ADMIN_METHODS = ("card", "upi", "cash")
UPI_RE = re.compile(r"^[\w.\-]{2,64}@[A-Za-z]{2,32}$")


def _luhn_ok(number: str) -> bool:
    total = 0
    for i, ch in enumerate(reversed(number)):
        d = int(ch)
        if i % 2:
            d = d * 2 - 9 if d > 4 else d * 2
        total += d
    return total % 10 == 0


def validate_card(number: str, expiry: str, cvv: str, today: date) -> str:
    number = re.sub(r"\D", "", number or "")
    if not (13 <= len(number) <= 19) or not _luhn_ok(number):
        raise ServiceError("Enter a valid card number.")
    m = re.match(r"^(\d{2})\s*/\s*(\d{2})$", (expiry or "").strip())
    if not m or not (1 <= int(m.group(1)) <= 12):
        raise ServiceError("Enter the expiry as MM/YY.")
    month, year = int(m.group(1)), 2000 + int(m.group(2))
    if (year, month) < (today.year, today.month):
        raise ServiceError("This card has expired.")
    if not re.match(r"^\d{3,4}$", (cvv or "").strip()):
        raise ServiceError("Enter the 3-digit CVV.")
    return number


def payable_session(actor, session_id: int):
    s = session_repo.get(session_id)
    if s is None or (actor["role"] != "admin" and s["user_id"] != actor["id"]):
        raise ServiceError("Parking session not found.")
    if s["exit_time"] is None:
        raise ServiceError("Exit the vehicle first; the fee is calculated at exit.")
    if s["status"] == "paid":
        raise ConflictError("This parking session is already paid.")
    return s


def pay(actor, session_id: int, method: str, details: dict, key: str, gateway_secret: str, today: date):
    """Returns (payment_row, created). A replayed key returns the first result."""
    if key:
        existing = payment_repo.get_by_key(key)
        if existing is not None:
            return payment_repo.get_by_public_id(existing["public_id"]), False

    allowed = ADMIN_METHODS if actor["role"] == "admin" else USER_METHODS
    if method not in allowed:
        raise ServiceError("Choose a supported payment method.")
    s = payable_session(actor, session_id)
    amount = float(s["fee"])  # from the server-side calculation, never from the form

    reference = None
    if method == "card":
        number = validate_card(details.get("card_number"), details.get("expiry"), details.get("cvv"), today)
        reference = "card ****" + number[-4:]
        details = {"card_number": number}
    elif method == "upi":
        upi = (details.get("upi_id") or "").strip()
        if not UPI_RE.match(upi):
            raise ServiceError("Enter a valid UPI ID, for example name@okbank.")
        reference = "upi " + upi[:2] + "***@" + upi.split("@")[1]
        details = {"upi_id": upi}
    else:
        reference = "cash at desk"

    if method == "cash":
        status = "success"
    else:
        response = payment_gateway.charge(gateway_secret, amount, method, details)
        if not payment_gateway.verify(gateway_secret, response):
            raise ServiceError("Payment could not be verified. You have not been charged.")
        status = response["status"]

    public_id = "pay_" + secrets.token_urlsafe(9)
    with transaction(immediate=True) as conn:
        if status == "success" and payment_repo.mark_session_paid(conn, session_id) == 0:
            raise ConflictError("This parking session is already paid.")
        payment_repo.insert(conn, public_id, session_id, amount, method, reference, status, key or None)
    return payment_repo.get_by_public_id(public_id), True


def pending(actor):
    if actor["role"] == "admin":
        return session_repo.all_unpaid()
    return session_repo.unpaid_for_user(actor["id"])


def receipt(actor, public_id: str):
    p = payment_repo.get_by_public_id(public_id or "")
    if p is None or (actor["role"] != "admin" and p["user_id"] != actor["id"]):
        raise ServiceError("Payment not found.")
    return p
