# Quick script to find minimal card coverage
import json

with open('src/data/cards.json', 'r') as f:
    data = json.load(f)

# Collect all normal effect types
all_normal_effects = set()
normal_effects_by_card = {}

for card in data['data']:
    card_effects = set()
    for effect_array in card.get('effects', []):
        if len(effect_array) > 0:
            effect_type = effect_array[0]
            all_normal_effects.add(effect_type)
            card_effects.add(effect_type)
    
    if card_effects:
        normal_effects_by_card[card['support_id']] = {
            'name': card['char_name'],
            'effects': list(card_effects)
        }

# Collect all unique effect types  
all_unique_effects = set()
unique_effects_by_card = {}

for card in data['data']:
    if 'unique' in card and 'effects' in card['unique']:
        card_unique_effects = set()
        for effect in card['unique']['effects']:
            effect_type = effect['type']
            all_unique_effects.add(effect_type)
            card_unique_effects.add(effect_type)
        
        if card_unique_effects:
            unique_effects_by_card[card['support_id']] = {
                'name': card['char_name'],
                'effects': list(card_unique_effects)
            }

print(f"All normal effect types: {sorted(all_normal_effects)}")
print(f"All unique effect types: {sorted(all_unique_effects)}")

# Find cards with most coverage
normal_coverage = [(card_id, len(info['effects']), info) for card_id, info in normal_effects_by_card.items()]
normal_coverage.sort(key=lambda x: x[1], reverse=True)

print(f"\nTop 5 cards by normal effect coverage:")
for card_id, count, info in normal_coverage[:5]:
    print(f"  {info['name']} (ID: {card_id}): {count} effects - {info['effects']}")

unique_coverage = [(card_id, len(info['effects']), info) for card_id, info in unique_effects_by_card.items()]
unique_coverage.sort(key=lambda x: x[1], reverse=True)

print(f"\nTop 5 cards by unique effect coverage:")
for card_id, count, info in unique_coverage[:5]:
    print(f"  {info['name']} (ID: {card_id}): {count} effects - {info['effects']}")
