import logging
logger = logging.getLogger(__name__)

from typing import Iterator
from .card import Card
from .event import Event
from utils import DeckConstants, CardConstants


class Deck:
    """A deck containing up to 6 cards with limit break levels."""
    
    def __init__(self, name: str = "New Deck", size: int = DeckConstants.DEFAULT_DECK_SIZE, cards: list[Card | None] | None = None, limit_breaks: list[int] | None = None) -> None:
        """Initialize a new deck.
        
        Args:
            name: Display name for the deck
            size: Maximum number of cards
            cards: Optional list of initial cards
            limit_breaks: Optional list of limit break levels for initial cards
        """
        self.name: str = name

        if size < DeckConstants.MIN_DECK_SIZE:
            raise ValueError(f"Size {size} is not valid, it must be at least {DeckConstants.MIN_DECK_SIZE}.")
        self._size: int = size

        self._cards: list[Card | None] = [None] * size
        if cards is not None:
            if len(cards) > size:
                logger.warning(f"Deck size is {size} but {len(cards)} cards were given, discarding {len(cards) - size}")
                self._cards = cards[:size]
            else:
                self._cards = cards + [None] * (size - len(cards))

        self._limit_breaks: list[int] = [0] * size
        if limit_breaks is not None:
            if len(limit_breaks) > size:
                logger.warning(f"Deck size is {size} but {len(limit_breaks)} limit breaks were given, discarding {len(limit_breaks) - size}")
                self._limit_breaks = limit_breaks[:size]
            else:
                self._limit_breaks = limit_breaks + [0] * (size - len(limit_breaks))

        self.card_added_at_slot: Event = Event()
        self.card_removed_at_slot: Event = Event()
        self.limit_break_set_at_slot: Event = Event()
        self.deck_was_cleared: Event = Event()
        self.deck_pushed_past_capacity: Event = Event()

    @property
    def size(self) -> int:
        """Maximum number of cards this deck can hold."""
        return self._size

    @property
    def is_full(self) -> bool:
        """True if deck contains maximum number of cards."""
        return all(card is not None for card in self._cards)

    @property
    def is_empty(self) -> bool:
        """True if deck contains no cards."""
        return all(card is None for card in self._cards)

    @property
    def count(self) -> int:
        """Number of cards currently in the deck."""
        return sum(1 for card in self._cards if card is not None)

    def remove_card_at_slot(self, slot: int) -> Card | None:
        """Remove card at the specified slot.
        
        Args:
            slot: Slot position (0-based)
            
        Returns:
            The removed card, or None if slot was empty
        """
        removed_card = self._cards[slot]
        self._cards[slot] = None
        self._limit_breaks[slot] = 0  # Reset when removing #TODO: Use constant
        if removed_card:
            logger.debug(f"Removed card at slot {slot} from deck '{self.name}'")
            self.card_removed_at_slot.trigger(self, card=removed_card, slot=slot)
        return removed_card

    def remove_card_by_id(self, card_id: int) -> int | None:
        """Remove card with the specified ID.
        
        Args:
            card_id: ID of card to remove
            
        Returns:
            Slot position where card was removed, or None if not found
        """
        for slot, card in enumerate(self._cards):
            if card and card.id == card_id:
                self.remove_card_at_slot(slot)
                return slot
        return None

    def remove_card(self, card: Card) -> int | None:
        """Remove the specified card.
        
        Args:
            card: Card to remove
            
        Returns:
            Slot position where card was removed, or None if not found
        """
        return self.remove_card_by_id(card.id)

    def add_card(self, card: Card, limit_break: int = 0) -> int | None:
        """Add card to first available slot.
        
        Args:
            card: Card to add
            limit_break: Initial limit break level
            
        Returns:
            Slot position where card was added, or None if deck is full
        """
        logger.debug(f"Adding card {card.id} at limit break {limit_break} to deck '{self.name}'")
        if card in self:
            logger.debug(f"Failed to add card {card.id}, already in deck '{self.name}'")
            return None

        slot = self.find_first_empty_slot()
        if slot is not None:
            self._cards[slot] = card
            self.set_limit_break_at_slot(slot, limit_break)
            logger.debug(f"Added card {card.id} at slot {slot} to deck '{self.name}'")
            self.card_added_at_slot.trigger(self, card=card, slot=slot)
            return slot
        else:
            logger.debug(f"Could not add card {card.id}, deck '{self.name}' is full")
            self.deck_pushed_past_capacity.trigger(self, card=card)
            return None

    def add_card_at_slot(self, slot: int, card: Card, limit_break: int = 0) -> bool:
        """Add card at specific slot.
        
        Args:
            slot: Target slot position
            card: Card to add
            limit_break: Initial limit break level
            
        Returns:
            True if card was added, False if slot occupied or card already in deck
        """
        if card in self:
            return False  # Card already in deck

        if self._cards[slot] is not None:
            return False  # Slot already occupied

        self._cards[slot] = card
        self.card_added_at_slot.trigger(self, card=card, slot=slot)
        self.set_limit_break_at_slot(slot, limit_break)
        return True

    def find_first_empty_slot(self, reverse: bool = False) -> int | None:
        """Find first empty slot in deck.
        
        Args:
            reverse: If True, search from last slot to first
            
        Returns:
            Slot position, or None if deck is full
        """
        slots = range(self._size - 1, -1, -1) if reverse else range(self._size)
        for slot in slots:
            if self._cards[slot] is None:
                return slot
        return None

    def get_card_at_slot(self, slot: int) -> Card | None:
        """Get card at specified slot.
        
        Args:
            slot: Slot position
            
        Returns:
            Card at slot, or None if empty
        """
        return self._cards[slot]

    def get_limit_break_at_slot(self, slot: int) -> int:
        """Get limit break level at specified slot.
        
        Args:
            slot: Slot position
            
        Returns:
            Limit break level
        """
        return self._limit_breaks[slot]

    def set_limit_break_at_slot(self, slot: int, limit_break: int) -> bool:
        """Set limit break level at specified slot.
        
        Args:
            slot: Slot position
            limit_break: New limit break level
            
        Returns:
            True if set successfully, False if slot is empty
        """
        # Validate parameters
        if not 0 <= slot < self._size:
            raise ValueError(f"Invalid slot {slot}, must be in range [0, {self._size})")
        if not CardConstants.MIN_LIMIT_BREAK <= limit_break <= CardConstants.MAX_LIMIT_BREAK:
            raise ValueError(f"Invalid limit_break {limit_break}, must be in range [{CardConstants.MIN_LIMIT_BREAK}, {CardConstants.MAX_LIMIT_BREAK}]")
        
        if self._cards[slot] is None:
            logger.debug(f"Cannot set limit break on empty slot {slot} for deck '{self.name}'")
            return False
        self._limit_breaks[slot] = limit_break
        logger.debug(f"Set limit break {self._limit_breaks[slot]} at slot {slot} for deck '{self.name}'")
        self.limit_break_set_at_slot.trigger(self, limit_break=limit_break, slot=slot)
        return True

    def clear(self) -> None:
        """Remove all cards from deck."""
        cards_removed_count = 0
        for slot in range(self._size):
            card_removed = self.remove_card_at_slot(slot)
            if card_removed is not None:
                cards_removed_count += 1
        self.deck_was_cleared.trigger(self, cards_removed_count=cards_removed_count)

    def __contains__(self, card: Card) -> bool:
        """Check if card is in deck."""
        return card in self._cards

    def __iter__(self) -> Iterator[tuple[int, Card | None, int]]:
        """Iterate over deck slots.
        
        Yields:
            Tuple of (slot, card, limit_break) for each position
        """
        for slot, (card, limit_break) in enumerate(zip(self._cards, self._limit_breaks)):
            yield (slot, card, limit_break)

    def __str__(self) -> str:
        return f"{self.name} ({self.count}/{self._size}): {[elem for elem in self if elem[1]]}"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}', count={self.count}/{self._size}, cards={[card.id for card in self._cards if card]})"
