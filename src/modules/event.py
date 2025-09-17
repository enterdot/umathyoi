from typing import Callable, Any
from utils import Logger


class Event:
    def __init__(self) -> None:
        self._callbacks: list[Callable[..., Any]] = []

    def subscribe(self, callback: Callable[..., Any]) -> None:
        if callback not in self._callbacks:
            self._callbacks.append(callback)
            Logger.debug(f"Callback {callback.__name__} has subscribed", event=self)

    def unsubscribe(self, callback: Callable[..., Any]) -> None:
        if callback in self._callbacks:
            self._callbacks.remove(callback)
            Logger.debug(f"Callback {callback.__name__} has unsubscribed", event=self)

    def trigger(self, caller: Any, **kwargs: Any) -> None:
        for callback in self._callbacks:
            callback(caller, **kwargs)
            Logger.debug("Event triggered", event=self, callbacks=self.count)
    
    @property
    def count(self) -> int:
        """Number of subscribed callbacks."""
        return len(self._callbacks)
