from typing import Iterator
from .card import Card
from .event import Event


class Deck:
    def __init__(self, name: str = "New Deck", size: int = 6, cards: list[Card | None] | None = None, limit_breaks: list[int] | None = None) -> None:
        self.name: str = name

        if size < 1:
            raise ValueError(f"Size {size} is not valid, it must be positive")
        self._size: int = size

        self._cards: list[Card | None] = [None] * size
        if cards is not None:
            if len(cards) > size:
                print(f"Deck size is {size} but {len(cards)} cards were given, discarding {len(cards) - size}")
                self._cards = cards[:size]
            else:
                self._cards = cards + [None] * (size - len(cards))

        self._limit_breaks: list[int] = [0] * size
        if limit_breaks is not None:
            if len(limit_breaks) > size:
                print(f"Deck size is {size} but {len(limit_breaks)} limit breaks were given, discarding {len(limit_breaks) - size}")
                self._limit_breaks = limit_breaks[:size]
            else:
                self._limit_breaks = limit_breaks + [0] * (size - len(limit_breaks))
        

        self.card_added_at_slot: Event = Event()
        self.card_removed_at_slot: Event = Event()
        self.limit_break_set_at_slot: Event = Event()
        self.deck_was_cleared: Event = Event()
        self.deck_reached_capacity: Event = Event()
        self.deck_pushed_past_capacity: Event = Event()

    def remove_card_at_slot(self, index: int) -> Card | None:
        removed_card = self._cards[index]
        self._cards[index] = None
        self._limit_breaks[index] = 0  # Reset when removing
        self.card_removed_at_slot.trigger(self, card=removed_card, index=index)
        return removed_card

    def remove_card_by_id(self, card_id: int) -> int | None:
        for index, card in enumerate(self._cards):
            if card and card.id == card_id:
                self.remove_card_at_slot(index)
                return index
        return None

    def remove_card(self, card: Card) -> int | None:
        return self.remove_card_by_id(card.id)

    def add_card(self, card: Card, limit_break: int = 0) -> int | None:
        if card in self:
            return None  # Card already in deck

        index = self.find_first_empty_slot()
        if index is not None:
            self._cards[index] = card
            self.set_limit_break_at_slot(limit_break, index)
            self.card_added_at_slot.trigger(self, card=card, index=index)
            return index
        else:
            self.deck_pushed_past_capacity.trigger(self, card=card)
            return None

    def add_card_at_slot(self, index: int, card: Card, limit_break: int = 0) -> bool:
        if card in self:
            return False  # Card already in deck

        if self._cards[index] is not None:
            return False  # Slot already occupied

        self._cards[index] = card
        self.card_added_at_slot.trigger(self, card=card, index=index)
        self.set_limit_break_at_slot(limit_break, index)
        return True

    def find_first_empty_slot(self) -> int | None:
        for index in range(self._size):
            if self._cards[index] is None:
                return index
        return None

    def get_card_at_slot(self, index: int) -> Card | None:
        return self._cards[index]

    def get_limit_break_at_slot(self, index: int) -> int:
        return self._limit_breaks[index]

    def set_limit_break_at_slot(self, limit_break: int, index: int) -> bool:
        if self._cards[index] is None:
            return False  # Can't set limit break on empty index
        self._limit_breaks[index] = limit_break
        self.limit_break_set_at_slot.trigger(self, limit_break=limit_break, index=index)
        return True

    @property
    def is_full(self) -> bool:
        return all(card is not None for card in self._cards)

    @property
    def is_empty(self) -> bool:
        return all(card is None for card in self._cards)

    @property
    def card_count(self) -> int:
        return sum(1 for card in self._cards if card is not None)

    def clear(self) -> None:
        cards_removed_count = 0
        for index in range(self._size):
            card_removed = self.remove_card_at_slot(index)
            if card_removed is not None:
                cards_removed_count += 1
        self.deck_was_cleared.trigger(self, cards_removed_count=cards_removed_count)

    def __contains__(self, card: Card) -> bool:
        return card in self._cards

    def __iter__(self) -> Iterator[tuple[int, Card | None, int]]:
        for index, (card, limit_break) in enumerate(zip(self._cards, self._limit_breaks)):
            yield (index, card, limit_break)

    def __str__(self) -> str:
        return f"Deck '{self.name}': {self.card_count}/{self._size} cards"

    def __repr__(self) -> str:
        cards_repr = [f"Slot {i}: {card.view_name if card else 'Empty'}" for i, card in enumerate(self._cards)]
        return f"Deck(name='{self.name}', cards=[{', '.join(cards_repr)}])"
