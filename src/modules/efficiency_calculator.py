from enum import Enum
from dataclasses import dataclass
from .skill import Skill, SkillType
from .mood import Mood
from .card import Card, CardType, CardEffect, CardUniqueEffect
from .scenario import Scenario, Facility, FacilityType
from .character import GenericCharacter, StatType
from utils import GameplayConstants

@dataclass(frozen=True)
class Turn:
    scenario: Scenario
    facility_levels: dict[FacilityType, int]
    energy: int
    max_energy: int
    fan_count: int
    mood: Mood
    character: GenericCharacter
    cards: list[Card]
    card_levels: dict[Card, int]
    card_bonds: dict[Card, int]
    skills: list[Skill]

    def __post_init__(self) -> None:
        # Distribute cards among facilities
        card_facilities = self._distribute_cards()
        object.__setattr__(self, 'card_facilities', card_facilities)

        # Build training effects
        training_effects = {facility: [] for facility in FacilityType}
        for card in self.cards:
            effect = TrainingEffect(card, self)
            training_effects[effect.facility_type].append(effect)
        object.__setattr__(self, 'training_effects', training_effects)

    def _distribute_cards(self) -> dict[Card, FacilityType]:
        """Distribute cards among facilities using specialty priority mechanic."""
        import random

        card_facilities = {}
        
        for card in self.cards:
            # Get card's specialty priority at current level
            card_level = self.card_levels[card]
            specialty_priority = card.get_effect_at_level(CardEffect.specialty_priority, card_level)
            
            # Calculate total weight for probability denominator
            total_weight = (GameplayConstants.PREFERRED_FACILITY_BASE_WEIGHT * 5) + specialty_priority + GameplayConstants.NON_APPEARANCE_BASE_WEIGHT
            
            # Get preferred facility (None for Pal cards)
            preferred_facility = card.preferred_facility
            
            # Build weights for each outcome
            weights = []
            outcomes = []
            
            for facility in FacilityType:
                weight = GameplayConstants.PREFERRED_FACILITY_BASE_WEIGHT
                if facility == preferred_facility:
                    # Preferred facility gets bonus from specialty_priority
                    weight += specialty_priority
                
                weights.append(weight)
                outcomes.append(facility)
            
            # Add non-appearance as an outcome
            weights.append(GameplayConstants.NON_APPEARANCE_BASE_WEIGHT)
            outcomes.append(None)  # None represents "card doesn't appear"
            
            # Weighted random selection
            chosen_outcome = random.choices(outcomes, weights=weights, k=1)[0]
            
            # Only add to dict if card actually appears
            if chosen_outcome is not None:
                card_facilities[card] = chosen_outcome
        
        return card_facilities

    @property
    def combined_bond_gauge(self) -> int:
        return sum(self.card_bonds.values())

    @property
    def combined_facility_levels(self) -> int:
        return sum(self.facility_levels.values())
    
    @property
    def card_types_in_deck(self) -> int:
        return len({c.type for c in self.cards})

    def get_card_count(self, card_type: CardType | None = None, facility_type: FacilityType | None = None) -> int:
        if facility_type is None:
            # Count across all facilities
            if card_type is None:
                # Count all cards
                return len(self.cards)
            else:
                # Count specific card type across all facilities
                return sum(1 for card in self.cards if card.type == card_type)
        else:
            # Count on specific facility
            if card_type is None:
                # Count all cards on this facility
                return sum(1 for facility in card_facilities.values() if facility == facility_type)
            else:
                # Count specific card type on this facility
                return sum(1 for card, facility in card_facilities.items() if facility == facility_type and card.type == card_type)

    def get_skill_count(self, skill_type: SkillType | None = None) -> int:
        if skill_type is None:
            return len(self.skills)
        return sum(1 for skill in self.skills if skill.type == skill_type)


