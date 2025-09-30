from enum import Enum
from dataclasses import dataclass
from .skill import Skill, SkillType
from .mood import Mood
from .card import Card, CardType, CardEffect, CardUniqueEffect
from .scenario import Scenario, Facility, FacilityType
from .character import StatType, StatGrowth

@dataclass
class TurnConfiguration:
    fan_count: int
    mood: Mood
    scenario: Scenario
    cards: list[Card]
    card_levels: dict[int, int] # card_id -> card_level
    bond_gauges: dict[int, int] # card_id -> bond_gauge
    skills: list[Skill]
    energy: int
    max_energy: int
    facility_levels: dict[FacilityType, int]
    facility_cards: dict[FacilityType, list[Card]]
    stat_growth: StatGrowth
    
    @property
    def combined_bond_gauge(self) -> int:
        return sum(bond_gauges.values())

    @property
    def combined_facility_levels(self) -> int:
        return sum(self.facility_levels.values())
    
    @property
    def card_types_in_deck(self) -> int:
        return len({c.type for c in cards})

    def get_card_count(self, card_type: CardType | None = None, facility_type: FacilityType | None = None) -> int:
        if facility_type is None:
            # Count across all facilities
            if card_type is None:
                # Count all cards
                return sum(len(cards) for cards in self.facility_cards.values())
            else:
                # Count specific card type across all facilities
                return sum(
                    len([c for c in self.facility_cards[facility] if c.type == card_type])
                    for facility in FacilityType
                )
        else:
            # Count on specific facility
            if card_type is None:
                # Count all cards on this facility
                return len(self.facility_cards[facility_type])
            else:
                # Count specific card type on this facility
                return len([c for c in self.facility_cards[facility_type] if c.type == card_type])

    def get_skill_count(self, skill_type: SkillType | None = None) -> int:
        if skill_type is None:
            return len(self.skills)
        return sum(1 for skill in self.skills if skill.type == skill_type)


