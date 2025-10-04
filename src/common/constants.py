"""Application-wide constants and configuration values."""

#TODO: Keep moving constants to relevant modules

class ApplicationConstants:
    """Constants related to the application itself."""

    NAME = "Umathyoi"
    VERSION = "0.0"
    REVERSE_DNS = "org.example.umathyoi"
    CACHE_NAME = "umathyoi"
    CARD_ARTWORK_CACHE_NAME = "card_artwork"
    CARDS_JSON = "data/cards.json"
    CHARACTERS_JSON = "data/characters.json"
    SKILLS_JSON = "data/skills.json"
    SCENARIOS_JSON = "data/scenarios.json"


class GameplayConstants:
    """Constants related to general gameplay"""

    MIN_FACILITY_LEVEL = 1
    MAX_FACILITY_LEVEL = 5
    PREFERRED_FACILITY_BASE_WEIGHT = 100
    NON_APPEARANCE_BASE_WEIGHT = 50
    PERCENTAGE_BASE = 100


class CharacterConstants:
    """Constants related to characters."""

    MAX_TOTAL_STAT_GROWTH = 30  # 30%


class UIConstants:
    """Constants for UI dimensions and spacing."""

    # Card artwork dimensions
    CARD_THUMBNAIL_WIDTH = 45
    CARD_THUMBNAIL_HEIGHT = 60
    CARD_SLOT_WIDTH = 150
    CARD_SLOT_HEIGHT = 200
    STATS_ARTWORK_SCALE = 3  # Multiplier for stats view artwork

    # Spacing and margins
    CARD_LIST_MARGIN = 18
    CARD_LIST_PADDING_VERTICAL = 12
    DECK_GRID_SPACING = 24
    CAROUSEL_MIN_SPACING = 30
    CAROUSEL_SPACING = 20
    CAROUSEL_MARGIN = 30
    DECK_EFFICIENCY_MARGIN_BOTTOM = 40

    # Animation durations (in milliseconds)
    CAROUSEL_REVEAL_DURATION = 200


class NetworkConstants:
    """Constants for network operations."""

    IMAGE_TIMEOUT_SECONDS = 10
    IMAGE_BASE_URL = "https://gametora.com/images/umamusume/supports/tex_support_card_{card_id}.png"
    MAX_CONCURRENT_CONNECTIONS = 10