@dataclass(frozen=True)
class TrainingEffect:
    """The effect on training a card provides based on turn state"""
    card: Card
    turn: Turn

    def __post_init__(self):
        """Pre-build effect handlers and calculate combined normal and unique effects"""
        object.__setattr__(self, '_unique_effect_handlers', self._make_unique_effect_handlers())
        object.__setattr__(self, 'combined_effects', self._calculate_combined_effects())
    
    @property
    def facility_type(self) -> FacilityType:
        return self.turn.card_facilities[self.card]

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
                        vals[2] * (self.turn.card_bonds[self.card] >= vals[0])
                    )
                ],

            CardUniqueEffect.effect_bonus_per_combined_bond:
            # unique_effect_id = 109
            # value = effect_id, value_1 = max_bonus
            # sample card: 30208-nishino-flower
                lambda vals: [
                    (
                        CardEffect(vals[0]),
                        20 + self.turn.combined_bond_gauge // vals[1]
                    )
                ],
            
            CardUniqueEffect.effect_bonus_per_facility_level:
            # unique_effect_id = 111
            # value = effect_id, value_1 = bonus_amount
            # sample card: 30107-maruzensky
                lambda vals: [
                    (
                        CardEffect(vals[0]),
                        self.turn.facility_levels[self.facility_type] * vals[1]
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
                        min(self.turn.energy // vals[1], vals[2])
                    )
                ],
            
            CardUniqueEffect.effect_bonus_on_less_energy:
            # unique_effect_id = 107
            # value = effect_id, value_1 = energy_per_bonus_point, value_2 = energy_floor, value_3 = max_bonus, value_4 = base_bonus
            # sample card: 30094-bamboo-memory
                lambda vals: [
                    (
                        CardEffect(vals[0]),
                        min(vals[3], vals[4] + (self.turn.max_energy - max(self.turn.energy, vals[2])) // vals[1]) * (self.turn.energy <= 100)
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
                lambda vals: [],

            CardUniqueEffect.training_effectiveness_if_min_card_types:
            # unique_effect_id = 103
            # value = min_card_types, value_1 = bonus_amount
            # sample card: 30250-buena-vista
            # Bonus if number of different card types on facility >= threshold
                lambda vals: [
                    (
                        CardEffect.training_effectiveness,
                        vals[1] * (self.turn.card_types_in_deck >= vals[0])
                    )
                ],

            CardUniqueEffect.training_effectiveness_for_fans:
            # unique_effect_id = 104
            # value = fans_per_bonus, value_1 = max_bonus_amount
            # sample card: 30086-narita-top-road
                lambda vals: [
                    (
                        CardEffect.training_effectiveness,
                        min(vals[1], self.turn.fan_count // vals[0])
                    )
                ],

            CardUniqueEffect.training_effectiveness_if_min_bond_and_not_preferred_facility:
            # unique_effect_id = 102
            # value = min_bond, value_1 = bonus_amount
            # sample card: 30083-sakura-bakushin-o
                lambda vals: [
                    (
                        CardEffect.training_effectiveness,
                        vals[1] * (self.turn.card_bonds[self.card] >= vals[0] and not self.card.is_preferred_facility(self.facility_type))
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
                        vals[2] * vals[0] * (self.turn.card_bonds[self.card] >= CardConstants.FRIENDSHIP_BOND_THRESHOLD)
                    )
                ],

            CardUniqueEffect.effect_bonus_per_card_on_facility:
            # unique_effect_id = 110
            # value = effect_id, value_1 = bonus_amount
            # sample card: 30102-el-condor-pasa
                lambda vals: [
                    (
                        CardEffect(vals[0]),
                        (self.turn.get_card_count(facility_type=self.facility_type) - 1) * vals[1]
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
                        min(self.turn.get_skill_count(SkillType(vals[0])), vals[3]) * vals[2]
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
                        vals[2] * self.turn.combined_facility_levels // vals[1]
                    )
                ],

            CardUniqueEffect.stat_or_skill_points_bonus_per_card_based_on_type:
            # unique_effect_id = 120
            # value = skill_point_bonus_per_pal, value_1 = min_bond, value_2 = stat_bonus_per_stat_type, value_3 = max_cards_per_stat
            # sample card: 30187-orfevre
                lambda vals: [
                    # Speed bonus (effect 3)
                    (
                        CardEffect(3), 
                        min(self.turn.get_card_count(card_type=CardType.SPEED), vals[3]) 
                        * vals[2] 
                        * (self.turn.card_bonds[self.card] >= vals[1])
                    ),
                    # Stamina bonus (effect 4)
                    (
                        CardEffect(4), 
                        min(self.turn.get_card_count(card_type=CardType.STAMINA), vals[3]) 
                        * vals[2] 
                        * (self.turn.card_bonds[self.card] >= vals[1])
                    ),
                    # Power bonus (effect 5)
                    (
                        CardEffect(5), 
                        min(self.turn.get_card_count(card_type=CardType.POWER), vals[3]) 
                        * vals[2] 
                        * (self.turn.card_bonds[self.card] >= vals[1])
                    ),
                    # Guts bonus (effect 6)
                    (
                        CardEffect(6), 
                        min(self.turn.get_card_count(card_type=CardType.GUTS), vals[3]) 
                        * vals[2] 
                        * (self.turn.card_bonds[self.card] >= vals[1])
                    ),
                    # Wit bonus (effect 7)
                    (
                        CardEffect(7), 
                        min(self.turn.get_card_count(card_type=CardType.WIT), vals[3]) 
                        * vals[2] 
                        * (self.turn.card_bonds[self.card] >= vals[1])
                    ),
                    # Skill points (effect 30) - no cap on Pal cards
                    (
                        CardEffect(30), 
                        self.turn.get_card_count(card_type=CardType.PAL) 
                        * vals[0] 
                        * (self.turn.card_bonds[self.card] >= vals[1])
                    )
                ],

            # Add unique effects handlers here as they are added to the game
            # See: https://umamusu.wiki/Game:List_of_Support_Cards
        }

    def _calculate_combined_effects(self) -> dict[CardEffect, int]:
        """Flatten unique effects into normal effects"""
        effects = self.card.get_all_effects_at_level(self.turn.card_levels[self.card])

        if self.turn.card_levels[self.card] < self.card.unique_effects_unlock_level:
            # Card unique effects are not unlocked
            return effects
        
        unique_effects = self.card.get_all_unique_effects()
        flattend_effects = {}
        for unique_effect_type, unique_effect_values in unique_effects.items():
            if unique_effect_type.value < CardConstants.COMPLEX_UNIQUE_EFFECTS_ID_THRESHOLD:
                # Unique effect is already equivalent to its normal effect counterpart
                if len(unique_effect_values) != 1:
                    logger.warning(f"Card {card.id} has single value unique effect {unique_effect_type.name()}, but has more than 1 value: {unique_effect_values}")
                mapped_effect_type = CardEffect(unique_effect_type.value)
                flattened_effects[mapped_effect_type] = flattened_effects.get(mapped_effect_type, 0) + unique_effect[0]
            else:
                handler = self._unique_effect_handlers(unique_effect_type)
                if handler:
                    results = handler(unique_effect_values)  # Always a list
                    for effect_type, effect_value in results:
                        flattened_effects[effect_type] = flattened_effects.get(effect_type, 0) + effect_value
        
        # Merge effects and flattened_effects
        combined_effects = effects.copy()
        
        for effect_type, unique_value in flattened_effects.items():
            if effect_type == CardEffect.friendship_effectiveness:
                # Special multiplication rule for friendship training effectiveness
                normal_value = combined_effects.get(effect_type, 0)
                combined = ((GameplayConstants.PERCENTAGE_BASE + normal_value) * (GameplayConstants.PERCENTAGE_BASE + unique_value) / GameplayConstants.PERCENTAGE_BASE) - GameplayConstants.PERCENTAGE_BASE
                combined_effects[effect_type] = int(combined)
            else:
                # Additive rule for all other effects
                combined_effects[effect_type] = combined_effects.get(effect_type, 0) + unique_value
        
        return combined_effects
                
class EfficiencyCalculator:
    """Initialize calculator with deck configuration."""
    
    def __init__(self, deck: Deck, scenario: Scenario, character: Character):
        # Private attributes
        self._deck: Deck = deck
        self._scenario: Scenario = scenario
        self._character: Character = character
        self._fan_count: int = 100000
        self._mood: Mood = Mood.good
        self._energy: int = 70
        self._max_energy: int = 104
        self._facility_levels: dict[FacilityType, int] = {facility: 3 for facility in FacilityType}
        self._card_levels: dict[Card, int] = {card: card.max_level for card in deck.cards}
        self._card_bonds: dict[Card, int] = {card: 80 for card in deck.cards}
        self._skills: list[Skill] = []

        # Number of turns to simulate
        self.turn_count = 1000

        # Events
        self.calculation_started = Event()
        self.calculation_progress = Event()  # Passes (current, total)
        self.calculation_finished = Event()
        
        logger.debug(f"{auto_title_from_instance(self)} initialized")

    # Deck property
    @property
    def deck(self) -> Deck:
        return self._deck
    
    @deck.setter
    def deck(self, value: Deck) -> None:
        self._deck = value
        self.recalculate()

    # Scenario property
    @property
    def scenario(self) -> Scenario:
        return self._scenario
    
    @scenario.setter
    def scenario(self, value: Scenario) -> None:
        self._scenario = value
        self.recalculate()

    # Character property
    @property
    def character(self) -> Character:
        return self._character
    
    @character.setter
    def character(self, value: Character) -> None:
        self._character = value
        self.recalculate()

    # Fan count property
    @property
    def fan_count(self) -> int:
        return self._fan_count
    
    @fan_count.setter
    def fan_count(self, value: int) -> None:
        self._fan_count = value
        self.recalculate()

    # Mood property
    @property
    def mood(self) -> Mood:
        return self._mood
    
    @mood.setter
    def mood(self, value: Mood) -> None:
        self._mood = value
        self.recalculate()

    # Energy property
    @property
    def energy(self) -> int:
        return self._energy
    
    @energy.setter
    def energy(self, value: int) -> None:
        self._energy = value
        self.recalculate()

    # Max energy property
    @property
    def max_energy(self) -> int:
        return self._max_energy
    
    @max_energy.setter
    def max_energy(self, value: int) -> None:
        self._max_energy = value
        self.recalculate()

    # Facility levels property
    @property
    def facility_levels(self) -> dict[FacilityType, int]:
        return self._facility_levels
    
    @facility_levels.setter
    def facility_levels(self, value: dict[FacilityType, int]) -> None:
        self._facility_levels = value
        self.recalculate()

    # Card levels property
    @property
    def card_levels(self) -> dict[Card, int]:
        return self._card_levels
    
    @card_levels.setter
    def card_levels(self, value: dict[Card, int]) -> None:
        self._card_levels = value
        self.recalculate()

    # Card bonds property
    @property
    def card_bonds(self) -> dict[Card, int]:
        return self._card_bonds
    
    @card_bonds.setter
    def card_bonds(self, value: dict[Card, int]) -> None:
        self._card_bonds = value
        self.recalculate()

    # Skills property
    @property
    def skills(self) -> list[Skill]:
        return self._skills
    
    @skills.setter
    def skills(self, value: list[Skill]) -> None:
        self._skills = value
        self.recalculate()

    @debounce(wait_ms=350)
    def recalculate(self) -> None:
        """Run the Monte Carlo simulation."""
        
        self.calculation_started.trigger(self)
        
        self._simulated_turns: list[Turn] = []
        
        for i in range(self.turn_count):
            # Create Turn instance
            turn = Turn(
                scenario=self.scenario,
                facility_levels=self.facility_levels.copy(),
                energy=self.energy,
                max_energy=self.max_energy,
                fan_count=self.fan_count,
                mood=self.mood,
                character=self.character,
                cards=list(self.deck.cards),
                card_levels=self.card_levels.copy(),
                card_bonds=self.card_bonds.copy(),
                skills=self.skills.copy()
            )
            
            self._simulated_turns.append(turn)
            
            # Report progress every 1%
            if i % (self.turn_count // 100) == 0:
                self.calculation_progress.trigger(self, current=i, total=self.turn_count)
        
        
        # Aggregating results of all turns
        for turn in self._simulated_turns:

            for training_effect in turn.training_effects:

                for combined_effect in training_effect.combined_effects:

                    # friendship_multiplier for cards which type match the facility
                    # (1 + friendship_effectiveness_1/100) * (1 + friendship_effectiveness_2/100) * ...

                    # mood_multiplier
                    # 1 + ( turn_mood/100 * (1 + mood_effect_increase_1/100 + mood_effect_increase_2/100 + ...))

                    # training_multiplier
                    # 1 + training_effectiveness_1/100 + training_effectiveness_2/100 + ...

                    # speed_stat_total_bonus (for each facility that gives speed)
                    # speed_stat_bonus_1 + speed_stat_bonus_2 + ...
                    
                    # similar for stamina, power, guts, wit and skill_points

                    # support_multiplier
                    # 1 + card_count_on_facility * 0.05
                    
                    # speed_growth_multiplier
                    # 1 + character_speed_growth/100

                    # similar for stamina, power, guts and wit growth

                    # final_speed_gain
                    # (facility_speed_base + speed_stat_base) * friendship_multiplier * mood_multiplier * training_multiplier * support_multiplier * speed_growth_multiplier

                    # similar for stamina, power, guts and wit

                    # final_skill_points_gain
                    # facility_skill_points_base + skill_points_total_bonus
                    
