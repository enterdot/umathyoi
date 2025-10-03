import logging
logger = logging.getLogger(__name__)

from enum import Enum
from dataclasses import dataclass
from .skill import Skill, SkillType
from .card import Card, CardType, CardEffect, CardUniqueEffect
from .deck import Deck
from .scenario import Scenario, Facility, FacilityType
from .character import GenericCharacter, StatType, Mood
from .event import Event
from utils import GameplayConstants, CardConstants, debounce, auto_title_from_instance, stopwatch

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
        import time
        
        # Track cumulative times across all Turn instances
        if not hasattr(Turn, '_profile_times'):
            Turn._profile_times = {
                'distribute': 0,
                'create_effects': 0,
                'total_calls': 0
            }
        
        start = time.perf_counter()
        
        # Distribute cards among facilities
        card_facilities = self._distribute_cards()
        distribute_time = time.perf_counter() - start
        
        object.__setattr__(self, 'card_facilities', card_facilities)

        effects_start = time.perf_counter()
        
        # Build training effects - only for cards that actually appeared
        training_effects = {facility: [] for facility in FacilityType}
        for card, facility_type in card_facilities.items():
            effect = TrainingEffect(card, self)
            training_effects[facility_type].append(effect)
        
        effects_time = time.perf_counter() - effects_start
        
        object.__setattr__(self, 'training_effects', training_effects)
        
        # Accumulate times
        Turn._profile_times['distribute'] += distribute_time
        Turn._profile_times['create_effects'] += effects_time
        Turn._profile_times['total_calls'] += 1
        
        # Print report after last turn (assuming 10000 turns)
        if Turn._profile_times['total_calls'] == 10000:
            total = Turn._profile_times['distribute'] + Turn._profile_times['create_effects']
            print(f"\n{'='*60}")
            print(f"Turn Creation Breakdown (10000 turns)")
            print(f"{'='*60}")
            print(f"_distribute_cards:    {Turn._profile_times['distribute']*1000:7.2f}ms ({Turn._profile_times['distribute']/total*100:5.1f}%)")
            print(f"TrainingEffect init:  {Turn._profile_times['create_effects']*1000:7.2f}ms ({Turn._profile_times['create_effects']/total*100:5.1f}%)")
            print(f"Total:                {total*1000:7.2f}ms")
            print(f"{'='*60}\n")
            
            # Reset for next run
            Turn._profile_times = {'distribute': 0, 'create_effects': 0, 'total_calls': 0}

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


# Class-level caches (defined BEFORE the dataclass decorator)
_normal_effects_cache: dict = {}
_unique_effects_cache: dict = {}

