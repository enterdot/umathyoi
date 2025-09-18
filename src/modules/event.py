from typing import Callable, Any
from utils import Logger


class Event:
    def __init__(self) -> None:
        self._callbacks: list[Callable[..., Any]] = []

    def subscribe(self, callback: Callable[..., Any]) -> None:
        if callback not in self._callbacks:
            self._callbacks.append(callback)
            Logger.debug(f"Callback subscribed.", self, name=callback.__name__)

    def unsubscribe(self, callback: Callable[..., Any]) -> None:
        if callback in self._callbacks:
            self._callbacks.remove(callback)
            Logger.debug(f"Callback unsubscribed.", self, name=callback.__name__)

    def trigger(self, caller: Any, **kwargs: Any) -> None:
        for callback in self._callbacks:
            callback(caller, **kwargs)
            Logger.debug(f"Event triggered.", caller, callbacks=self.count)
    
    @property
    def count(self) -> int:
        """Number of subscribed callbacks."""
        return len(self._callbacks)
