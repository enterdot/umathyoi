import logging
logger = logging.getLogger(__name__)

from enum import Enum
from dataclasses import dataclass


class SkillType(Enum):
    speed = 27
    acceleration = 31
    recovery = 9
    start_delay = 10
    # TODO: [LOw PRIORITY] Add all effects (see effects:type in skills.json)

    def __str__(self) -> str:
        return self.name.title().replace("_", " ")


@dataclass(frozen=True)
class Skill:
    """Represents a skill that can be learned by characters or granted by cards"""
    id: int
    name: str
    icon_id: int
