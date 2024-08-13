from datetime import datetime
from typing import Any, Callable, TypeVar


class HTTPDate(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, value: str) -> str:
        try:
            datetime.strptime(value, "%a, %d %b %Y %H:%M:%S GMT")
        except ValueError:
            raise ValueError(f"Invalid HTTP-date format: {value}")
        return value


F = TypeVar("F", bound=Callable[..., Any])
WrappedFn = TypeVar("WrappedFn", bound=Callable[..., Any])
