"""Human-friendly validation messages for Persian UI.

FastAPI/Pydantic produce raw, technical error structures. These helpers turn
them into short, user-facing messages so backend validation stays authoritative
without ever leaking framework internals to the user.
"""

from typing import Any

FIELD_LABELS: dict[str, str] = {
    "first_name": "نام",
    "last_name": "نام خانوادگی",
    "username": "یوزرنیم",
    "email": "ایمیل",
    "password": "رمز عبور",
    "education_level": "مقطع تحصیلی",
    "field_of_study": "رشته تحصیلی",
    "activity_field": "زمینه فعالیت",
    "display_name": "نام نمایشی",
}


def _render(field: str | None, error_type: str, message: str) -> str:
    label = FIELD_LABELS.get(field or "", field or "فیلد")

    if field == "email":
        return "یه ایمیل معتبر وارد کن."

    if field == "password":
        return "رمزت باید حداقل ۸ کاراکتر و شامل حرف و عدد باشه."

    if field == "username":
        return (
            "یوزرنیم باید ۳ تا ۳۰ کاراکتر و فقط شامل "
            "حروف انگلیسی، عدد، _ ، . یا - باشه."
        )

    if field in ("first_name", "last_name"):
        if error_type in ("missing", "string_too_short", "value_error"):
            return f"{label} رو وارد کن."
        if error_type == "string_too_long":
            return f"{label} خیلی طولانیه."

    if error_type == "missing":
        return f"{label} رو وارد کن."
    if error_type == "string_too_short":
        return f"{label} خیلی کوتاهه."
    if error_type == "string_too_long":
        return f"{label} خیلی طولانیه."

    return message


def first_friendly_error(errors: list[dict[str, Any]]) -> str:
    """Return the first error as a short, user-facing Persian message."""
    if not errors:
        return "اطلاعات واردشده معتبر نیست."

    err = errors[0]
    loc = err.get("loc", [])
    field = str(loc[-1]) if loc else None
    error_type = str(err.get("type", ""))
    message = str(err.get("msg", ""))

    return _render(field, error_type, message)
