from typing import Callable, Any


class Event:
    def __init__(self) -> None:
        self._callbacks: list[Callable[..., Any]] = []

    def subscribe(self, callback: Callable[..., Any]) -> None:
        if callback not in self._callbacks:
            self._callbacks.append(callback)

    def unsubscribe(self, callback: Callable[..., Any]) -> None:
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    def trigger(self, caller: Any, **kwargs: Any) -> None:
        for callback in self._callbacks:
            callback(caller, **kwargs)
