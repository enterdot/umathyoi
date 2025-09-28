from enum import Enum
from dataclasses import dataclass
from .skill import SkillType
from .mood import Mood
from .card import Card, CardType
from .scenario import Scenario, Facility, FacilityType
from .character import StatType, StatGrowth

@dataclass
class TurnConfiguration:
    _fan_count: int
    _mood: Mood
    _scenario: Scenario
    _card_types: dict[CardType, int] # number of cards per each type
    _skill_types: dict[SkillType, int]  # number of skills per each type
    _combined_bond_gauge: int
    _average_energy: int
    _combined_faciliy_level: int
    _stat_growth: StatGrowth

@dataclass
class TrainingEffect:
    _card: Card
    _turn_config: TurnConfiguration
    
    # TODO: methods that "distills" card's normal an unique effects
  
@dataclass
class TrainingResult:
    _training_effects: list[TrainingEffect]
    
    # TODO: methods that add/multiply all cards "distilled" effects accordingly
    
    # TODO: interface to query for the actual stat gains
    def get_stat_gain_by_type(stat_type: StatType) -> int:
        # always 0 or positive
        pass
    
    def get_skill_points_gain() -> int:
        # always 0 or positive
        pass

    def get_energy_gain() -> int:
        # can be negative
        pass

class CareerSimulation:
    _turn_config: TurnConfiguration
    _turns: list[list[TrainingResult]] # e.g. 100 turns * 5 train_results (1 per facility) = 500 object instances
    
    def __init__(self, turns_count: int, turn_config: TurnConfiguration, cards: list[Card]) -> None:
        for i in range(turns_count):
            cards_on_facilities = self._distribute_cards(cards)
            training_result_per_facility = []
            for cards_on_facility in cards_on_facilities:
                training_effects_on_facility = []
                for card_on_facility in cards_on_facility:
                    training_effects_on_facility.append(TrainingEffect(card_on_facility, turn_config))
                training_result_per_facility.append(TrainingResult(training_effects_on_facility))
            self._turns.append(training_result_per_facility)
                    


    def _distribute_cards(self, cards: list[Card]) -> list[list[Card]]:
        pass
    
    # TODO: whatever methods we need to more easily build the violing plots
