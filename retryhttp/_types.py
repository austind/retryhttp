from typing import Any, Callable, TypeVar

F = TypeVar("F", bound=Callable[..., Any])
WrappedFn = TypeVar("WrappedFn", bound=Callable[..., Any])
