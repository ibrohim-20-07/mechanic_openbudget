from decimal import Decimal


def format_money(amount: Decimal | int | str) -> str:
    value = int(Decimal(amount))
    return f"{value:,}".replace(",", " ") + " so'm"


def mask_card(card_number: str) -> str:
    digits = "".join(ch for ch in card_number if ch.isdigit())
    if len(digits) < 8:
        return card_number
    return f"{digits[:4]} **** **** {digits[-4:]}"
