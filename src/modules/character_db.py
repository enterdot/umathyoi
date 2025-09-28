import logging
logger = logging.getLogger(__name__)

from typing import Iterator
from .character import Character, StatType
from utils import auto_title_from_instance, ApplicationConstants

class CharacterDatabase:
    """Database for managing characters loaded from Gametora website."""
    
    def __init__(self, characters_file: str = ApplicationConstants.CHARACTERS_JSON) -> None:
        """Initialize character database."""
        self.characters: dict[int, Character] = {}
        self._load_characters_from_file(characters_file)

        logger.debug(f"{auto_title_from_instance(self)} initialized")
    
    def _load_characters_from_file(self, characters_file: str) -> None:
        """Load characters data from JSON file."""
        # TODO: Implement actual data loading, follow pattern of card_db.py and scenario.py
        # Placeholder: empty characters data
        pass
