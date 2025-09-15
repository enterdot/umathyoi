from typing import Iterator
from .card import Card
from .event import Event

class CardStats:
    def __init__(self, card: Card = None, limit_break: int = 0) -> None:
        self._card: Card = card
        self._limit_break: int = limit_break

        self.card_changed: Event = Event()
        self.limit_break_changed: Event = Event()

    @property
    def card(self):
        return self._card

    @card.setter
    def card(self, card: Card) -> None:
        prev_card = self._card
        self._card = card
        self.card_changed.trigger(self, card=self._card, prev_card=prev_card)

    @property
    def limit_break(self):
        return self._limit_break

    @limit_break.setter
    def limit_break(self, limit_break: int) -> None:
        prev_limit_break = self._limit_break
        self._limit_break = limit_break
        self.limit_break_changed.trigger(self, card=self._card, prev_limit_break=prev_limit_break)

    def get_limit_break(self) -> int:
        return self._limit_break

    def get_card(self) -> Card:
        return self._card
