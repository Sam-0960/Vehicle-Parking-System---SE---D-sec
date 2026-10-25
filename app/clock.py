"""Single source of the current time, so fee and expiry logic is testable."""
from datetime import datetime

FMT = "%Y-%m-%d %H:%M:%S"
_override = None


def now() -> datetime:
    return _override or datetime.now().replace(microsecond=0)


def set_now(value) -> None:
    """Tests only: freeze the clock (pass None to unfreeze)."""
    global _override
    _override = value


def to_str(dt: datetime) -> str:
    return dt.strftime(FMT)


def parse(value: str) -> datetime:
    return datetime.strptime(value, FMT)
