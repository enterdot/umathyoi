import logging

logger = logging.getLogger(__name__)

from typing import Iterator
from .card import Card
from .event import Event
from common import auto_title_from_instance


class Deck:
    """A deck containing up to 6 cards with limit break levels and mute state."""

    SIZE: int = 6

    def __init__(
        self,
        cards: list[Card | None] | None = None,
        limit_breaks: list[int] | None = None,
    ) -> None:

        self._cards: list[Card | None] = [None] * Deck.SIZE
        if cards is not None:
            if len(cards) > Deck.SIZE:
                logger.warning(
                    f"Deck size is {Deck.SIZE} but {len(cards)} cards were given, discarding {len(cards) - Deck.SIZE}"
                )
                self._cards = cards[: Deck.SIZE]
            else:
                self._cards = cards + [None] * (Deck.SIZE - len(cards))

        self._limit_breaks: list[int] = [0] * Deck.SIZE
        if limit_breaks is not None:
            if len(limit_breaks) > Deck.SIZE:
                logger.warning(
                    f"Deck size is {Deck.SIZE} but {len(limit_breaks)} limit breaks were given, discarding {len(limit_breaks) - Deck.SIZE}"
                )
                self._limit_breaks = limit_breaks[: Deck.SIZE]
            else:
                self._limit_breaks = limit_breaks + [0] * (
                    Deck.SIZE - len(limit_breaks)
                )

        # Mute state for each slot
        self._muted: list[bool] = [False] * Deck.SIZE

        self.card_added_at_slot: Event = Event()
        self.card_removed_at_slot: Event = Event()
        self.limit_break_set_at_slot: Event = Event()
        self.mute_toggled_at_slot: Event = Event()
        self.deck_was_cleared: Event = Event()
        self.deck_pushed_past_capacity: Event = Event()

        logger.info(f"{auto_title_from_instance(self)} initialized: {self}")

    @property
    def size(self) -> int:
        """Maximum number of cards this deck can hold."""
        return Deck.SIZE

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

    @property
    def cards(self) -> list[Card]:
        """List of all cards currently in the deck (including muted)."""
        return [card for card in self._cards if card]

    @property
    def active_cards(self) -> list[Card]:
        """List of active (non-muted) cards in the deck."""
        return [
            card
            for card, muted in zip(self._cards, self._muted)
            if card and not muted
        ]

    def is_muted_at_slot(self, slot: int) -> bool:
        """Check if card at slot is muted."""
        return self._muted[slot]

    def set_mute_at_slot(self, slot: int, muted: bool) -> bool:
        """Set mute state at specified slot."""
        if not 0 <= slot < Deck.SIZE:
            raise ValueError(
                f"Invalid slot {slot}, must be in range [0, {Deck.SIZE})"
            )

        if self._cards[slot] is None:
            logger.debug(f"Cannot mute empty slot {slot} for deck {self}")
            return False

        self._muted[slot] = muted
        logger.debug(f"Set mute={muted} at slot {slot} for deck {self}")
        self.mute_toggled_at_slot.trigger(self, muted=muted, slot=slot)
        return True

    def toggle_mute_at_slot(self, slot: int) -> bool | None:
        """Toggle mute state at specified slot."""
        if self._cards[slot] is None:
            return None

        new_state = not self._muted[slot]
        self.set_mute_at_slot(slot, new_state)
        return new_state

    def remove_card_at_slot(self, slot: int) -> Card | None:
        """Remove card at the specified slot."""
        removed_card = self._cards[slot]
        self._cards[slot] = None
        self._limit_breaks[slot] = Card.MIN_LIMIT_BREAK
        self._muted[slot] = False  # Reset mute state
        if removed_card:
            logger.debug(f"Removed card at slot {slot} from deck {self}")
            self.card_removed_at_slot.trigger(
                self, card=removed_card, slot=slot
            )
        return removed_card

    def remove_card_by_id(self, card_id: int) -> int | None:
        """Remove card with the specified ID."""
        for slot, card in enumerate(self._cards):
            if card and card.id == card_id:
                self.remove_card_at_slot(slot)
                return slot
        return None

    def remove_card(self, card: Card) -> int | None:
        """Remove the specified card."""
        return self.remove_card_by_id(card.id)

    def add_card(
        self, card: Card, limit_break: int = Card.MIN_LIMIT_BREAK
    ) -> int | None:
        """Add card to first available slot."""
        logger.debug(
            f"Adding card {card.id} at limit break {limit_break} to deck {self}"
        )
        if card in self:
            logger.debug(
                f"Failed to add card {card.id}, already in deck {self}"
            )
            return None

        slot = self.find_first_empty_slot()
        if slot is not None:
            self._cards[slot] = card
            self.set_limit_break_at_slot(slot, limit_break)
            self._muted[slot] = False  # New cards start unmuted
            logger.debug(f"Added card {card.id} at slot {slot} to deck {self}")
            self.card_added_at_slot.trigger(self, card=card, slot=slot)
            return slot
        else:
            logger.debug(f"Could not add card {card.id}, deck {self} is full")
            self.deck_pushed_past_capacity.trigger(self, card=card)
            return None

    def add_card_at_slot(
        self, slot: int, card: Card, limit_break: int = Card.MIN_LIMIT_BREAK
    ) -> bool:
        """Add card at specific slot."""
        if card in self:
            return False

        if self._cards[slot] is not None:
            return False

        self._cards[slot] = card
        self._muted[slot] = False
        self.card_added_at_slot.trigger(self, card=card, slot=slot)
        self.set_limit_break_at_slot(slot, limit_break)
        return True

    def find_first_empty_slot(self, reverse: bool = False) -> int | None:
        """Find first empty slot in deck."""
        slots = range(Deck.SIZE - 1, -1, -1) if reverse else range(Deck.SIZE)
        for slot in slots:
            if self._cards[slot] is None:
                return slot
        return None

    def get_card_at_slot(self, slot: int) -> Card | None:
        """Get card at specified slot."""
        return self._cards[slot]

    def get_limit_break_at_slot(self, slot: int) -> int:
        """Get limit break level at specified slot."""
        return self._limit_breaks[slot]

    def set_limit_break_at_slot(self, slot: int, limit_break: int) -> bool:
        """Set limit break level at specified slot."""
        if not 0 <= slot < Deck.SIZE:
            raise ValueError(
                f"Invalid slot {slot}, must be in range [0, {Deck.SIZE})"
            )
        if not Card.MIN_LIMIT_BREAK <= limit_break <= Card.MAX_LIMIT_BREAK:
            raise ValueError(
                f"Invalid limit_break {limit_break}, must be in range [{Card.MIN_LIMIT_BREAK}, {Card.MAX_LIMIT_BREAK}]"
            )

        if self._cards[slot] is None:
            logger.debug(
                f"Cannot set limit break on empty slot {slot} for deck {self}"
            )
            return False
        self._limit_breaks[slot] = limit_break
        logger.debug(
            f"Set limit break {self._limit_breaks[slot]} at slot {slot} for deck {self}"
        )
        self.limit_break_set_at_slot.trigger(
            self, limit_break=limit_break, slot=slot
        )
        return True

    def clear(self) -> None:
        """Remove all cards from deck."""
        cards_removed_count = 0
        for slot in range(Deck.SIZE):
            card_removed = self.remove_card_at_slot(slot)
            if card_removed is not None:
                cards_removed_count += 1
        self.deck_was_cleared.trigger(
            self, cards_removed_count=cards_removed_count
        )

    def __contains__(self, card: Card) -> bool:
        """Check if card is in deck."""
        return card in self._cards

    def __iter__(self) -> Iterator[tuple[int, Card | None, int, bool]]:
        """Iterate over deck slots.

        Yields:
            Tuple of (slot, card, limit_break, muted) for each position
        """
        for slot, (card, limit_break, muted) in enumerate(
            zip(self._cards, self._limit_breaks, self._muted)
        ):
            yield (slot, card, limit_break, muted)

    def __str__(self) -> str:
        return f"{[elem[1].id for elem in self if elem[1]]}"
