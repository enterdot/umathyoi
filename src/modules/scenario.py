from enum import Enum
from dataclasses import dataclass
from datetime import date
from .character import StatType


class FacilityType(Enum):
    speed = 1
    stamina = 2
    power = 3
    guts = 4
    wit = 5


@dataclass(frozen=True)
class Facility:
    """Represents a training facility with level-based gains."""

    MIN_LEVEL = 1
    MAX_LEVEL = 5
    PREFERRED_BASE_WEIGHT = 100
    NON_APPEARANCE_BASE_WEIGHT = 50

    type: FacilityType
    level: int
    stat_gain: dict[int, dict[StatType, int]]  # level -> {stat_type: value}
    skill_points_gain: dict[int, int]  # level -> skill_points
    energy_gain: dict[
        int, int
    ]  # level -> energy value (negative = cost, positive = recovery)

    def get_stat_gain_at_level(self, level: int, stat_type: StatType) -> int:
        """Get specified stat gain for training at specified facility level."""
        level_stats = self.stat_gain.get(level, {})
        return level_stats.get(stat_type, 0)

    def get_all_stat_gains_at_level(self, level: int) -> dict[StatType, int]:
        """Get all stat gains for training at specified facility level."""
        return self.stat_gain.get(level, {}).copy()

    def get_skill_points_gain_at_level(self, level: int) -> int:
        """Get skill points gain for training at specified facility level."""
        return self.skill_points_gain.get(level, 0)

    def get_energy_gain_at_level(self, level: int) -> int:
        """Get energy cost/gain for training at specified facility level."""
        return self.energy_gain.get(level, -20)  # Default to -20 energy cost


@dataclass(frozen=True)
class Scenario:
    """Represents a game scenario with facility configurations."""

    name: str
    id: int
    release: date | None
    facilities: dict[FacilityType, Facility]

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other) -> bool:
        if not isinstance(other, self.__class__):
            return False
        return self.id == other.id
