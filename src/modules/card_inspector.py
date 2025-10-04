import logging

logger = logging.getLogger(__name__)

from .card import Card
from .event import Event
from common import auto_title_from_instance


class CardInspector:
    """Tracks currently inspected card and limit break level for info display."""

    def __init__(self, card: Card | None = None, limit_break: int = 0) -> None:
        """Initialize card stats tracker."""
        self._card: Card | None = card
        self._limit_break: int = limit_break

        self.card_changed: Event = Event()
        self.limit_break_changed: Event = Event()

        logger.debug(f"{auto_title_from_instance(self)} initialized")

    @property
    def card(self) -> Card | None:
        """Currently inspected card."""
        return self._card

    @card.setter
    def card(self, card: Card | None) -> None:
        """Set currently inspected card."""
        if card != self._card:
            prev_card = self._card
            self._card = card
            self.card_changed.trigger(self, card=self._card, prev_card=prev_card)

    @property
    def limit_break(self) -> int:
        """Currently selected limit break level."""
        return self._limit_break

    @limit_break.setter
    def limit_break(self, limit_break: int) -> None:
        """Set limit break level."""
        if not (Card.MIN_LIMIT_BREAK <= limit_break <= Card.MAX_LIMIT_BREAK):
            raise ValueError(f"{limit_break=} is not in range [{Card.MIN_LIMIT_BREAK}, {Card.MAX_LIMIT_BREAK}]")

        if limit_break != self._limit_break:
            prev_limit_break = self._limit_break
            self._limit_break = limit_break
            self.limit_break_changed.trigger(self, card=self._card, limit_break=self._limit_break, prev_limit_break=prev_limit_break)
