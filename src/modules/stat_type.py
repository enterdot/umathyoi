from enum import Enum


class StatType(Enum):
    """Enum for the five core stats in Uma Musume."""
    SPEED = 1
    STAMINA = 2
    POWER = 3
    GUTS = 4
    WIT = 5

    def __str__(self) -> str:
        return self.name.title()
