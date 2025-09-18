import logging
logger = logging.getLogger(__name__)

from typing import Callable, Any


class Event:
    def __init__(self) -> None:
        self._callbacks: list[Callable[..., Any]] = []

    def subscribe(self, callback: Callable[..., Any]) -> None:
        if callback not in self._callbacks:
            self._callbacks.append(callback)
            logger.debug(f"Callback subscribed: {callback.__name__}")

    def unsubscribe(self, callback: Callable[..., Any]) -> None:
        if callback in self._callbacks:
            self._callbacks.remove(callback)
            logger.debug(f"Callback unsubscribed: {callback.__name__}")

    def trigger(self, caller: Any, **kwargs: Any) -> None:
        for callback in self._callbacks:
            callback(caller, **kwargs)
            logger.debug(f"{caller.__class__.__name__} triggered {self.count} callbacks")
    
    @property
    def count(self) -> int:
        """Number of subscribed callbacks."""
        return len(self._callbacks)
