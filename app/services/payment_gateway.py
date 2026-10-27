"""External system adapter: Payment Gateway (mock).

Stands in for a hosted gateway such as Razorpay/Stripe test mode. The gateway
signs its response; the app trusts a response only after verifying the
signature (TB-03). Test inputs that are declined:
  card number ending in 0002, or UPI ID starting with "fail".
"""
import hashlib
import hmac
import secrets


def _sign(secret: str, txn_id: str, amount: float, status: str) -> str:
    msg = f"{txn_id}|{amount:.2f}|{status}".encode()
    return hmac.new(secret.encode(), msg, hashlib.sha256).hexdigest()


def charge(secret: str, amount: float, method: str, details: dict) -> dict:
    declined = (
        (method == "card" and details.get("card_number", "").endswith("0002"))
        or (method == "upi" and details.get("upi_id", "").lower().startswith("fail"))
    )
    status = "failed" if declined else "success"
    txn_id = "txn_" + secrets.token_hex(8)
    return {"txn_id": txn_id, "amount": amount, "status": status,
            "signature": _sign(secret, txn_id, amount, status)}


def verify(secret: str, response: dict) -> bool:
    expected = _sign(secret, response["txn_id"], response["amount"], response["status"])
    return hmac.compare_digest(expected, response.get("signature", ""))
