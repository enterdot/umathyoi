from enum import Enum
from dataclasses import dataclass
from datetime import date
from .character import StatType
from utils import GameplayConstants

class FacilityType(Enum):
    speed = 1
    stamina = 2
    power = 3
    guts = 4
    wit = 5

@dataclass
class Facility:
    """Represents a training facility with level-based gains."""
    type: FacilityType
    level: int
    stat_gain: dict[int, dict[StatType, int]]  # level -> {stat_type: value}
    skill_points_gain: dict[int, int]  # level -> skill_points
    energy_gain: dict[int, int]  # level -> energy value (negative = cost, positive = recovery)
    
    def __post_init__(self):
        self._assert_facility_level(self.level)

    def _assert_facility_level(self, level: int) -> None:
        if not (GameplayConstants.MIN_FACILITY_LEVEL <= level <= GameplayConstants.MAX_FACILITY_LEVEL):
            raise RuntimeError(f"Facility level was {level}, must be [{GameplayConstants.MIN_FACILITY_LEVEL}, {GameplayConstants.MAX_FACILITY_LEVEL}]")
    
    def set_level(self, new_level: int) -> None:
        """Set facility level with validation."""
        self._assert_facility_level(new_level)
        self.level = new_level
    
    def get_stat_gain_at_level(self, level: int, stat_type: StatType) -> int:
        """Get specified stat gain for training at specified facility level."""
        level_stats = self.stat_gain.get(level, {})
        return level_stats.get(stat_type, 0)
    
    def get_stat_gain_at_current_level(self, stat_type: StatType) -> int:
        """Get specified stat gain for training at current facility level."""
        return self.get_stat_gain_at_level(self.level, stat_type)
    
    def get_all_stat_gains_at_level(self, level: int) -> dict[StatType, int]:
        """Get all stat gains for training at specified facility level."""
        return self.stat_gain.get(level, {}).copy()
    
    def get_all_stat_gains_at_current_level(self) -> dict[StatType, int]:
        """Get all stat gains for training at current facility level."""
        return self.get_all_stat_gains_at_level(self.level)
    
    def get_skill_points_gain_at_level(self, level: int) -> int:
        """Get skill points gain for training at specified facility level."""
        return self.skill_points_gain.get(level, 0)
    
    def get_skill_points_gain_at_current_level(self) -> int:
        """Get skill points gain for training at current facility level."""
        return self.get_skill_points_gain_at_level(self.level)
    
    def get_energy_gain_at_level(self, level: int) -> int:
        """Get energy cost/gain for training at specified facility level."""
        return self.energy_gain.get(level, -20)  # Default to -20 energy cost
    
    def get_energy_gain_at_current_level(self) -> int:
        """Get energy cost/gain for training at current facility level."""
        return self.get_energy_gain_at_level(self.level)

@dataclass
class Scenario:
    """Represents a game scenario with facility configurations."""
    name: str
    id: int
    release: date | None
    facilities: dict[FacilityType, Facility]
    
    def get_facility(self, facility_type: FacilityType) -> Facility:
        """Get facility by type."""
        if facility_type not in self.facilities:
            raise ValueError(f"Facility type {facility_type} not found in scenario")
        return self.facilities[facility_type]
    
    def set_all_facility_levels(self, level: int) -> None:
        """Set the same level for all facilities."""
        for facility in self.facilities.values():
            facility.set_level(level)
    
    def get_facility_levels(self) -> dict[FacilityType, int]:
        """Get current levels of all facilities."""
        return {facility_type: facility.level for facility_type, facility in self.facilities.items()}

