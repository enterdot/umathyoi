from typing import Iterator
from .deck import Deck
from .event import Event

class DeckList:
    def __init__(self, size: int = 5, decks: list[Deck | None] | None = None) -> None:
        if size < 1:
            raise ValueError(f"Size {size} is not valid, it must be positive")  # Fixed f-string
        self._size: int = size

        if decks is not None:
            if len(decks) > size:
                print(f"DeckList size is {size} but {len(decks)} decks were given, discarding {len(decks) - size}")  # Fixed calculation
                decks = decks[:size]
            self._decks = [deck if deck is not None else Deck() for deck in decks]

            if len(self._decks) < size:
                self._decks.extend([Deck() for _ in range(size - len(self._decks))])
        else:
            self._decks = [Deck() for _ in range(size)]
            
        self._active_slot: int = 0

        self.slot_activated: Event = Event()
        self.slot_deactivated: Event = Event()

    @property
    def active_deck(self) -> Deck | None:
        return self._decks[self._active_slot]

    @property
    def active_slot(self) -> int:
        return self._active_slot

    @active_slot.setter
    def active_slot(self, index: int) -> None:
        if 0 <= index < self._size:
            if index != self.active_slot:
                self.slot_deactivated.trigger(self, index=self.active_slot, deck=self.active_deck)
                self._active_slot = index
                self.slot_activated.trigger(self, index=self.active_slot, deck=self.active_deck)
                print(f"activated deck in slot {self._active_slot}")
        else:
            raise ValueError(f"Slot {index} is out of bounds") 

    @property
    def slot_count(self):
        return self._size

    def get_slot_at_offset(self, offset: int) -> int:
        offset_index = self._active_slot + offset
        offset_index = ((offset_index % self._size) + self._size) % self._size
        return offset_index

    def get_deck_at_offset(self, offset: int) -> Deck:
        index = self.get_slot_at_offset(offset)
        return self._decks[index]

    def get_deck_at_slot(self, index: int):
        return self._decks[index]

    @property
    def next_slot(self):
        return self.get_slot_at_offset(1)

    @property
    def previous_slot(self):
        return self.get_slot_at_offset(-1)
    
    @property
    def next_deck(self) -> Deck | None:
        return self.get_deck_at_offset(1)  

    @property
    def previous_deck(self):
        return self.get_deck_at_offset(-1)

    def __contains__(self, deck: Deck) -> bool:
        return deck in self._decks

    def __iter__(self):
        for index in range(self._size):
            yield (index, self._decks[index])

    def __repr__(self):
        return f"DeckList(size={self._size}, decks={self._decks})"
    
    def __str__(self):
        return f"{self._decks}"

