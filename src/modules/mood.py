from enum import Enum

class Mood(Enum):
    awful = -2
    bad = -1
    normal = 0
    good = 1
    great = 2

    @property
    def multiplier(self) -> float:
        """Get the mood multiplier for training effectiveness."""
        mood_multipliers = {
            Mood.awful: 0.8,    # -20%
            Mood.bad: 0.9,      # -10%
            Mood.normal: 1.0,   #  0%
            Mood.good: 1.1,     # +10%
            Mood.great: 1.2,    # +20%
        }
        return mood_multipliers[self]
    
    def __str__(self) -> str:
        return self.name.title()