@dataclass
class TrainingEffect:
    """The effect on training a card provides based on turn state"""
    card: Card
    facility_type: FacilityType # facility the card was assigned to
    turn_config: TurnConfiguration

    def __post_init__(self):
        """Pre-build effect handlers once"""
        self._unique_effect_handlers = self._make_unique_effect_handlers()

    def _make_unique_effect_handlers(self):
        """Creates a dictionary of effect handlers as closures. Each closure captures self and can access instance state."""
        return {

            CardUniqueEffect.effect_bonus_if_min_bond:
            # unique_effect_id = 101
            # value=min_bond, value_1=effect_id, value_2=bonus_amount
            # sample card: 30189-kitasan-black
                lambda vals: [
                    (
                        CardEffect(vals[1]),
                        vals[2] * (self.turn_config.bond_gauges[self.card.id] >= vals[0])
                    )
                ],

            CardUniqueEffect.effect_bonus_per_combined_bond:
            # unique_effect_id = 109
            # value = effect_id, value_1 = max_bonus
            # sample card: 30208-nishino-flower
                lambda vals: [
                    (
                        CardEffect(vals[0]),
                        20 + self.turn_config.combined_bond_gauge // vals[1]
                    )
                ],
            
            CardUniqueEffect.effect_bonus_per_facility_level:
            # unique_effect_id = 111
            # value = effect_id, value_1 = bonus_amount
            # sample card: 30107-maruzensky
                lambda vals: [
                    (
                        CardEffect(vals[0]),
                        self.turn_config.facility_levels[self.facility_type] * vals[1]
                    )
                ],
            
            CardUniqueEffect.effect_bonus_if_friendship_training:
            # unique_effect_id = 113
            # value = effect_id, value_1 = bonus_amount
            # sample card: 30256-tamamo-cross
                lambda vals: [
                    (
                        CardEffect(vals[0]),
                        vals[1] * self.card.is_preferred_facility(self.facility_type)
                    )
                ],
            
            CardUniqueEffect.effect_bonus_on_more_energy:
            # unique_effect_id = 114
            # value = effect_id, value_1 = energy_per_bonus_point, value_2 = max_bonus
            # sample card: 30115-mejiro-palmer
                lambda vals: [
                    (
                        CardEffect(vals[0]),
                        min(self.turn_config.energy // vals[1], vals[2])
                    )
                ],
            
            CardUniqueEffect.effect_bonus_on_less_energy:
            # unique_effect_id = 107
            # value = effect_id, value_1 = energy_per_bonus_point, value_2 = energy_floor, value_3 = max_bonus, value_4 = base_bonus
            # sample card: 30094-bamboo-memory
                lambda vals: [
                    (
                        CardEffect(vals[0]),
                        min(vals[3], vals[4] + (self.turn_config.max_energy - max(self.turn_config.energy, vals[2])) // vals[1]) * (self.turn_config.energy <= 100)
                    )
                ],

            CardUniqueEffect.effect_bonus_on_more_max_energy:
            # unique_effect_id = 108
            # value=effect_id, value_1=?, value_2=?, value_3=min_bonus?, value_4=max_bonus?
            # TODO: Formula unclear - needs testing with actual card
            # Temporarily returns max_bonus until proper implementation can be verified
            # sample card: 30095-seeking-the-pearl
                lambda vals: (
                    logger.warning(f"Card {self.card.id} uses effect_bonus_on_more_max_energy (108) which has an unverified implementation"),
                    [
                        (
                            CardEffect(vals[0]),
                            vals[4]  # Always return max_bonus (20) until formula is confirmed
                        )
                    ]
                )[1],

            CardUniqueEffect.extra_appearance_if_min_bond:
            # unique_effect_id = 118
            # value = extra_appearances, value_1 = min_bond
            # sample card: 30160-mei-satake
            # Not used in simulator - return empty list
                lambda vals: [],

            CardUniqueEffect.cards_appear_more_if_min_bond:
            # unique_effect_id = 119
            # value = ?, value_1 = ?, value_2 = min_bond
            # sample card: 30188-ryoka-tsurugi
            # Not used in simulator - return empty list
                lambda vals: [],

            CardUniqueEffect.all_cards_gain_bond_bonus_per_training:
            # unique_effect_id = 121
            # value = bonus_amount, value_1 = bonus_amount_if_card_on_facility
            # sample card: 30207-yayoi-akikawa
            # Affects other cards - not tracked in simulator
                lambda vals: [],

            CardUniqueEffect.cards_gain_effect_bonus_next_turn_after_trained_with:
            # unique_effect_id = 122
            # value = effect_id, value_1 = bonus_amount
            # sample card: 30257-tucker-bryne
            # Requires turn-by-turn tracking - too complex for simulator
                lambda vals: (
                    logger.warning(f"Card {self.card.id} has next-turn effect {CardUniqueEffect(122).name} which is not supported in simulator"),
                    []
                )[1],

            CardUniqueEffect.training_effectiveness_if_min_card_types:
            # unique_effect_id = 103
            # value = min_card_types, value_1 = bonus_amount
            # sample card: 30250-buena-vista
            # Bonus if number of different card types on facility >= threshold
                lambda vals: [
                    (
                        CardEffect.training_effectiveness,
                        vals[1] * (self.turn_config.card_types_in_deck >= vals[0])
                    )
                ],

            CardUniqueEffect.training_effectiveness_for_fans:
            # unique_effect_id = 104
            # value = fans_per_bonus, value_1 = max_bonus_amount
            # sample card: 30086-narita-top-road
                lambda vals: [
                    (
                        CardEffect.training_effectiveness,
                        min(vals[1], self.turn_config.fan_count // vals[0])
                    )
                ],

            CardUniqueEffect.training_effectiveness_if_min_bond_and_not_preferred_facility:
            # unique_effect_id = 102
            # value = min_bond, value_1 = bonus_amount
            # sample card: 30083-sakura-bakushin-o
                lambda vals: [
                    (
                        CardEffect.training_effectiveness,
                        vals[1] * (self.turn_config.bond_gauges[self.card.id] >= vals[0] and not self.card.is_preferred_facility(self.facility_type))
                    )
                ],

            CardUniqueEffect.effect_bonus_per_friendship_trainings:
            # unique_effect_id = 106
            # value=max_times, value_1 = effect_id, value_2 = bonus_amount
            # sample card: 30112-twin-turbo
            # Bonus per friendship trainings done (assumes max_times if bond is enough to trigger them)
                lambda vals: [
                    (
                        CardEffect(vals[1]),
                        vals[2] * vals[0] * (self.turn_config.bond_gauges[self.card.id] >= CardConstants.FRIENDSHIP_BOND_THRESHOLD)
                    )
                ],

            CardUniqueEffect.effect_bonus_per_card_on_facility:
            # unique_effect_id = 110
            # value = effect_id, value_1 = bonus_amount
            # sample card: 30102-el-condor-pasa
                lambda vals: [
                    (
                        CardEffect(vals[0]),
                        (self.turn_config.get_card_count(facility_type=self.facility_type) - 1) * vals[1]
                    )
                ],

            CardUniqueEffect.chance_for_no_failure:
            # unique_effect_id = 112
            # value = chance
            # sample card: 30108-nakayama-festa
            # Not used in simulator - return empty list
                lambda vals: [],

            CardUniqueEffect.all_cards_gain_effect_bonus:
            # unique_effect_id = 115
            # value = effect_id, value_1 = bonus_amount
            # sample card: 30146-oguri-cap
            # Affects other cards - not tracked in simulator
                lambda vals: [],

            CardUniqueEffect.effect_bonus_per_skill_type:
            # unique_effect_id = 116
            # value = skill_type, value_1 = effect_id, value_2 = bonus_amount, value_3 = max_skills_count
            # sample card: 30134-mejiro-ramonu
                lambda vals: [
                    (
                        CardEffect(vals[1]),
                        min(self.turn_config.get_skill_count(SkillType(vals[0])), vals[3]) * vals[2]
                    )
                ],

            CardUniqueEffect.stat_up_per_card_based_on_type:
            # unique_effect_id = 105
            # value=stat_amount_per_matching_stat_card, value_1=all_stats_amount_per_non_stat_card
            # sample card: 30090-symboli-rudolf
            # Provides initial stats at start of run based on deck composition
            # Not tracked in training simulator - affects only starting stats
                lambda vals: [],

            CardUniqueEffect.effect_bonus_per_combined_facility_level:
            # unique_effect_id = 117
            # value = effect_id, value_1 = target_combined_level, value_2 = max_bonus
            # sample card: 30148-daiwa-scarlet
                lambda vals: [
                    (
                        CardEffect(vals[0]),
                        vals[2] * self.turn_config.combined_facility_levels // vals[1]
                    )
                ],

            CardUniqueEffect.stat_or_skill_points_bonus_per_card_based_on_type:
            # unique_effect_id = 120
            # value = skill_point_bonus_per_pal, value_1 = min_bond, value_2 = stat_bonus_per_stat_type, value_3 = max_cards_per_stat
            # When bond >= min_bond: +stat_bonus per stat-type card (capped per stat), +skill_points per Pal
            # sample card: 30187-orfevre
                lambda vals: [
                    # Speed bonus (effect 3)
                    (
                        CardEffect(3), 
                        min(self.turn_config.get_card_count(card_type=CardType.SPEED), vals[3]) 
                        * vals[2] 
                        * (self.turn_config.bond_gauges[self.card.id] >= vals[1])
                    ),
                    # Stamina bonus (effect 4)
                    (
                        CardEffect(4), 
                        min(self.turn_config.get_card_count(card_type=CardType.STAMINA), vals[3]) 
                        * vals[2] 
                        * (self.turn_config.bond_gauges[self.card.id] >= vals[1])
                    ),
                    # Power bonus (effect 5)
                    (
                        CardEffect(5), 
                        min(self.turn_config.get_card_count(card_type=CardType.POWER), vals[3]) 
                        * vals[2] 
                        * (self.turn_config.bond_gauges[self.card.id] >= vals[1])
                    ),
                    # Guts bonus (effect 6)
                    (
                        CardEffect(6), 
                        min(self.turn_config.get_card_count(card_type=CardType.GUTS), vals[3]) 
                        * vals[2] 
                        * (self.turn_config.bond_gauges[self.card.id] >= vals[1])
                    ),
                    # Wit bonus (effect 7)
                    (
                        CardEffect(7), 
                        min(self.turn_config.get_card_count(card_type=CardType.WIT), vals[3]) 
                        * vals[2] 
                        * (self.turn_config.bond_gauges[self.card.id] >= vals[1])
                    ),
                    # Skill points (effect 30) - no cap on Pal cards
                    (
                        CardEffect(30), 
                        self.turn_config.get_card_count(card_type=CardType.PAL) 
                        * vals[0] 
                        * (self.turn_config.bond_gauges[self.card.id] >= vals[1])
                    )
                ],

            # Add unique effects handlers here as they are added to the game
            # See: https://umamusu.wiki/Game:List_of_Support_Cards
        }

    @property
    def effects(self) -> dict[CardEffect, int]:
        """Flatten unique effects into normal effects"""
        effects = self.card.get_all_effects_at_level(self.turn_config.card_levels[self.card.id])

        if self.turn_config.card_levels[self.card.id] < self.card.unique_effects_unlock_level:
            # Card unique effects are not unlocked
            return effects
        
        unique_effects = self.card.get_all_unique_effects()
        flattend_effects = {}
        for unique_effect_type, unique_effect_values in unique_effects:
            if unique_effect_type.value() < CardConstants.COMPLEX_UNIQUE_EFFECTS_ID_THRESHOLD:
                # Unique effect is already equivalent to its normal effect counterpart
                if len(unique_effect_values) != 1:
                    logger.warning(f"Card {card.id} has single value unique effect {unique_effect_type.name()}, but has more than 1 value: {unique_effect_values}")
                mapped_effect_type = CardEffect(unique_effect_type.value())
                flattened_effects[mapped_effect_type] = flattened_effects.get(mapped_effect_type, 0) + unique_effect[0]
            else:
                handler = self._unique_effect_handlers(unique_effect_type)
                if handler:
                    results = handler(unique_effect_values)  # Always a list
                    for effect_type, effect_value in results:
                        flattened_effects[effect_type] = flattened_effects.get(effect_type, 0) + effect_value
        
        # TODO: Merge effects and flattened_effects with appropriate logic
                

@dataclass
class TrainingResult:
    facility_type: FacilityType
    training_effects: list[TrainingEffect]
    turn_config: TurnConfiguration
    
    # TODO: methods that combine the effects of all cards
    
    # TODO: interface to query for the actual stat gains
    def get_stat_gain_by_type(self, stat_type: StatType) -> int:
        # always 0 or positive
        pass
    
    def get_skill_points_gain(self) -> int:
        # always 0 or positive
        pass

    def get_energy_gain(self) -> int:
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
