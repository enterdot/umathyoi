import logging
logger = logging.getLogger(__name__)

from enum import Enum
from dataclasses import dataclass
from typing import Iterator
from functools import lru_cache

from utils import CardConstants

class Rarity(Enum):
    R = 1
    SR = 2
    SSR = 3

    def __str__(self) -> str:
        return self.name


class CardType(Enum):
    speed = 1
    stamina = 2
    power = 3
    guts = 4
    wit = 5
    pal = 6

    def __str__(self) -> str:
        return self.name.title()

class CardEffect(Enum):
    friendship_effectiveness = 1
    mood_effect_increase = 2
    speed_stat_bonus = 3
    stamina_stat_bonus = 4
    power_stat_bonus = 5
    guts_stat_bonus = 6
    wit_stat_bonus = 7
    training_effectiveness = 8
    speed_stat_up = 9
    stamina_stat_up = 10
    power_stat_up = 11
    guts_stat_up = 12
    wit_stat_up = 13
    friendship_gauge_up = 14
    race_stat_gain_increase = 15
    race_fan_gain_increase = 16
    skill_hint_levels = 17
    skill_hint_frequency = 18
    specialty_priority = 19
    event_recovery_increase = 25
    event_effectiveness = 26
    failure_protection =27
    energy_cost_reduction = 28
    skill_points_bonus = 30
    wit_friendship_recovery_bonus = 31
    skill_points_up = 32

class CardUniqueEffect(Enum):
    friendship_effectiveness = 1
    mood_effect_increase = 2
    speed_stat_bonus = 3
    stamina_stat_bonus = 4
    power_stat_bonus = 5
    guts_stat_bonus = 6
    wit_stat_bonus = 7
    training_effectiveness = 8
    speed_stat_up = 9
    stamina_stat_up = 10
    power_stat_up = 11
    guts_stat_up = 12
    wit_stat_up = 13
    friendship_gauge_up = 14
    race_stat_gain_increase = 15
    skill_hint_frequency = 18
    specialty_priority = 19
    failure_protection =27
    energy_cost_reduction = 28
    skill_points_bonus = 30
    effect_bonus_if_min_bond = 101                                          # value=min_bond, value_1=effect_id, value_2=amount [30189-kitasan-black]
    training_effectiveness_if_min_bond_and_not_preferred_facility = 102     # value=min_bond, value_1=amount [30083-sakura-bakushin-o]
    training_effectiveness_if_min_card_types = 103                          # value=min_card_types, value_1=amount [30250-buena-vista]
    training_effectiveness_for_fans = 104                                   # value=fans, value_1=max_amount [30086-narita-top-road]
    stat_up_per_card_based_on_type = 105                                    # value=type_amount_per_stat_type, value_1=all_amount_per_non_stat_type [30090-symboli-rudolf]
    effect_bonus_per_friendship_trainings = 106                             # value=max_times, value_1=unique_id, value_2=amount [30112-twin-turbo]
    effect_bonus_on_less_energy = 107                                       # value=effect_id, value_1=max_low_energy, value_2=min_low_energy, value_3=max_amount, value_4=min_amount  [30094-bamboo-memory]
    effect_bonus_on_more_max_energy = 108                                   # TODO: unclear, ignore and print warning when used - value=effect_id, value_1=, value_2=, value_3=, value_4= [30095-seeking-the-pearl] 
    effect_bonus_per_combined_bond = 109                                    # value=effect_id, value_1=max_bonus [30208-nishino-flower]
    effect_bonus_per_card_on_facility = 110                                 # value=effect_id, value_1=amount [30102-el-condor-pasa]
    effect_bonus_per_facility_level = 111                                   # value=effect_id, value_1=amount [30107-maruzensky]
    chance_for_no_failure = 112                                             # value=chance [30108-nakayama-festa]
    effect_bonus_if_friendship_training = 113                               # value=effect_id, value_1=amount [30256-tamamo-cross]
    effect_bonus_on_more_energy = 114                                       # value=effect_id, value_1=min_value, value_2=max_value [30115-mejiro-palmer]
    all_cards_gain_effect_bonus = 115                                       # value=effect_id, value_1=amount [30146-oguri-cap]
    effect_bonus_per_skill_type = 116                                       # value=skill_type, value_1=effect_id, value_2=amount, value_3=max_skills [30134-mejiro-ramonu]
    effect_bonus_per_combined_facility_level = 117                          # value=effect_id, value_1=max_combined_level, value_2=max_amount [30148-daiwa-scarlet]
    extra_appearance_if_min_bond = 118                                      # value=extra_appearances, value_1=min_bond [30160-mei-satake]
    cards_appear_more_if_min_bond = 119                                     # TODO: unclear, ignore and print warning when used - value=, value_1=, value_2=min_bond [30188-ryoka-tsurugi]
    stat_or_skill_points_bonus_per_card_based_on_type = 120                 # value=skill_point_bonus_per_non_stat_type, value_1=min_bond, value_2=stat_bonus_per_stat_type, value_3=max_stat_bonus [30187-orfevre]
    all_cards_gain_bond_bonus_per_training = 121                            # value=amount, value_1=amount_if_card_is_on_facility [30207-yayoi-akikawa]
    cards_gain_effect_bonus_next_turn_after_trained_with = 122              # value=effect_id, value_1=amount [30257-tucker-bryne]

