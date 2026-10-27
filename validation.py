import re
from datetime import datetime, date

EMAIL_RE = re.compile(r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+$")

def _parse_date(value, input_date_format="slash"):
    value = str(value).strip()
    if input_date_format == "slash":
        fmt = "%d/%m/%Y"
    elif input_date_format == "dot":
        fmt = "%d.%m.%Y"
    else:
        raise ValueError("Unsupported date format")
    parsed = datetime.strptime(value, fmt).date()
    return parsed

def validate_patient(raw, input_date_format="slash"):
    errors = []
    clean = {}
    name = str(raw.get("full_name", "")).strip()
    if not name:
        errors.append("Full Name is required.")
    elif len(name) > 120:
        errors.append("Full Name must be 120 characters or fewer.")
    else:
        clean["full_name"] = name

    dob_raw = str(raw.get("date_of_birth", "")).strip()
    try:
        dob = _parse_date(dob_raw, input_date_format)
        if dob > date.today():
            errors.append("Date of Birth cannot be in the future.")
        else:
            clean["date_of_birth"] = dob.strftime("%d/%m/%Y")
    except ValueError:
        expected = "dd/mm/yyyy" if input_date_format == "slash" else "dd.mm.yyyy"
        errors.append(f"Date of Birth must be a real calendar date in {expected} format.")

    email = str(raw.get("email", "")).strip()
    if not EMAIL_RE.fullmatch(email):
        errors.append("Email Address is not in a valid email format (example: name@example.com).")
    else:
        clean["email"] = email

    numeric_fields = [
        ("glucose", "Glucose"),
        ("haemoglobin", "Haemoglobin"),
        ("cholesterol", "Cholesterol"),
    ]
    for key, label in numeric_fields:
        value = str(raw.get(key, "")).strip()
        try:
            number = float(value)
            if not (number >= 0 and number < float("inf")):
                raise ValueError()
            clean[key] = number
        except (ValueError, TypeError):
            errors.append(f"{label} must be a non-negative numeric value.")
    return errors, clean

def validate_import_row(raw):
    # The supplied assignment table uses dd.mm.yyyy; preserve that source format while validating it.
    return validate_patient(raw, input_date_format="dot")

def calculate_age(dob_string):
    dob = datetime.strptime(dob_string, "%d/%m/%Y").date()
    today = date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
