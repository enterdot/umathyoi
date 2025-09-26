from dataclasses import dataclass


@dataclass
class CardTrainingEffects:
    """Dataclass containing all training effects a card provides."""
    
    mood_effect: int = 0
    friendship_bonus: int = 0
    training_effectiveness: int = 0
    specialty_priority: int = 0
    speed_bonus: int = 0
    stamina_bonus: int = 0
    power_bonus: int = 0
    guts_bonus: int = 0
    wit_bonus: int = 0
    skills: list[int] | None = None
    hint_frequency: int = 0
    hint_levels: int = 0
    
    def __post_init__(self) -> None:
        """Initialize skills list if None."""
        if self.skills is None:
            self.skills = []
