import re


def validate_phone_number(v: str) -> str:
    """
    Validate that the phone number starts with 09 and has 11 digits total.
    """
    pattern = r"^09\d{9}$"
    if not re.match(pattern, v):
        raise ValueError("Phone number must start with 09 and have 11 digits total")
    return v


def validate_password(v: str) -> str:
    """
    Validate password strength requirements.
    """
    if len(v) < 8:
        raise ValueError("Password must be at least 8 characters long")
    if not re.search(r"\d", v):
        raise ValueError("Password must contain at least one digit")
    if not re.search(r"[a-zA-Z]", v):
        raise ValueError("Password must contain at least one letter")
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
        raise ValueError("Password must contain at least one special character")
    return v
