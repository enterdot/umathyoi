from dataclasses import dataclass
from enum import Enum
from typing import ClassVar
from .skill import Skill


class Mood(Enum):
    awful = -2
    bad = -1
    normal = 0
    good = 1
    great = 2

    @property
    def multiplier(self) -> float:
        """Get the mood multiplier for training effectiveness."""
        # TODO: Use int's instead, update EfficiencyCalculator afterwards
        mood_multipliers = {
            Mood.awful: 0.8,  # -20%
            Mood.bad: 0.9,  # -10%
            Mood.normal: 1.0,  # 0%
            Mood.good: 1.1,  # +10%
            Mood.great: 1.2,  # +20%
        }
        return mood_multipliers[self]

    def __str__(self) -> str:
        return self.name.title()


class StatType(Enum):
    """Enum for the five core stats in Uma Musume."""

    speed = 1
    stamina = 2
    power = 3
    guts = 4
    wit = 5

    def __str__(self) -> str:
        return self.name.title()


class Aptitude(Enum):
    S = 1
    A = 0
    B = -1
    C = -2
    D = -3
    E = -4
    F = -5
    G = -6

    def __str__(self) -> str:
        return self.name


@dataclass(frozen=True)
class Character:
    """Represents a trainee (character)."""

    MAX_TOTAL_STAT_BONUS: ClassVar[int] = 30

    id: int  # Full costume ID (e.g., 102840)
    character_id: int  # Base character ID (e.g., 1028)
    name: str  # URL slug name (e.g., "102802-hishi-akebono")
    view_name: str  # Display name (e.g., "Hishi Akebono")
    stat_bonus: list[int]  # [speed, stamina, power, guts, wit] bonuses
    aptitudes: list[Aptitude]  # 10 aptitudes for different conditions

    @property
    def costume_id(self) -> int:
        """Calculate costume ID from full ID and character ID."""
        return self.id - (self.character_id * 100)

    @property
    def track_aptitudes(self) -> list[Aptitude]:
        return self.aptitudes[0,1]
    @property
    def distance_aptitudes(self) -> list[Aptitude]:
        return self.aptitudes[2,5]
    @property
    def style_aptitudes(self) -> list[Aptitude]:
        return self.aptitudes[6,9]
        
    def __post_init__(self) -> None:
        if (
            sum(v for v in self.stat_bonus)
            > self.__class__.MAX_TOTAL_STAT_BONUS
        ):
            raise ValueError(
                f"Total stat growth bonus exceeds {self.__class__.MAX_TOTAL_STAT_BONUS}% limit"
            )

    def get_stat_bonus(self, stat_type: StatType) -> int:
        """Get bonus for a specific stat type."""
        stat_index = {
            StatType.speed: 0,
            StatType.stamina: 1,
            StatType.power: 2,
            StatType.guts: 3,
            StatType.wit: 4,
        }
        return self.stat_bonus[stat_index[stat_type]]

    def get_stat_bonus_string(self, stat_type: StatType) -> str:
        return f"{self.get_stat_bonus(stat_type)}%"

    def get_stat_bonus_multipler(self, stat_type: StatType) -> float:
        return (100 + self.get_stat_bonus(stat_type)) / 100
