#!/usr/bin/env python

"""
Generate a template JSON file for support card taglines.
Creates entries for all SSR and SR cards with a placeholder tagline.
"""
from common import setup_logging, get_logger
from pathlib import Path

setup_logging("info")
logger = get_logger(Path(__file__).name)

import json
from datetime import datetime


def generate_tagline_template():
    """Generate tagline template from cards.json"""

    # Read the cards.json file
    cards_file = Path("data/cards.json")
    with open(cards_file, "r", encoding="utf-8") as f:
        cards_data = json.load(f)

    # Read existing taglines if file exists
    output_file = Path("data/card_taglines.json")
    existing_taglines = {}
    if output_file.exists():
        with open(output_file, "r", encoding="utf-8") as f:
            existing_data = json.load(f)
            existing_taglines = existing_data.get("data", {})
        logger.debug(f"Loaded {len(existing_taglines)} existing taglines")

    # Filter for SR (rarity=2) and SSR (rarity=3) cards with release field
    filtered_cards = [
        card
        for card in cards_data["data"]
        if card["rarity"] in [2, 3] and card.get("release")
    ]

    logger.debug(f"Total cards: {len(cards_data['data'])}")
    logger.debug(f"Released SSR and SR cards: {len(filtered_cards)}")

    # Create tagline mapping, preserving existing non-TODO entries
    tagline_mapping = {}
    new_entries = 0
    preserved_entries = 0

    for card in filtered_cards:
        support_id = str(card["id"])

        # Check if we already have a tagline for this card
        if support_id in existing_taglines:
            existing_value = existing_taglines[support_id]
            # If it's not a TODO placeholder, preserve it
            if not existing_value.startswith("TODO:"):
                tagline_mapping[support_id] = existing_value
                preserved_entries += 1
                continue

        # Add placeholder with character name for easier manual update
        char_name = card.get("character_name", "Unknown")
        rarity = "SSR" if card["rarity"] == 3 else "SR"
        card_type = card.get("type", "unknown")
        tagline_mapping[support_id] = (
            f"TODO: {char_name} ({rarity} {card_type})"
        )
        new_entries += 1

    # Sort by support_id for easier navigation
    sorted_mapping = dict(
        sorted(tagline_mapping.items(), key=lambda x: int(x[0]))
    )

    # Create output structure
    output = {
        "metadata": {
            "updated_at": datetime.now().strftime("%Y-%m-%d"),
            "description": "Support card taglines for SSR and SR cards. R cards all use 'Tracen Academy'.",
        },
        "data": sorted_mapping,
    }

    # Write to file
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    logger.info(f"Preserved {preserved_entries} manually updated taglines")
    logger.info(f"Added or kept {new_entries} placeholder taglines")
    logger.debug(f"Saved to: {output_file}")


if __name__ == "__main__":
    generate_tagline_template()
