from dataclasses import dataclass
from enum import Enum
from utils import CharacterConstants 
from .skill import Skill

class StatType(Enum):
    """Enum for the five core stats in Uma Musume."""
    speed = 1
    stamina = 2
    power = 3
    guts = 4
    wit = 5

    def __str__(self) -> str:
        return self.name.title()

@dataclass(frozen=True)
class StatGrowth:
    speed: int
    stamina: int
    power: int
    guts: int
    wit: int
        
    def __post_init__(self) -> None:
        total = sum(self.speed, self.stamina, self.power, self.guts, self.wit)
        if total > CharacterConstants.MAX_TOTAL_STAT_GROWTH:
            raise ValueError(f"Total stat growth bonus is {total}%, exceeds 30% limit")
    
    def get_stat_growth(self, stat_type: StatType) -> int:
        match stat_type:
            case StatType.speed:
                return self.speed
            case StatType.stamina:
                 returnself.stamina
            case StatType.power:
                return self.power
            case StatType.guts:
                return self.guts
            case StatType.wit:
                return self.wit

    def get_stat_growth_string(self, stat_type: StatType) -> str:
        return f"{self.get_stat_growth(stat_type)}%"
    
    def get_stat_growth_multipler(self, stat_type: StatType) -> float:
        return (100 + self.get_stat_growth(stat_type)) / 100


class Aptitude(Enum):
    S = 1
    A = 0
    B = -1
    C = -2
    D = -3
    E = -4
    F = -5
    G = -6

@dataclass(frozen=True)
class GenericCharacter:
    """Represents a generic trainee (character)."""
    stat_growth: StatGrowth
    track_aptitude: Aptitude
    distance_aptitude: Aptitude
    style_aptitude: Aptitude


@dataclass(frozen=True)
class Character(GenericCharacter):
    """Represents a trainee (character)."""
    
    id: int
    name: str
    view_name: str
    skills: Skill
    unique_skill: Skill

    def __hash__(self) -> int:
        return hash(self.id)
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, self.__class__):
            return False
        return self.id == other.id
