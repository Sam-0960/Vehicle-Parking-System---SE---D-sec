"""Business Logic: Notification Service (FR-11).

Notifies users about reservation confirmation, parking expiry and payment
status. Messages never contain card details (R-04).
"""
from datetime import timedelta

from app import clock
from app.data import notification_repo

EXPIRY_WARNING_MINUTES = 15


def reservation_confirmed(reservation) -> None:
    notification_repo.add(
        reservation["user_id"], "reservation",
        f"Reservation confirmed: slot {reservation['slot_code']} for {reservation['vehicle_number']}, "
        f"{reservation['start_time'][5:16]} to {reservation['end_time'][5:16]}.")


def reservation_cancelled(reservation) -> None:
    notification_repo.add(reservation["user_id"], "reservation",
                          f"Reservation for slot {reservation['slot_code']} was cancelled.")


def payment_status(payment, user_id: int) -> None:
    if payment["status"] == "success":
        text = (f"Payment of ₹{payment['amount']:.2f} received for {payment['vehicle_number']}. "
                f"Receipt {payment['public_id']}.")
    else:
        text = (f"Payment of ₹{payment['amount']:.2f} for {payment['vehicle_number']} failed. "
                "You have not been charged.")
    notification_repo.add(user_id, "payment", text)


def sweep(user_id: int) -> None:
    """Create expiry notices that have become due. Cheap enough to run per request."""
    now = clock.now()
    n, soon = clock.to_str(now), clock.to_str(now + timedelta(minutes=EXPIRY_WARNING_MINUTES))
    for r in notification_repo.reservations_expiring(user_id, n, soon):
        notification_repo.add(user_id, "expiry",
                              f"Your reservation of slot {r['slot_code']} for {r['vehicle_number']} "
                              f"ends at {r['end_time'][11:16]}.")
        notification_repo.set_expiry_notified(r["id"], 1)
    for r in notification_repo.overstays(user_id, n):
        notification_repo.add(user_id, "expiry",
                              f"Parking time for {r['vehicle_number']} in slot {r['slot_code']} ended at "
                              f"{r['end_time'][11:16]}. Extra time is charged at the hourly rate.")
        notification_repo.set_expiry_notified(r["id"], 2)


def inbox(user_id: int):
    sweep(user_id)
    rows = notification_repo.for_user(user_id)
    notification_repo.mark_all_read(user_id)
    return rows


def unread(user_id: int) -> int:
    return notification_repo.unread_count(user_id)
