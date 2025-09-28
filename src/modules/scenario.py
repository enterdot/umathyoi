from enum import Enum
from dataclasses import dataclass
from datetime import date
from .character import StatType
from utils import CharacterConstants, GameplayConstants

class FacilityType(Enum):
    speed = 1
    stamina = 2
    power = 3
    guts = 4
    wit = 5

@dataclass
class Facility:
    """Represents a training facility with level-based gains."""
    _type: FacilityType
    _level: int
    _stat_gain: dict[int, dict[StatType, int]]  # level -> {stat_type: value}
    _skill_points_gain: dict[int, int]  # level -> skill_points
    _energy_gain: dict[int, int] # level -> value
    
    def __post_init__(self):
        self._assert_facility_level(self._level)

    def _assert_facility_level(self, level: int) -> None:
        if not (GameplayConstants.MIN_FACILITY_LEVEL <= level <= GameplayConstants.MAX_FACILITY_LEVEL):
            raise RuntimeError(f"Facility level was {level}, must be [{GameplayConstants.MIN_FACILITY_LEVEL}, {GameplayConstants.MAX_FACILITY_LEVEL}]")

    @property
    def type(self) -> FacilityType:
        """Get facility type."""
        return self._type
    
    @property
    def level(self) -> int:
        """Get current facility level."""
        return self._level
    
    @level.setter
    def level(self, new_level: int) -> None:
        """Set facility level."""
        self._assert_facility_level(new_level)
        self._level = new_level
    
    def get_stat_gain_at_level(self, level: int, stat_type: StatType) -> int:
        """Get specified stat gain for training at specified facility level."""
        return self._stat_gain.get(level).get(stat_type)
    
    def get_stat_gain_at_current_level(self, stat_type: StatType) -> int:
        """Get specified stat gain for training at current facility level."""
        return self.get_stat_gain_at_level(self._level, stat_type)
    
    def get_skill_points_gain_at_level(self, level: int) -> int:
        """Get skill points gain for training at specified facility level."""
        return self._skill_points_gain.get(level)
    
    def get_skill_points_gain_at_current_level(self) -> int:
        """Get skill points gain for training at current facility level."""
        return self.get_skill_points_gain_at_level(self._level)
    
    def get_energy_gain_at_level(self, level: int) -> int:
        """Get energy cost for training at specified facility level."""
        return self._energy_gain.get(level)

    def get_energy_gain_at_current_level(self, level: int) -> int:
        """Get energy cost for training at current facility level."""
        return self._energy_gain.get(self._level)


@dataclass
class Scenario:
    _name: str
    _id: int
    _release: date
    _facilities: dict[FacilityType, Facility]
