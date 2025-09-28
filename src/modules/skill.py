from enum import Enum
from dataclasses import dataclass

class SkillType(Enum):
    speed = 27
    acceleration = 31
    recovery = 9
    start_delay = 10
    #TODO: [LOw PRIORITY] Add all effects (see effects:type in skills.json)


@dataclass
class Skill:
    """Represents a skill that can be learned by characters."""
    
    id: int
    name: str
    
    # Future expansion fields (commented out for now):
    # description: str = ""
    # skill_type: SkillType = SkillType.UNKNOWN
    # effects: dict[str, Any] = None
    # cost: int = 0
    # requirements: list[str] = None
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.id}, name='{self.name}')"
