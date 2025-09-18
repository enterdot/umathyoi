import logging
logger = logging.getLogger(__name__)

from .card import Card
from .event import Event
from utils import CardConstants, auto_title_from_instance


class CardStats:
    """Tracks currently inspected card and limit break level for info display."""
    
    def __init__(self, card: Card | None = None, limit_break: int = 0) -> None:
        """Initialize card stats tracker.
        
        Args:
            card: Initial card to inspect
            limit_break: Initial limit break level (0-4)
        """
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
        """Set currently inspected card.
        
        Args:
            card: Card to inspect, or None to clear
        """
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
        """Set limit break level.
        
        Args:
            limit_break: Limit break level
        """
        if not (CardConstants.MIN_LIMIT_BREAKS <= limit_break <= CardConstants.MAX_LIMIT_BREAKS):
            raise ValueError(f"Limit break must be {CardConstants.MIN_LIMIT_BREAKS}-{CardConstants.MAX_LIMIT_BREAKS}, got {limit_break}.")
        
        if limit_break != self._limit_break:
            prev_limit_break = self._limit_break
            self._limit_break = limit_break
            self.limit_break_changed.trigger(
                self, 
                card=self._card, 
                limit_break=self._limit_break,
                prev_limit_break=prev_limit_break
            )
