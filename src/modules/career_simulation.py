class Mood(Enum):
    # TODO: potentially put in its own file or in a trainee.py module
    awful = -2
    bad = -1
    normal = 0
    good = 1
    great = 2
    
    def __str__(self) -> str:
        return self.name.title()

class SkillType(Enum):
    speed = 27
    acceleration = 31
    recovery = 9
    start_delay = 10
    #TODO: [LOw PRIORITY] Add all effects (see effects:type in skills.json)

class FacilityType(Enum):
    speed = 1
    stamina = 2
    power = 3
    guts = 4
    wit = 5

@dataclass
class Scenario:
    pass

@dataclass
class TurnConfiguration:
    self._fan_count: int
    self._mood: Mood
    self._scenario
    self._card_types # dictionary of CardType(Enum) -> int (number of cards of key type)
    self._skill_types # dictionary of SkillType(Enum) -> int (number of skills of key type)
    self._combined_bond_gauge: int
    self._average_energy: int
    self._combined_faciliy_level: int

@dataclass
class TrainingEffect:
    self._card: Card
    self._turn_config: TurnConfiguration
    
    # TODO: methods that "distills" card's normal an unique effects
  
@dataclass
class TrainingResult:
    self._training_effects: list[TrainingEffect]
    
    # TODO: methods that add/multiply all cards "distilled" effects accordingly
    
    # TODO: interface to query for the actual stat gains
    @property
    def speed(self) -> int: # always positive or 0
        pass

    @property
    def stamina(self) -> int: # always positive or 0
        pass

    @property
    def power(self) -> int: # always positive or 0
        pass
        
    @property
    def guts(self) -> int: # always positive or 0
        pass

    @property
    def wit(self) -> int: # always positive or 0
        pass

    @property
    def skill_points(self) -> int: # always positive or 0
        pass

    @property
    def energy(self) -> int: # can be negative
        pass

class CareerSimulation:
    self._turn_config: TurnConfiguration
    self._turns: list[list[TrainingResult]] # e.g. 100 turns * 5 train_results (1 per facility) = 500 object instances
    
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
