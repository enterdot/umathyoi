#!/usr/bin/env python3
"""Test script."""

# TODO: turn into a more comprehensive set of tests

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from modules import CardDatabase, CardEffect

def test_card_effects():
    """Test Card effects interpolation system."""
    print("Loading card database...")
    card_db = CardDatabase('data/cards.json')
    
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
    
    # Show cache info
    print(f"\nLRU Cache stats: {special_week._interpolate_effect_value.cache_info()}")

if __name__ == "__main__":
    test_card_effects()
