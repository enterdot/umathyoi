"""Application-wide constants and configuration values."""

# TODO: Keep moving constants to relevant modules as class attributes


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


class NetworkConstants:
    """Constants for network operations."""

    IMAGE_TIMEOUT_SECONDS = 10
    IMAGE_BASE_URL = "https://gametora.com/images/umamusume/supports/tex_support_card_{card_id}.png"
    MAX_CONCURRENT_CONNECTIONS = 10
