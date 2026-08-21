import re

PHONE_RE = re.compile(r"^\+998\d{9}$")


def normalize_uz_phone(raw: str) -> str | None:
    digits = re.sub(r"[^\d]", "", raw)
    if digits.startswith("998") and len(digits) == 12:
        digits = digits
    elif len(digits) == 9:
        digits = "998" + digits
    else:
        return None

    phone = f"+{digits}"
    return phone if PHONE_RE.match(phone) else None
