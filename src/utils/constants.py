"""Application-wide constants and configuration values."""


class CardConstants:
    """Constants related to cards and game mechanics."""
    MAX_LIMIT_BREAKS = 4
    MIN_LIMIT_BREAKS = 0
    DEFAULT_OWNED_COPIES = 3  # For testing


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
