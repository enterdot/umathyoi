import logging

logger = logging.getLogger(__name__)

import random

from .skill import Skill
from .card import Card, CardEffect, CardUniqueEffect
from .deck import Deck
from .deck_list import DeckList
from .scenario import Scenario, FacilityType
from .character import GenericCharacter, StatType, Mood
from .event import Event
from common import debounce, auto_title_from_instance


class EfficiencyCalculator:
    """Calculator that pre-computes static effects, calculates dynamic ones on-demand."""

    MIN_ENERGY: int = 0
    MAX_ENERGY: int = 120
    MIN_MAX_ENERGY: int = 100
    MIN_FANS: int = 1
    MAX_FANS: int = 350000

    def __init__(self, deck_list, scenario: Scenario, character: GenericCharacter):
        self._deck_list = deck_list
        self._scenario = scenario
        self._character = character
        self._fan_count = 100000
        self._mood = Mood.good
        self._energy = 80
        self._max_energy = 120
        self._facility_levels = {facility: 3 for facility in FacilityType}
        self._card_levels = {card: card.max_level for card in deck_list.active_deck.cards}
        self._card_bonds = {card: 80 for card in deck_list.active_deck.cards}
        self._skills = []

        self.turn_count = 1000

        # Events
        self.calculation_started = Event()
        self.calculation_progress = Event()
        self.calculation_finished = Event()

        # Subscribe to deck list events
        self._subscribe_to_deck_events()

        # Pre-calculate static card data once
        self._precalculate_static_effects()

        logger.debug(f"{auto_title_from_instance(self)} initialized")

    @property
    def deck_list(self):
        return self._deck_list

    @deck_list.setter
    def deck_list(self, value) -> None:
        self._deck_list = value
        self._subscribe_to_deck_events()
        self._precalculate_static_effects()
        self.recalculate()

    @property
    def deck(self) -> Deck:
        return self._deck_list.active_deck

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

    def _subscribe_to_deck_events(self):
        """Subscribe to deck list events to detect when deck changes."""
        # Active deck content changed
        self._deck_list.card_added_to_active_deck_at_slot.subscribe(self._on_deck_changed)
        self._deck_list.card_removed_from_active_deck_at_slot.subscribe(self._on_deck_changed)
        self._deck_list.limit_break_set_for_active_deck_at_slot.subscribe(self._on_deck_changed)
        self._deck_list.active_deck_was_cleared.subscribe(self._on_deck_changed)
        
        # Active deck swapped
        self._deck_list.slot_activated.subscribe(self._on_deck_swapped)

    def _on_deck_changed(self, source, **kwargs):
        """Called when the active deck's contents change."""
        # Sync card levels and bonds with current deck
        current_cards = set(self.deck.cards)
        
        # Remove cards no longer in deck
        self._card_levels = {card: level for card, level in self._card_levels.items() if card in current_cards}
        self._card_bonds = {card: bond for card, bond in self._card_bonds.items() if card in current_cards}
        
        # Add new cards with default values
        for card in current_cards:
            if card not in self._card_levels:
                self._card_levels[card] = card.max_level
            if card not in self._card_bonds:
                self._card_bonds[card] = 80
        
        self._precalculate_static_effects()
        self.recalculate()

    def _on_deck_swapped(self, source, **kwargs):
        """Called when a different deck becomes active."""
        # Reset card levels and bonds for new deck
        self._card_levels = {card: card.max_level for card in self.deck.cards}
        self._card_bonds = {card: 80 for card in self.deck.cards}
        self._precalculate_static_effects()
        self.recalculate()

    def _precalculate_static_effects(self):
        """Pre-calculate the static effects (normal + simple unique effects)."""
        logger.debug("Pre-calculating normal effects and static unique effects")
        self._static_effects = {}
        self._static_unique_effects = {}
        self._dynamic_unique_effects = {}
        self._card_stat_bonuses = {}
        self._card_distribution = {}

        for card in self.deck.cards:
            level = self._card_levels[card]
            effects = card.get_all_effects_at_level(level)

            # Handle unique effects
            unique_static = {}
            if level >= card.unique_effects_unlock_level:
                unique = card.get_all_unique_effects()
                if unique:
                    dynamic_effects = {}
                    for eff_type, values in unique.items():
                        if eff_type.value < Card.DYNAMIC_UNIQUE_EFFECT_ID_THRESHOLD:
                            # Static unique effect - map to CardEffect and store separately
                            mapped = CardEffect(eff_type.value)
                            unique_static[mapped] = values[0]
                        else:
                            # Dynamic unique effect - store for runtime calculation
                            dynamic_effects[eff_type] = values

                    if dynamic_effects:
                        self._dynamic_unique_effects[card] = dynamic_effects

            self._static_effects[card] = effects
            self._static_unique_effects[card] = unique_static

            # Pre-extract stat bonuses to avoid dict lookups in hot loop
            # Note: normal and unique static effects are kept separate for friendship handling
            self._card_stat_bonuses[card] = {
                "speed": effects.get(CardEffect.speed_stat_bonus, 0),
                "stamina": effects.get(CardEffect.stamina_stat_bonus, 0),
                "power": effects.get(CardEffect.power_stat_bonus, 0),
                "guts": effects.get(CardEffect.guts_stat_bonus, 0),
                "wit": effects.get(CardEffect.wit_stat_bonus, 0),
                "skill": effects.get(CardEffect.skill_points_bonus, 0),
                "training": effects.get(CardEffect.training_effectiveness, 0),
                "mood": effects.get(CardEffect.mood_effect_increase, 0),
                "friendship": effects.get(CardEffect.friendship_effectiveness, 0),
                # Unique static effects (kept separate for friendship calculation)
                "unique_speed": unique_static.get(CardEffect.speed_stat_bonus, 0),
                "unique_stamina": unique_static.get(CardEffect.stamina_stat_bonus, 0),
                "unique_power": unique_static.get(CardEffect.power_stat_bonus, 0),
                "unique_guts": unique_static.get(CardEffect.guts_stat_bonus, 0),
                "unique_wit": unique_static.get(CardEffect.wit_stat_bonus, 0),
                "unique_skill": unique_static.get(CardEffect.skill_points_bonus, 0),
                "unique_training": unique_static.get(CardEffect.training_effectiveness, 0),
                "unique_mood": unique_static.get(CardEffect.mood_effect_increase, 0),
                "unique_friendship": unique_static.get(CardEffect.friendship_effectiveness, 0),
            }

            specialty = card.get_effect_at_level(CardEffect.specialty_priority, self._card_levels[card])
            preferred = card.preferred_facility

            # Build cumulative probability ranges for fast selection
            total_weight = 500 + specialty + 50

            # Create cumulative ranges: [0, facility1_end, facility2_end, ..., total_weight]
            cumulative = []
            current = 0
            outcomes = []

            for facility in FacilityType:
                weight = 100 + specialty if facility == preferred else 100
                current += weight
                cumulative.append(current)
                outcomes.append(facility)

            # Add non-appearance
            current += 50
            cumulative.append(current)
            outcomes.append(None)

            self._card_distribution[card] = {"cumulative": cumulative, "outcomes": outcomes, "total_weight": total_weight}

    @debounce(wait_ms=350)
    def recalculate(self):
        self._recalculate_sync()

    def _recalculate_sync(self):
        """Monte Carlo simulation."""

        self.calculation_started.trigger(self)

        # Store minimal turn data
        turn_data = []

        for i in range(self.turn_count):
            card_facilities = {}

            for card in self.deck.cards:
                # Fast random selection using pre-calculated cumulative probabilities
                dist_data = self._card_distribution[card]
                rand_val = random.random() * dist_data["total_weight"]

                # Find which range the random value falls into
                chosen = dist_data["outcomes"][-1]  # Default to last outcome (None)
                for idx, threshold in enumerate(dist_data["cumulative"]):
                    if rand_val < threshold:
                        chosen = dist_data["outcomes"][idx]
                        break

                if chosen is not None:
                    card_facilities[card] = chosen

            turn_data.append(card_facilities)

            if (i + 1) % max(1, self.turn_count // 100) == 0:
                self.calculation_progress.trigger(self, current=i + 1, total=self.turn_count)

        # Aggregation
        aggregated_gains = {f: {s: [] for s in StatType} for f in FacilityType}
        aggregated_skill_points = {f: [] for f in FacilityType}

        combined_bond = sum(self._card_bonds.values())

        for card_facilities in turn_data:
            # Group cards by facility
            by_facility = {f: [] for f in FacilityType}
            for card, facility in card_facilities.items():
                by_facility[facility].append(card)

            for facility_type, cards_on_facility in by_facility.items():
                if not cards_on_facility:
                    continue

                # Get facility data
                facility = self._scenario.facilities[facility_type]
                level = self._facility_levels[facility_type]
                base_stats = facility.get_all_stat_gains_at_level(level)
                base_skill_points = facility.get_skill_points_gain_at_level(level)

                # Accumulate effects from all cards
                stat_bonuses = {s: 0 for s in StatType}
                skill_bonus = 0
                training_eff = 0
                mood_eff = 0
                friendship_mult = 1.0

                for card in cards_on_facility:
                    bonuses = self._card_stat_bonuses[card]

                    # Add normal static bonuses
                    stat_bonuses[StatType.speed] += bonuses["speed"]
                    stat_bonuses[StatType.stamina] += bonuses["stamina"]
                    stat_bonuses[StatType.power] += bonuses["power"]
                    stat_bonuses[StatType.guts] += bonuses["guts"]
                    stat_bonuses[StatType.wit] += bonuses["wit"]
                    skill_bonus += bonuses["skill"]
                    training_eff += bonuses["training"]
                    mood_eff += bonuses["mood"]

                    # Add unique static bonuses
                    stat_bonuses[StatType.speed] += bonuses["unique_speed"]
                    stat_bonuses[StatType.stamina] += bonuses["unique_stamina"]
                    stat_bonuses[StatType.power] += bonuses["unique_power"]
                    stat_bonuses[StatType.guts] += bonuses["unique_guts"]
                    stat_bonuses[StatType.wit] += bonuses["unique_wit"]
                    skill_bonus += bonuses["unique_skill"]
                    training_eff += bonuses["unique_training"]
                    mood_eff += bonuses["unique_mood"]

                    # Handle dynamic unique effects
                    dynamic_friendship = 0  # Accumulate dynamic friendship for this card
                    
                    if card in self._dynamic_unique_effects:
                        for eff_type, values in self._dynamic_unique_effects[card].items():
                            if eff_type == CardUniqueEffect.effect_bonus_if_min_bond:
                                if self._card_bonds[card] >= values[0]:
                                    effect_id = CardEffect(values[1])
                                    bonus = values[2]
                                    if effect_id == CardEffect.speed_stat_bonus:
                                        stat_bonuses[StatType.speed] += bonus
                                    elif effect_id == CardEffect.stamina_stat_bonus:
                                        stat_bonuses[StatType.stamina] += bonus
                                    elif effect_id == CardEffect.power_stat_bonus:
                                        stat_bonuses[StatType.power] += bonus
                                    elif effect_id == CardEffect.guts_stat_bonus:
                                        stat_bonuses[StatType.guts] += bonus
                                    elif effect_id == CardEffect.wit_stat_bonus:
                                        stat_bonuses[StatType.wit] += bonus
                                    elif effect_id == CardEffect.skill_points_bonus:
                                        skill_bonus += bonus
                                    elif effect_id == CardEffect.training_effectiveness:
                                        training_eff += bonus
                                    elif effect_id == CardEffect.mood_effect_increase:
                                        mood_eff += bonus
                                    elif effect_id == CardEffect.friendship_effectiveness:
                                        dynamic_friendship += bonus

                            elif eff_type == CardUniqueEffect.effect_bonus_per_combined_bond:
                                effect_id = CardEffect(values[0])
                                bonus = 20 + combined_bond // values[1]
                                if effect_id == CardEffect.training_effectiveness:
                                    training_eff += bonus
                                elif effect_id == CardEffect.friendship_effectiveness:
                                    dynamic_friendship += bonus

                            elif eff_type == CardUniqueEffect.effect_bonus_per_facility_level:
                                effect_id = CardEffect(values[0])
                                bonus = self._facility_levels[facility_type] * values[1]
                                if effect_id == CardEffect.training_effectiveness:
                                    training_eff += bonus
                                elif effect_id == CardEffect.friendship_effectiveness:
                                    dynamic_friendship += bonus

                            elif eff_type == CardUniqueEffect.effect_bonus_if_friendship_training:
                                if card.is_preferred_facility(facility_type):
                                    effect_id = CardEffect(values[0])
                                    bonus = values[1]
                                    if effect_id == CardEffect.training_effectiveness:
                                        training_eff += bonus
                                    elif effect_id == CardEffect.friendship_effectiveness:
                                        dynamic_friendship += bonus

                            elif eff_type == CardUniqueEffect.effect_bonus_on_more_energy:
                                effect_id = CardEffect(values[0])
                                bonus = min(self._energy // values[1], values[2])
                                if effect_id == CardEffect.training_effectiveness:
                                    training_eff += bonus
                                elif effect_id == CardEffect.friendship_effectiveness:
                                    dynamic_friendship += bonus

                            elif eff_type == CardUniqueEffect.effect_bonus_on_less_energy:
                                if self._energy <= 100:
                                    effect_id = CardEffect(values[0])
                                    bonus = min(values[3], values[4] + (self._max_energy - max(self._energy, values[2])) // values[1])
                                    if effect_id == CardEffect.training_effectiveness:
                                        training_eff += bonus
                                    elif effect_id == CardEffect.friendship_effectiveness:
                                        dynamic_friendship += bonus

                    # Friendship calculation (special multiplicative rules)
                    if card.is_preferred_facility(facility_type):
                        # Rule 3a: Add dynamic + static unique friendship
                        unique_friendship_total = bonuses["unique_friendship"] + dynamic_friendship
                        
                        # Rule 3b: Multiply unique with normal friendship
                        # (1 + unique/100) * (1 + normal/100)
                        card_friendship_mult = (1 + unique_friendship_total / 100) * (1 + bonuses["friendship"] / 100)
                        
                        # Rule 3c: Multiply with other cards' friendship
                        friendship_mult *= card_friendship_mult

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

        self._aggregated_stat_gains = aggregated_gains
        self._aggregated_skill_points = aggregated_skill_points
        self.calculation_finished.trigger(self, results=self._aggregated_stat_gains)
        logger.debug("Deck efficiency calculation completed")

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
        if not hasattr(self, "_aggregated_stat_gains"):
            return None

        results = {"per_facility": {}, "total": {"stats": {}, "skill_points": {}}}

        # Calculate per-facility statistics
        for facility_type in FacilityType:
            facility_results = {"stats": {}, "skill_points": {}}

            # Process each stat
            for stat_type in StatType:
                gains = self._aggregated_stat_gains[facility_type][stat_type]
                if gains:
                    facility_results["stats"][stat_type] = {"mean": sum(gains) / len(gains), "min": min(gains), "max": max(gains)}
                else:
                    facility_results["stats"][stat_type] = {"mean": 0.0, "min": 0, "max": 0}

            # Process skill points
            skill_points = self._aggregated_skill_points[facility_type]
            if skill_points:
                facility_results["skill_points"] = {"mean": sum(skill_points) / len(skill_points), "min": min(skill_points), "max": max(skill_points)}
            else:
                facility_results["skill_points"] = {"mean": 0.0, "min": 0, "max": 0}

            results["per_facility"][facility_type] = facility_results

        # Calculate totals across all facilities
        for stat_type in StatType:
            all_gains = []
            for facility_type in FacilityType:
                all_gains.extend(self._aggregated_stat_gains[facility_type][stat_type])

            if all_gains:
                results["total"]["stats"][stat_type] = {"mean": sum(all_gains) / len(all_gains), "total": sum(all_gains)}
            else:
                results["total"]["stats"][stat_type] = {"mean": 0.0, "total": 0.0}

        # Calculate total skill points
        all_skill_points = []
        for facility_type in FacilityType:
            all_skill_points.extend(self._aggregated_skill_points[facility_type])

        if all_skill_points:
            results["total"]["skill_points"] = {"mean": sum(all_skill_points) / len(all_skill_points), "total": sum(all_skill_points)}
        else:
            results["total"]["skill_points"] = {"mean": 0.0, "total": 0.0}

        return results

    def print_results(self) -> None:
        """Print calculation results to terminal."""
        results = self.get_results()

        if results is None:
            print("No calculation results available. Run recalculate() first.")
            return

        print(f"\n{'=' * 80}")
        print(f"Efficiency Calculation Results ({self.turn_count} simulated turns)")
        print(f"{'=' * 80}")

        # Print deck info
        print(f"\nDeck: {self.deck}")
        print(f"Scenario: {self.scenario.name}")
        print(f"Stat Growth: {self.character.stat_growth}")
        print(f"Energy: {self.energy}/{self.max_energy}")
        print(f"Mood: {self.mood.name}")
        print(f"Fans: {self.fan_count:,}")
        print(f"Facility level: {self.facility_levels.values()}")

        # Print per-facility results
        print(f"\n{'-' * 80}")
        print("Per-Facility Average Gains:")
        print(f"{'-' * 80}")

        for facility_type in FacilityType:
            facility_data = results["per_facility"][facility_type]
            print(f"\n{facility_type.name.upper()} Training:")

            # Print stats
            for stat_type in StatType:
                stat_data = facility_data["stats"][stat_type]
                if stat_data["mean"] > 0:
                    print(f"  {stat_type.name.capitalize():10s}: {stat_data['mean']:6.2f} (min: {stat_data['min']:3d}, max: {stat_data['max']:3d})")

            # Print skill points
            sp_data = facility_data["skill_points"]
            if sp_data["mean"] > 0:
                print(f"  {'Skill Pts':10s}: {sp_data['mean']:6.2f} (min: {sp_data['min']:3d}, max: {sp_data['max']:3d})")

        # Print totals
        print(f"\n{'-' * 80}")
        print("Total Gains Across All Facilities:")
        print(f"{'-' * 80}")

        for stat_type in StatType:
            stat_data = results["total"]["stats"][stat_type]
            print(f"  {stat_type.name.capitalize():10s}: {stat_data['total']:8.1f} total, {stat_data['mean']:6.2f} avg per turn")

        sp_data = results["total"]["skill_points"]
        print(f"  {'Skill Pts':10s}: {sp_data['total']:8.1f} total, {sp_data['mean']:6.2f} avg per turn")

        print(f"\n{'=' * 80}\n")
