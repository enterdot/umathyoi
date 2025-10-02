#!/usr/bin/env python3
"""Test script."""

# TODO: turn into a more comprehensive set of tests

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from modules import (
    CardDatabase,
    ScenarioDatabase,
    CardEffect,
    Rarity,
    Deck,
    EfficiencyCalculator,
    Mood,
    GenericCharacter,
    StatType,
    Aptitude
)

print("Loading databases...")
card_db = CardDatabase('data/cards.json')
#char_db = CharacterDatabase()
scenario_db = ScenarioDatabase()

def test_card_effects():
    """Test Card effects interpolation system."""
    
    # Find the Special Week SSR Speed card (should be ID 30086 or similar)
    special_week = None
    for card in card_db.cards.values():
        if "special" in card.view_name.lower() and card.rarity.value == 3:
            special_week = card
            break
    
    if not special_week:
        print("Could not find Special Week SSR card")
        return
    
    print(f"Testing card: {special_week.view_name} (ID: {special_week.id})")
    print(f"Effects arrays: {len(special_week.effects)} effects")
    
    # Test interpolation at various levels
    test_levels = [1, 10, 20, 30, 40, 50]
    
    print("\nFriendship training effectiveness progression:")
    for level in test_levels:
        bonus = special_week.get_effect_at_level(CardEffect.friendship_effectiveness, level)
        print(f"  Level {level:2d}: {bonus}%")
    
    print("\nSpeed Bonus progression:")
    for level in test_levels:
        bonus = special_week.get_effect_at_level(CardEffect.speed_stat_bonus, level)
        print(f"  Level {level:2d}: +{bonus}")
    
    print("\nAll effects at level 50:")
    all_effects = special_week.get_all_effects_at_level(50)
    for effect_name, value in all_effects.items():
        print(f"  {effect_name}: {value}")
    
    # Test LRU cache performance
    print("\nTesting LRU cache performance...")
    import time
    
    # First call (cache miss)
    start_time = time.time()
    for _ in range(1000):
        special_week.get_effect_at_level(CardEffect.friendship_effectiveness, 25)
    first_time = time.time() - start_time
    
    # Second call (cache hit) 
    start_time = time.time()
    for _ in range(1000):
        special_week.get_effect_at_level(CardEffect.friendship_effectiveness, 25)
    second_time = time.time() - start_time
    
    print(f"First 1000 calls (cache miss): {first_time:.4f}s")
    print(f"Second 1000 calls (cache hit): {second_time:.4f}s")
    print(f"Speedup: {first_time / second_time:.1f}x")



def test_efficiency_calculator():
    print("\n" + "="*80)
    print("Testing Efficiency Calculator")
    print("="*80)
    
    # Create a simple test deck
    print("\nCreating test deck...")
    cards = []
    
    # Try to get 6 SSR cards of different types
    ssr_cards = [c for c in card_db.cards.values() if c.rarity == Rarity.SSR]
    if len(ssr_cards) >= 6:
        cards = ssr_cards[:6]
    else:
        # Fallback: just use first 6 cards
        cards = list(card_db.cards.values())[:6]
    
    deck = Deck(name="Test Deck", cards=cards)
    print(f"Deck created with cards: {[c.name for c in cards]}")
    
    # Get first scenario
    scenario = scenario_db.scenarios[0]
    print(f"Using scenario: {scenario.name}")
    
    # Create a generic test character with balanced stat growth
    from modules import GenericCharacter, StatType, Aptitude
    character = GenericCharacter(
        stat_growth={
            StatType.speed: 10,
            StatType.stamina: 0,
            StatType.power: 10,
            StatType.guts: 0,
            StatType.wit: 10,
        },
        track_aptitude=Aptitude.A,
        distance_aptitude=Aptitude.A,
        style_aptitude=Aptitude.A
    )
    print(f"Created test character with stat growth: {character.stat_growth}")
    
    # Create calculator
    print("\nInitializing calculator...")
    calculator = EfficiencyCalculator(
        deck=deck,
        scenario=scenario,
        character=character
    )
    
    # Set test parameters
    calculator.energy = 80
    calculator.max_energy = 120
    calculator.mood = Mood.good
    calculator.fan_count = 50000
    calculator.turn_count = 100  # Fewer turns for quick test
    
    # Hook up event handlers to see progress
    def on_started(calc):
        print("\nCalculation started...")
    
    def on_progress(calc, current, total):
        if current % 10 == 0:
            print(f"Progress: {current}/{total} turns...")
    
    def on_finished(calc, results):
        print("Calculation finished!")
    
    calculator.calculation_started.subscribe(on_started)
    calculator.calculation_progress.subscribe(on_progress)
    calculator.calculation_finished.subscribe(on_finished)
    
    # Trigger calculation (should happen automatically due to init, but let's be explicit)
    print("\nRunning calculation...")
    calculator.recalculate()
    
    # Print results
    calculator.print_results()


if __name__ == "__main__":
    test_card_effects()
    test_efficiency_calculator()
