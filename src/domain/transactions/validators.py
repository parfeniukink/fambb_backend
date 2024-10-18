import contextlib
from datetime import date, datetime
from typing import Any

from .formatters import as_cents


def cents_from_raw(value: Any, /, **_) -> int:
    """try getting 'cents' money representation from the raw data.

    validations:
        available types: int, float, string
        available value range: (0..n) (positive numbers, exclude 0)

    errors:
        ValueError - in any case the validator is not happy
    """

    if isinstance(value, str):
        try:
            _result: int = as_cents(float(value))
        except ValueError as error:
            raise ValueError(
                f"Can not convert {value} to the proper value"
            ) from error
    elif isinstance(value, int):
        _result = value
    elif isinstance(value, float):
        _result = as_cents(value)
    else:
        raise ValueError(
            f"Can not convert {value}, the type of {type(value)} to cents"
        )

    if _result == 0:
        raise ValueError("The value must be greater than `0`")
    elif _result < 0:
        raise ValueError("The value must be a positive value")

    return _result


def timestamp_from_raw(value: Any, /, **_) -> date:
    """try converting the value to the date insatnce.

    errors:
        ValueError - proxied from the core `datetime` module

    workflow:
        - handle the native data type
        - try to convert the proper date string
        - try to convert the whole TIMESTAMP to the date
    """

    if isinstance(value, date):
        return value
    elif isinstance(value, str):
        with contextlib.suppress(ValueError):
            return datetime.strptime(value, "%Y-%m-%d").date()

        try:
            result = datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%f").date()
        except ValueError as error:
            raise ValueError(
                "Invalid TIMESTAMP string. Format: %Y-%m-%dT%H:%M:%S.%f"
            ) from error
        else:
            return result
    else:
        raise ValueError(
            f"Can not convet {value} of type {type(value)} "
            "to the `datetime.date` in Python"
        )