@dataclass
class Card:
    id: int
    name: str
    view_name: str
    rarity: Rarity
    type: CardType
    effects: list[list[int]] # [type, value_at_level_1, value_at_level_5, value_at_level_10, ...]
    unique_effects: list[list[int]] # [[type, value1], [type, value1, value2]]
    unique_effects_unlock_level: int # unique effects unlock at this level
    
    @property
    def min_level(self) -> int:
        return CardConstants.MIN_LEVEL

    @property
    def max_level(self) -> int:
        if self.rarity == Rarity.R:
            return CardConstants.R_MAX_LEVEL
        elif self.rarity == Rarity.SR:
            return CardConstants.SR_MAX_LEVEL
        elif self.rarity == Rarity.SSR:
            return CardConstants.SSR_MAX_LEVEL
        else:
            raise RuntimeError(f"Invalid state for {self}, {rarity=}")

    @lru_cache(maxsize=256)  # Cache up to 256 (effect_type, level) combinations
    def _interpolate_effect_value(self, effect_type: CardEffect, level: int) -> int:
        """
        Calculate effect value at specific level using interpolation between milestones.
        
        Args:
            effect_type: effect type
            level: card level
            
        Returns:
            Effect value at the specified level
            
        Note:
            Uses LRU cache for performance since the same levels are queried repeatedly.
            The cache key is (effect_type, level) so each effect type is cached separately.
        """

        if not self.min_level <= level <= self.max_level:
            logger.warning(f"{level=} is out of range for card {self.id}")
            return 0
        
        # Find the effects array for this effect type
        effect = None
        for effects_row in self.effects:
            if len(effects_row) > 0 and effects_row[0] == effect_type.value:
                effect = effects_row
                break
        
        # Valid effect should have values for all milestone levels plus the effect type ID
        if not effect or len(effect) < len(CardConstants.MILESTONE_LEVELS) + 1:
            logger.debug(f"Card {self.id} does not have effect type {effect_type} ({effect_type.name})")
            return 0

        # Find milestone values
        milestones = []
        for i, target_level in enumerate(CardConstants.MILESTONE_LEVELS):
            array_index = i + 1  # +1 because index 0 is effect_type
            if array_index < len(effect):
                value = effect[array_index]
                if value != -1:  # -1 means no milestone at this level
                    milestones.append((target_level, value))

        if not milestones:
            logger.warning(f"Card {self.id} has no valid milestone for effect type {effect_type} ({effect_type.name})")
            return 0
        
        # If level matches a milestone exactly, return that value
        for milestone_level, value in milestones:
            if level == milestone_level:
                return value
        
        # Find the two milestones to interpolate between
        lower_milestone = None
        upper_milestone = None
        
        for milestone_level, value in milestones:
            if milestone_level <= level:
                lower_milestone = (milestone_level, value)
            elif milestone_level > level and upper_milestone is None:
                upper_milestone = (milestone_level, value)
                break
        
        # Handle edge cases
        if lower_milestone is None:
            # Level is below first milestone, return first milestone value
            return milestones[0][1]
        
        if upper_milestone is None:
            # Level is above last milestone, return last milestone value
            return lower_milestone[1]
        
        # Linear interpolation between the two milestones
        lower_level, lower_value = lower_milestone
        upper_level, upper_value = upper_milestone
        
        # Calculate interpolation progress (0.0 to 1.0)
        progress = (level - lower_level) / (upper_level - lower_level)
        
        # Interpolate and round to nearest integer
        interpolated_value = lower_value + (upper_value - lower_value) * progress
        return round(interpolated_value)


    def get_level_at_limit_break(self, limit_break: int) -> int:
        """
        Get maximum level at the specified limit break.
        """        
        if not CardConstants.MIN_LIMIT_BREAK <= limit_break <= CardConstants.MAX_LIMIT_BREAK:
            raise RuntimeError(f"{limit_break=} is not in valid range [{CardConstants.MIN_LIMIT_BREAK}, {CardConstants.MAX_LIMIT_BREAK}]")

        if rarity == Rarity.R:
            base_level = CardConstants.R_MAX_LEVEL_AT_MIN_LIMIT_BREAK
        elif rarity == Rarity.SR:
            base_level = CardConstants.SR_MAX_LEVEL_AT_MIN_LIMIT_BREAK
        elif rarity == Rarity.SSR:
            base_level = CardConstants.SSR_MAX_LEVEL_AT_MIN_LIMIT_BREAK
        else:
            raise RuntimeError(f"Invalid state for {self}, {rarity=}")

        return base_level + CardConstants.LEVELS_PER_LIMIT_BREAK * limit_break

    def get_effect_at_level(self, effect: CardEffect, level: int) -> int:
        """Get effect value at specified level."""
        return self._interpolate_effect_value(effect, level)

    def get_effect_at_limit_break(self, effect: CardEffect, limit_break: int) -> int:
         """Get effect value at specified limit break."""
         level = self.get_level_at_limit_break(limit_break)
         return self.get_effect_at_level(effect, level)

    def get_effect_at_min_level(self, effect: CardEffect) -> int:
        """Get effect value at minimum level."""
        return self._interpolate_effect_value(effect, self.min_level)

    def get_effect_at_max_level(self, effect: CardEffect) -> int:
        """Get effect value at maximum level."""
        return self._interpolate_effect_value(effect, self.max_level)

    def get_effect_at_min_limit_break(self, effect: CardEffect) -> int:
        """Get effect value at maximum level for minimum limit break."""
        return self.get_effect_at_limit_break(CardConstants.MIN_LIMIT_BREAK)

    def get_effect_at_max_limit_break(self, effect: CardEffect) -> int:
        """Get effect value at maximum level for maximum limit break."""
        return self.get_effect_at_limit_break(CardConstants.MAX_LIMIT_BREAK)


    def get_all_effects_at_level(self, level: int) -> dict[str, int]:
        """
        Get all effects for this card at the specified level.
        
        Args:
            level: level
            
        Returns:
            Dictionary mapping effect names to values
            
        Note:
            This method benefits heavily from LRU caching since it calls
            _interpolate_effect_value multiple times for the same level.
        """
        effects = {}
        
        # Get all effect types present on this card
        present_effect_ids = set()
        for effects_row in self.effects:
            if len(effects_row) > 0:
                present_effect_ids.add(effects_row[0])
        
        # Calculate value for each present effect type
        for effect_type_id in present_effect_ids:
            try:
                effect_name = CardEffect(effect_type_id).name
                value = self._interpolate_effect_value(CardEffect(effect_type_id), level)
                if value > 0:  # Only include non-zero effects
                    effects[effect_name] = value
            except ValueError:
                continue
        
        return effects

    def get_all_effects_at_limit_break(self, limit_break: int) -> dict[str, int]:
        """
        Get all effects for this card at the specified limit break.
        
        Args:
            limit_break: limit break
            
        Returns:
            Dictionary mapping effect names to values
        """
        level = self.get_level_at_limit_break(limit_break)
        return self.get_all_effects_at_level(level)

    # TODO: add methods to get unique effects

    def __hash__(self) -> int:
        """Make Card hashable for LRU cache support."""
        return hash(self.id)  # Use card ID as hash since it's unique
    
    def __eq__(self, other) -> bool:
        """Define equality for hashing."""
        if not isinstance(other, Card):
            return False
        return self.id == other.id

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.id}, name='{self.name}', rarity={self.rarity}, type={self.type})"
