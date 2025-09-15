from enum import Enum
from dataclasses import dataclass
from typing import Iterator

class Rarity(Enum):
    R = 1
    SR = 2
    SSR = 3

    def __str__(self) -> str:
        return self.name


class CardType(Enum):
    SPEED = 1
    STAMINA = 2
    POWER = 3
    GUTS = 4
    WIT = 5
    PAL = 6
    GROUP = 7

    def __str__(self) -> str:
        return self.name.title()


@dataclass
class Card:
    id: int
    name: str
    view_name: str
    rarity: Rarity
    type: CardType
    limit_breaks: dict[int, dict[str, int]]

    def get_stats_at_limit_break(self, limit_break: int) -> dict[str, int]:
        return self.limit_breaks.get(limit_break, {})

    def get_stats(self) -> Iterator[dict[str, int]]:
        for limit_break in self.limit_breaks.values():
            yield limit_break

    def __repr__(self) -> str:
        return f"Card(id={self.id}, name='{self.name}', rarity={self.rarity}, type={self.type})"
