"""Application-wide constants and configuration values."""

# TODO: Keep moving constants to relevant modules as class attributes


class ApplicationConstants:
    """Constants related to the application itself."""

    CACHE_NAME = "umathyoi"


class NetworkConstants:
    """Constants for network operations."""

    IMAGE_TIMEOUT_SECONDS = 10
    IMAGE_BASE_URL = "https://gametora.com/images/umamusume/supports/tex_support_card_{card_id}.png"
    MAX_CONCURRENT_CONNECTIONS = 10
