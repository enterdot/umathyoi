"""Application-wide constants and configuration values."""

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
    

class CardConstants:
    """Constants related to cards and game mechanics."""
    MAX_LIMIT_BREAK = 4
    MIN_LIMIT_BREAK = 0
    LEVELS_PER_LIMIT_BREAK = 5
    R_MAX_LEVEL_AT_MIN_LIMIT_BREAK = 20
    SR_MAX_LEVEL_AT_MIN_LIMIT_BREAK = 25
    SSR_MAX_LEVEL_AT_MIN_LIMIT_BREAK = 30
    MIN_LEVEL = 1
    R_MAX_LEVEL = R_MAX_LEVEL_AT_MIN_LIMIT_BREAK + LEVELS_PER_LIMIT_BREAK * MAX_LIMIT_BREAK
    SR_MAX_LEVEL = SR_MAX_LEVEL_AT_MIN_LIMIT_BREAK + LEVELS_PER_LIMIT_BREAK * MAX_LIMIT_BREAK
    SSR_MAX_LEVEL = SSR_MAX_LEVEL_AT_MIN_LIMIT_BREAK + LEVELS_PER_LIMIT_BREAK * MAX_LIMIT_BREAK
    MILESTONE_LEVELS = [1, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50]
    DEFAULT_OWNED_COPIES = 3  # TODO: For testing


class DeckConstants:
    """Constants related to deck management."""
    DEFAULT_DECK_SIZE = 6
    DEFAULT_DECK_LIST_SIZE = 5
    MIN_DECK_SIZE = 1


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
    CSS_TRANSITION_DURATION = 150
    
    # Responsive breakpoints
    DEFAULT_BREAKPOINT_WIDTH = 848
    MIN_WINDOW_WIDTH = 560
    MIN_WINDOW_HEIGHT = 720
    DEFAULT_WINDOW_WIDTH = 1024
    DEFAULT_WINDOW_HEIGHT = 720


class NetworkConstants:
    """Constants for network operations."""
    IMAGE_TIMEOUT_SECONDS = 10
    IMAGE_BASE_URL = "https://gametora.com/images/umamusume/supports/tex_support_card_{card_id}.png"
    MAX_CONCURRENT_CONNECTIONS = 10
