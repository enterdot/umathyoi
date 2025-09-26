from dataclasses import dataclass
from typing import Optional
from .stat_type import StatType


@dataclass
class Character:
    """Represents a character (trainee) in Uma Musume."""
    
    id: int
    name: str
    description: str = ""
    stat_growth: list[tuple[StatType, int]] | None = None
    unique_skill: Optional[int] = None
    skills: list[int] | None = None
    
    # Future expansion fields from Gametora JSON:
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
    
    def __post_init__(self) -> None:
        """Initialize lists if None."""
        if self.stat_growth is None:
            self.stat_growth = []
        if self.skills is None:
            self.skills = []
    
    def get_stat_growth_bonus(self, stat_type: StatType) -> int:
        """Get growth bonus percentage for a specific stat.
        
        Args:
            stat_type: Stat type to get bonus for
            
        Returns:
            Growth bonus percentage (e.g., 20 for 20% bonus)
        """
        for stat, bonus in self.stat_growth:
            if stat == stat_type:
                return bonus
        return 0
    
    def has_stat_growth_bonus(self, stat_type: StatType) -> bool:
        """Check if character has growth bonus for a stat.
        
        Args:
            stat_type: Stat type to check
            
        Returns:
            True if character has bonus for this stat
        """
        return self.get_stat_growth_bonus(stat_type) > 0
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.id}, name='{self.name}')"
