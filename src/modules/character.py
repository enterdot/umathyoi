from dataclasses import dataclass
from enum import Enum

class StatType(Enum):
    """Enum for the five core stats in Uma Musume."""
    speed = 1
    stamina = 2
    power = 3
    guts = 4
    wit = 5

    def __str__(self) -> str:
        return self.name.title()

@dataclass
class StatGrowth:
    _speed: int
    _stamina: int
    _power: int
    _guts: int
    _wit: int
        
    def __post_init__(self) -> None:
        self._assert_total_limit()
    
    def _assert_total_limit(self) -> None:
        total = sum(self._speed, self._stamina, self._power, self._guts, self._wit)
        if total > 30: # TODO: add constant
            raise RuntimeError(f"A trainee total stat growth bonus cannot be more than 30%")

    def set_stat_growth(self, stat_type: StatType, value: int) -> None:
        match stat_type:
            case StatType.speed:
                self._speed = value
            case StatType.stamina:
                self._stamina = value
            case StatType.power:
                self._power = value
            case StatType.guts:
                self._guts = value
            case StatType.wit:
                self._wit = value
        self._assert_total_limit()
    
    def get_stat_growth(self, stat_type: StatType) -> None:
        match stat_type:
            case StatType.speed:
                return self._speed
            case StatType.stamina:
                 returnself._stamina
            case StatType.power:
                return self._power
            case StatType.guts:
                return self._guts
            case StatType.wit:
                return self._wit

    def get_stat_growth_tag(self, stat_type: StatType) -> str:
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

@dataclass
class GenericCharacter:
    _stat_growth: StatGrowth
    _track_aptitude: Aptitude
    _distance_aptitude: Aptitude
    _style_aptitude: Aptitude


@dataclass
class Character(GenericCharacter):
    """Represents a trainee (character) in Uma Musume."""
    
    _id: int
    _name: str
    _view_name: str
    
    # TODO: expand to include fields from Gametora JSON:
    # unique_skill
    # skills
    # rarity: int = 1
    # cv: str = ""  # voice actor
    # birthday: str = ""
    # height: int = 0
    # weight: int = 0
    # three_sizes: str = ""
    # shoe_size: float = 0.0
    # preferred_distance: list[str] = None
    # preferred_surface: list[str] = None
    # preferred_strategy: list[str] = None

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.id}, name='{self.name}')"