@dataclass(frozen=True)
class TrainingEffect:
    """The effect on training a card provides based on turn state"""
    card: Card
    turn: Turn

    def __post_init__(self):
        """Calculate combined normal and unique effects"""
        object.__setattr__(self, 'combined_effects', self._calculate_combined_effects())
    
    @property
    def facility_type(self) -> FacilityType:
        return self.turn.card_facilities[self.card]

    def _handle_unique_effect(self, effect_type: CardUniqueEffect, values: list[int]) -> list[tuple[CardEffect, int]]:
        """Handle a unique effect inline instead of using lambda closures."""
        
        if effect_type == CardUniqueEffect.effect_bonus_if_min_bond:
            # unique_effect_id = 101
            return [(CardEffect(values[1]), values[2] * (self.turn.card_bonds[self.card] >= values[0]))]
        
        elif effect_type == CardUniqueEffect.effect_bonus_per_combined_bond:
            # unique_effect_id = 109
            return [(CardEffect(values[0]), 20 + self.turn.combined_bond_gauge // values[1])]
        
        elif effect_type == CardUniqueEffect.effect_bonus_per_facility_level:
            # unique_effect_id = 111
            return [(CardEffect(values[0]), self.turn.facility_levels[self.facility_type] * values[1])]
        
        elif effect_type == CardUniqueEffect.effect_bonus_if_friendship_training:
            # unique_effect_id = 113
            return [(CardEffect(values[0]), values[1] * self.card.is_preferred_facility(self.facility_type))]
        
        elif effect_type == CardUniqueEffect.effect_bonus_on_more_energy:
            # unique_effect_id = 114
            return [(CardEffect(values[0]), min(self.turn.energy // values[1], values[2]))]
        
        elif effect_type == CardUniqueEffect.effect_bonus_on_less_energy:
            # unique_effect_id = 107
            return [(
                CardEffect(values[0]),
                min(values[3], values[4] + (self.turn.max_energy - max(self.turn.energy, values[2])) // values[1]) * (self.turn.energy <= 100)
            )]
        
        elif effect_type == CardUniqueEffect.effect_bonus_on_more_max_energy:
            # unique_effect_id = 108
            return []
        
        else:
            return []

    def _calculate_combined_effects(self) -> dict[CardEffect, int]:
        """Calculate combined normal and unique effects for this card."""
        card_level = self.turn.card_levels[self.card]
        
        # Get normal effects - cache them using module-level cache
        cache_key = (self.card.id, card_level)
        if cache_key in _normal_effects_cache:
            effects = _normal_effects_cache[cache_key].copy()
        else:
            effects = self.card.get_all_effects_at_level(card_level)
            _normal_effects_cache[cache_key] = effects.copy()
        
        # Check if unique effects are unlocked
        if card_level < self.card.unique_effects_unlock_level:
            return effects
        
        # Get unique effects - cache them using module-level cache
        if self.card.id in _unique_effects_cache:
            unique_effects = _unique_effects_cache[self.card.id]
        else:
            unique_effects = self.card.get_all_unique_effects()
            _unique_effects_cache[self.card.id] = unique_effects
        
        if not unique_effects:
            return effects
        
        flattened_effects = {}
        for unique_effect_type, unique_effect_values in unique_effects.items():
            if unique_effect_type.value < CardConstants.COMPLEX_UNIQUE_EFFECTS_ID_THRESHOLD:
                if len(unique_effect_values) != 1:
                    logger.warning(f"Card {self.card.id} should have 1 value for unique effect {unique_effect_type.name()}")
                mapped_effect_type = CardEffect(unique_effect_type.value)
                flattened_effects[mapped_effect_type] = flattened_effects.get(mapped_effect_type, 0) + unique_effect_values[0]
            else:
                # Dynamic effects - must calculate each time
                results = self._handle_unique_effect(unique_effect_type, unique_effect_values)
                for effect_type, effect_value in results:
                    flattened_effects[effect_type] = flattened_effects.get(effect_type, 0) + effect_value
        
        # Merge effects
        combined_effects = effects.copy()
        for effect_type, unique_value in flattened_effects.items():
            if effect_type == CardEffect.friendship_effectiveness:
                normal_value = combined_effects.get(effect_type, 0)
                combined = ((GameplayConstants.PERCENTAGE_BASE + normal_value) * 
                           (GameplayConstants.PERCENTAGE_BASE + unique_value) / 
                           GameplayConstants.PERCENTAGE_BASE) - GameplayConstants.PERCENTAGE_BASE
                combined_effects[effect_type] = int(combined)
            else:
                combined_effects[effect_type] = combined_effects.get(effect_type, 0) + unique_value
        
        return combined_effects
                
class EfficiencyCalculator:
    """Calculator that pre-computes static effects, calculates dynamic ones on-demand."""
    
    def __init__(self, deck: Deck, scenario: Scenario, character: GenericCharacter):
        self._deck = deck
        self._scenario = scenario
        self._character = character
        self._fan_count = 100000
        self._mood = Mood.good
        self._energy = 80
        self._max_energy = 120
        self._facility_levels = {facility: 3 for facility in FacilityType}
        self._card_levels = {card: card.max_level for card in deck.cards}
        self._card_bonds = {card: 80 for card in deck.cards}
        self._skills = []
        
        self.turn_count = 1000
        
        # Events
        self.calculation_started = Event()
        self.calculation_progress = Event()
        self.calculation_finished = Event()
        
        # Pre-calculate static card data once
        self._precalculate_static_effects()

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
    def character(self) -> GenericCharacter:
        return self._character
    
    @character.setter
    def character(self, value: GenericCharacter) -> None:
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

    def _precalculate_static_effects(self):
        """Pre-calculate the static parts (normal + simple unique effects)."""
        self._static_effects = {}
        self._dynamic_unique_effects = {}
        
        for card in self._deck.cards:
            level = self._card_levels[card]
            effects = card.get_all_effects_at_level(level)
            
            # Handle unique effects
            if level >= card.unique_effects_unlock_level:
                unique = card.get_all_unique_effects()
                if unique:
                    dynamic_effects = {}
                    for eff_type, values in unique.items():
                        if eff_type.value < CardConstants.COMPLEX_UNIQUE_EFFECTS_ID_THRESHOLD:
                            # Static unique effect
                            mapped = CardEffect(eff_type.value)
                            effects[mapped] = effects.get(mapped, 0) + values[0]
                        else:
                            # Dynamic unique effect - store for later calculation
                            dynamic_effects[eff_type] = values
                    
                    if dynamic_effects:
                        self._dynamic_unique_effects[card] = dynamic_effects
            
            self._static_effects[card] = effects
    
    def _calculate_dynamic_effects(self, card: Card, facility_type: FacilityType, 
                                   combined_bond: int) -> dict[CardEffect, int]:
        """Calculate dynamic unique effects based on turn state."""
        if card not in self._dynamic_unique_effects:
            return {}
        
        effects = {}
        for eff_type, values in self._dynamic_unique_effects[card].items():
            if eff_type == CardUniqueEffect.effect_bonus_if_min_bond:
                effects[CardEffect(values[1])] = values[2] * (self._card_bonds[card] >= values[0])
            
            elif eff_type == CardUniqueEffect.effect_bonus_per_combined_bond:
                effects[CardEffect(values[0])] = 20 + combined_bond // values[1]
            
            elif eff_type == CardUniqueEffect.effect_bonus_per_facility_level:
                effects[CardEffect(values[0])] = self._facility_levels[facility_type] * values[1]
            
            elif eff_type == CardUniqueEffect.effect_bonus_if_friendship_training:
                effects[CardEffect(values[0])] = values[1] * card.is_preferred_facility(facility_type)
            
            elif eff_type == CardUniqueEffect.effect_bonus_on_more_energy:
                effects[CardEffect(values[0])] = min(self._energy // values[1], values[2])
            
            elif eff_type == CardUniqueEffect.effect_bonus_on_less_energy:
                effects[CardEffect(values[0])] = min(values[3], values[4] + (self._max_energy - max(self._energy, values[2])) // values[1]) * (self._energy <= 100)
        
        return effects
    
    @debounce(wait_ms=350)
    def recalculate(self):
        self._recalculate_sync()
    
    def _recalculate_sync(self):
        """Monte Carlo simulation with minimal object creation."""
        import random
        import time
        
        start = time.perf_counter()
        self.calculation_started.trigger(self)
        
        # Store minimal turn data
        turn_data = []
        
        for i in range(self.turn_count):
            # Distribute cards
            card_facilities = {}
            for card in self._deck.cards:
                specialty = card.get_effect_at_level(CardEffect.specialty_priority, self._card_levels[card])
                total_weight = 500 + specialty + 50
                preferred = card.preferred_facility
                
                weights = [100 + specialty if f == preferred else 100 for f in FacilityType]
                weights.append(50)
                
                outcomes = list(FacilityType) + [None]
                chosen = random.choices(outcomes, weights=weights, k=1)[0]
                
                if chosen is not None:
                    card_facilities[card] = chosen
            
            turn_data.append(card_facilities)
            
            if (i + 1) % max(1, self.turn_count // 100) == 0:
                self.calculation_progress.trigger(self, current=i+1, total=self.turn_count)
        
        turn_time = time.perf_counter() - start
        agg_start = time.perf_counter()
        
        # Aggregation
        aggregated_gains = {f: {s: [] for s in StatType} for f in FacilityType}
        aggregated_skill_points = {f: [] for f in FacilityType}
        
        combined_bond = sum(self._card_bonds.values())
        
        for card_facilities in turn_data:
            by_facility = {f: [] for f in FacilityType}
            for card, facility in card_facilities.items():
                by_facility[facility].append(card)
            
            for facility_type, cards_on_facility in by_facility.items():
                if not cards_on_facility:
                    continue
                
                facility = self._scenario.facilities[facility_type]
                level = self._facility_levels[facility_type]
                base_stats = facility.get_all_stat_gains_at_level(level)
                base_skill_points = facility.get_skill_points_gain_at_level(level)
                
                # Accumulate effects from all cards
                stat_bonuses = {s: 0 for s in StatType}
                skill_bonus = 0
                friendship_mult = 1.0
                training_eff = 0
                mood_eff = 0
                
                for card in cards_on_facility:
                    # Start with static effects
                    effects = self._static_effects[card].copy()
                    
                    # Add dynamic effects
                    dynamic = self._calculate_dynamic_effects(card, facility_type, combined_bond)
                    for eff_type, value in dynamic.items():
                        effects[eff_type] = effects.get(eff_type, 0) + value
                    
                    # Accumulate
                    stat_bonuses[StatType.speed] += effects.get(CardEffect.speed_stat_bonus, 0)
                    stat_bonuses[StatType.stamina] += effects.get(CardEffect.stamina_stat_bonus, 0)
                    stat_bonuses[StatType.power] += effects.get(CardEffect.power_stat_bonus, 0)
                    stat_bonuses[StatType.guts] += effects.get(CardEffect.guts_stat_bonus, 0)
                    stat_bonuses[StatType.wit] += effects.get(CardEffect.wit_stat_bonus, 0)
                    skill_bonus += effects.get(CardEffect.skill_points_bonus, 0)
                    training_eff += effects.get(CardEffect.training_effectiveness, 0)
                    mood_eff += effects.get(CardEffect.mood_effect_increase, 0)
                    
                    if card.is_preferred_facility(facility_type):
                        friend_eff = effects.get(CardEffect.friendship_effectiveness, 0)
                        friendship_mult *= (1 + friend_eff / 100)
                
                # Calculate multipliers
                mood_mult = 1 + (self._mood.multiplier - 1) * (1 + mood_eff / 100)
                training_mult = 1 + training_eff / 100
                support_mult = 1 + len(cards_on_facility) * 0.05
                
                # Calculate final gains
                for stat in StatType:
                    base = base_stats.get(stat, 0)
                    if base == 0:
                        aggregated_gains[facility_type][stat].append(0)
                        continue
                    
                    total_base = base + stat_bonuses[stat]
                    growth = self._character.get_stat_growth_multipler(stat)
                    final = total_base * friendship_mult * mood_mult * training_mult * support_mult * growth
                    aggregated_gains[facility_type][stat].append(int(final))
                
                aggregated_skill_points[facility_type].append(base_skill_points + skill_bonus)
        
        agg_time = time.perf_counter() - agg_start
        total = time.perf_counter() - start
        
        self._aggregated_stat_gains = aggregated_gains
        self._aggregated_skill_points = aggregated_skill_points
        
        print(f"\n{'='*60}")
        print(f"Performance Profile ({self.turn_count} turns)")
        print(f"{'='*60}")
        print(f"Turn generation: {turn_time*1000:7.2f}ms ({turn_time/total*100:5.1f}%)")
        print(f"Aggregation:     {agg_time*1000:7.2f}ms ({agg_time/total*100:5.1f}%)")
        print(f"Total:           {total*1000:7.2f}ms")
        print(f"{'='*60}\n")
        
        self.calculation_finished.trigger(self, results=self._aggregated_stat_gains)

    def get_results(self) -> dict | None:
        """Get aggregated calculation results.
        
        Returns dict with structure:
        {
            'per_facility': {
                FacilityType: {
                    'stats': {StatType: {'mean': float, 'min': int, 'max': int}},
                    'skill_points': {'mean': float, 'min': int, 'max': int}
                }
            },
            'total': {
                'stats': {StatType: {'mean': float, 'total': float}},
                'skill_points': {'mean': float, 'total': float}
            }
        }
        
        Returns None if no calculation has been performed yet.
        """
        if not hasattr(self, '_aggregated_stat_gains'):
            return None
        
        results = {'per_facility': {}, 'total': {'stats': {}, 'skill_points': {}}}
        
        # Calculate per-facility statistics
        for facility_type in FacilityType:
            facility_results = {'stats': {}, 'skill_points': {}}
            
            # Process each stat
            for stat_type in StatType:
                gains = self._aggregated_stat_gains[facility_type][stat_type]
                if gains:
                    facility_results['stats'][stat_type] = {
                        'mean': sum(gains) / len(gains),
                        'min': min(gains),
                        'max': max(gains)
                    }
                else:
                    facility_results['stats'][stat_type] = {'mean': 0.0, 'min': 0, 'max': 0}
            
            # Process skill points
            skill_points = self._aggregated_skill_points[facility_type]
            if skill_points:
                facility_results['skill_points'] = {
                    'mean': sum(skill_points) / len(skill_points),
                    'min': min(skill_points),
                    'max': max(skill_points)
                }
            else:
                facility_results['skill_points'] = {'mean': 0.0, 'min': 0, 'max': 0}
            
            results['per_facility'][facility_type] = facility_results
        
        # Calculate totals across all facilities
        for stat_type in StatType:
            all_gains = []
            for facility_type in FacilityType:
                all_gains.extend(self._aggregated_stat_gains[facility_type][stat_type])
            
            if all_gains:
                results['total']['stats'][stat_type] = {
                    'mean': sum(all_gains) / len(all_gains),
                    'total': sum(all_gains)
                }
            else:
                results['total']['stats'][stat_type] = {'mean': 0.0, 'total': 0.0}
        
        # Calculate total skill points
        all_skill_points = []
        for facility_type in FacilityType:
            all_skill_points.extend(self._aggregated_skill_points[facility_type])
        
        if all_skill_points:
            results['total']['skill_points'] = {
                'mean': sum(all_skill_points) / len(all_skill_points),
                'total': sum(all_skill_points)
            }
        else:
            results['total']['skill_points'] = {'mean': 0.0, 'total': 0.0}
        
        return results


    def print_results(self) -> None:
        """Print calculation results to terminal."""
        results = self.get_results()
        
        if results is None:
            print("No calculation results available. Run recalculate() first.")
            return
        
        print(f"\n{'='*80}")
        print(f"Efficiency Calculation Results ({self.turn_count} simulated turns)")
        print(f"{'='*80}")
        
        # Print deck info
        print(f"\nDeck: {self.deck.name}")
        print(f"Scenario: {self.scenario.name}")
        print(f"Stat Growth: {self.character.stat_growth}")
        print(f"Energy: {self.energy}/{self.max_energy}")
        print(f"Mood: {self.mood.name}")
        print(f"Fans: {self.fan_count:,}")
        print(f"Facility level: {self.facility_levels.values()}")
        
        # Print per-facility results
        print(f"\n{'-'*80}")
        print("Per-Facility Average Gains:")
        print(f"{'-'*80}")
        
        for facility_type in FacilityType:
            facility_data = results['per_facility'][facility_type]
            print(f"\n{facility_type.name.upper()} Training:")
            
            # Print stats
            for stat_type in StatType:
                stat_data = facility_data['stats'][stat_type]
                if stat_data['mean'] > 0:
                    print(f"  {stat_type.name.capitalize():10s}: {stat_data['mean']:6.2f} (min: {stat_data['min']:3d}, max: {stat_data['max']:3d})")
            
            # Print skill points
            sp_data = facility_data['skill_points']
            if sp_data['mean'] > 0:
                print(f"  {'Skill Pts':10s}: {sp_data['mean']:6.2f} (min: {sp_data['min']:3d}, max: {sp_data['max']:3d})")
        
        # Print totals
        print(f"\n{'-'*80}")
        print("Total Gains Across All Facilities:")
        print(f"{'-'*80}")
        
        for stat_type in StatType:
            stat_data = results['total']['stats'][stat_type]
            print(f"  {stat_type.name.capitalize():10s}: {stat_data['total']:8.1f} total, {stat_data['mean']:6.2f} avg per turn")
        
        sp_data = results['total']['skill_points']
        print(f"  {'Skill Pts':10s}: {sp_data['total']:8.1f} total, {sp_data['mean']:6.2f} avg per turn")
        
        print(f"\n{'='*80}\n")
