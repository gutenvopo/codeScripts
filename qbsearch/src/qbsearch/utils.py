from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from time import monotonic
from typing import ParamSpec, TypeVar

P = ParamSpec("P")
T = TypeVar("T")


def human_size(value: int) -> str:
    if value is None or value < 0:
        return "Unknown"
    size = float(value)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024 or unit == "TB":
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.2f} {unit}"
        size /= 1024
    return "Unknown"


def throttle(seconds: float) -> Callable[[Callable[P, T]], Callable[P, T | None]]:
    def decorator(func: Callable[P, T]) -> Callable[P, T | None]:
        last = 0.0

        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T | None:
            nonlocal last
            now = monotonic()
            if now - last < seconds:
                return None
            last = now
            return func(*args, **kwargs)

        return wrapper

    return decorator
