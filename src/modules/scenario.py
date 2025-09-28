from enum import Enum
from dataclasses import dataclass
from .character import StatType

class FacilityType(Enum):
    speed = 1
    stamina = 2
    power = 3
    guts = 4
    wit = 5

@dataclass
class Facility:
    _type: FacilityType
    _level: int
    _stat_gain: dict[int, dict[StatType, int]] # level -> [stat_type, value]
    _skill_points_gain: dict[int, int] # level -> value
    _energy_gain: dict[int, int] # level -> value

    #methods to get all the values by facility level or its current level
    #method to also set the level

@dataclass
class Scenario:

    _facilities: list[Facility] # one per FacilityType

    #use the scenarios.json to initialize
    pass
