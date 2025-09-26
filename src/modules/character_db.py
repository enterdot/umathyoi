import logging
logger = logging.getLogger(__name__)

from typing import Iterator, Optional
from .character import Character
from .stat_type import StatType
from utils import auto_title_from_instance


class CharacterDatabase:
    """Database for managing characters loaded from Gametora website."""
    
    def __init__(self) -> None:
        """Initialize character database."""
        self.characters: dict[int, Character] = {}
        self._load_characters_from_gametora()
        
        logger.debug(f"{auto_title_from_instance(self)} initialized")
    
    def _load_characters_from_gametora(self) -> None:
        """Load characters data from Gametora website.
        
        Note:
            This is a placeholder implementation. Should be replaced with
            actual web scraping or API calls to Gametora.
        """
        # TODO: Implement actual data loading from Gametora website
        logger.info("Loading characters from Gametora (placeholder)")
        
        # Placeholder: empty characters data
        self.characters = {}
    
    def get_character_by_id(self, character_id: int) -> Optional[Character]:
        """Get character by ID.
        
        Args:
            character_id: Unique character identifier
            
        Returns:
            Character instance, or None if not found
        """
        return self.characters.get(character_id)
    
    def search_characters(self, name_query: str) -> Iterator[Character]:
        """Search characters by name.
        
        Args:
            name_query: Partial name to search for (case insensitive)
            
        Yields:
            Characters matching the search query
        """
        name_lower = name_query.lower()
        for character in self.characters.values():
            if name_lower in character.name.lower():
                yield character
    
    def get_characters_with_stat_bonus(self, stat_type: StatType) -> Iterator[Character]:
        """Get characters that have growth bonus for a specific stat.
        
        Args:
            stat_type: Stat type to filter by
            
        Yields:
            Characters with growth bonus for the specified stat
        """
        for character in self.characters.values():
            if character.has_stat_growth_bonus(stat_type):
                yield character
    
    def get_characters_with_skill(self, skill_id: int) -> Iterator[Character]:
        """Get characters that can learn a specific skill.
        
        Args:
            skill_id: Skill ID to search for
            
        Yields:
            Characters that can learn the specified skill
        """
        for character in self.characters.values():
            if skill_id in character.skills or character.unique_skill == skill_id:
                yield character
    
    def reload_from_cache(self) -> bool:
        """Reload characters data from local cache if available.
        
        Returns:
            True if cache was loaded successfully, False otherwise
        """
        # TODO: Implement cache loading
        logger.debug("Cache loading not yet implemented")
        return False
    
    def save_to_cache(self) -> bool:
        """Save current characters data to local cache.
        
        Returns:
            True if cache was saved successfully, False otherwise
        """
        # TODO: Implement cache saving
        logger.debug("Cache saving not yet implemented")
        return False
    
    @property
    def count(self) -> int:
        """Number of characters in database."""
        return len(self.characters)
    
    def __iter__(self) -> Iterator[Character]:
        """Iterate over all characters in database.
        
        Yields:
            Character instances in the database
        """
        yield from self.characters.values()
