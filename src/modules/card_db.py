import logging
logger = logging.getLogger(__name__)

import gi
gi.require_version('Gdk', '4.0')
from gi.repository import GdkPixbuf, GLib

import json
import requests  # Replace aiohttp with requests
import threading
from typing import Iterator
from pathlib import Path
from platformdirs import user_cache_dir

from .card import CardRarity, CardType, Card
from utils import ApplicationConstants, CardConstants, NetworkConstants, auto_title_from_instance, stopwatch


class CardDatabase:
    """Database for managing card data, images, and ownership information."""
    
    @stopwatch(show_args=False)
    def __init__(self, cards_file: str = ApplicationConstants.CARDS_JSON) -> None:
        """Initialize card database.
        
        Args:
            cards_file: Path to JSON file containing card data
        """
        self.cards: dict[int, Card] = {}
        self.image_cache: dict[int, GdkPixbuf.Pixbuf] = {}
        self.owned_copies: dict[int, int] = {}
        
        # Thread-safe lock for cache access
        self._cache_lock = threading.Lock()
        
        # Shared requests session for connection pooling
        self._session = requests.Session()
        self._session.headers.update({
            'User-Agent': f'{ApplicationConstants.NAME}/{ApplicationConstants.VERSION}'
        })
        # Configure connection pooling
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=20,
            pool_maxsize=20,
            max_retries=3
        )
        self._session.mount('http://', adapter)
        self._session.mount('https://', adapter)
        
        # Setup disk cache directory
        self._cache_dir = Path(user_cache_dir(ApplicationConstants.CACHE_NAME)) / ApplicationConstants.CARD_ARTWORK_CACHE_NAME
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Card artwork cache directory: {self._cache_dir}")
        
        try:
            self._load_cards_from_file(cards_file)
        except Exception as e:
            logger.error(f"Could not load cards from {cards_file}: {e}")
            import sys
            sys.exit(1)
        self._load_ownership_data()
        
        logger.debug(f"{auto_title_from_instance(self)} initialized")

    @property
    def count(self) -> int:
        return len(self.cards)

    def _load_cards_from_file(self, cards_file: str) -> None:
        """Load card data from JSON file."""
        try:
            with open(cards_file, 'r', encoding='utf-8') as f:
                file_data = json.load(f)
                logger.info(f"Loaded card data from {f.name}")
        except FileNotFoundError:
            raise FileNotFoundError(f"Cards file {cards_file} not found.")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in cards file: {e}")

        cards_data = file_data['data']
        metadata = file_data.get('metadata', {})

        logger.info(f"Loading data: {metadata.get('record_count', len(cards_data))} cards")
        if 'scraped_at' in metadata:
            logger.info(f"Data scraped at: {metadata['scraped_at']}")

        self._load_cards(cards_data)
        logger.info(f"Loaded data for {self.count} cards")

    def _load_cards(self, cards_data: list) -> None:
        """Load cards, keep compact arrays for effects."""
        for card_data in cards_data:
            try:
                card_id = card_data["support_id"]
                self.cards[card_id] = Card(
                    id=card_id,
                    name=card_data["url_name"],
                    view_name=GLib.markup_escape_text(card_data["char_name"]),
                    rarity=CardRarity(card_data["rarity"]),
                    type=self._map_name_to_card_type(card_data["type"]),
                    effects=card_data.get("effects", []),
                    unique_effects=card_data.get("unique", {}).get("effects", []),
                    unique_effects_unlock_level=card_data.get("unique", {}).get("level", 0)
                )
                logger.debug(f"Card {card_id} added to database")
            except (KeyError, ValueError) as e:
                logger.warning(f"Skipping invalid data for card {card_data.get('support_id', 'unknown')}: {e}")

    def _map_name_to_card_type(self, name: str) -> CardType:
        """Map type name to CardType enum."""
        type_mapping = {
            'speed': CardType.speed,
            'stamina': CardType.stamina,
            'power': CardType.power,
            'guts': CardType.guts,
            'intelligence': CardType.wit,
            'friend': CardType.pal
        }
        return type_mapping.get(name)

    def _load_ownership_data(self) -> None:
        """Load card ownership data from persistent storage."""
        # TODO: Load serialized ownership data from file
        for card_id in self.cards:
            self.owned_copies[card_id] = CardConstants.DEFAULT_OWNED_COPIES

    def get_card_by_id(self, card_id: int) -> Card | None:
        """Get card by ID."""
        return self.cards.get(card_id)

    def get_cards_by_rarity(self, rarity: CardRarity) -> Iterator[Card]:
        """Get all cards of specified rarity."""
        for card in self.cards.values():
            if card.rarity == rarity:
                yield card

    def get_cards_by_type(self, card_type: CardType) -> Iterator[Card]:
        """Get all cards of specified type."""
        for card in self.cards.values():
            if card.type == card_type:
                yield card

    def search_cards(self, name_query: str | None = None, rarity: CardRarity | None = None, 
                    card_type: CardType | None = None, min_owned: int | None = None) -> Iterator[Card]:
        """Search cards with multiple filter criteria."""
        for card in self.cards.values():
            if name_query and (name_query.lower() not in card.name.lower() and 
                              name_query.lower() not in card.view_name.lower()):
                continue
            if rarity and card.rarity != rarity:
                continue
            if card_type and card.type != card_type:
                continue
            if min_owned and self.owned_copies[card.id] < min_owned:
                continue
            yield card

    def get_owned_copies(self, card_id: int) -> int:
        """Get the number of owned copies for a card."""
        return self.owned_copies.get(card_id, 0)

    def set_owned_copies(self, card_id: int, copies: int) -> None:
        """Set the number of owned copies for a card."""
        if copies < 0:
            copies = 0
        self.owned_copies[card_id] = copies

    def get_owned_limit_break(self, card_id: int) -> int:
        """Get the maximum limit break level achievable with owned copies."""
        owned = self.get_owned_copies(card_id)
        return max(0, owned - 1)

    def load_card_image_async(self, card_id: int, width: int, height: int, 
                              callback: callable) -> None:
        """Load and cache card artwork asynchronously.
        
        This method returns immediately and calls the callback with the result
        when loading completes. The callback is called on GTK's main thread.
        
        Args:
            card_id: Card identifier
            width: Desired image width in pixels
            height: Desired image height in pixels
            callback: Function to call with result: callback(pixbuf: GdkPixbuf.Pixbuf | None)
        """
        def load_in_thread():
            """This runs in a background thread."""
            try:
                pixbuf = self._load_card_image_sync(card_id, width, height)
                callback(pixbuf)
            except Exception as e:
                logger.error(f"Error loading image for card {card_id}: {e}")
                callback(None)
        
        # Start background thread
        thread = threading.Thread(target=load_in_thread, daemon=True)
        thread.start()

    @stopwatch(show_args=False)
    def _load_card_image_sync(self, card_id: int, width: int, height: int) -> GdkPixbuf.Pixbuf | None:
        """Synchronous internal method to load card image.
        
        This method does the actual work and can be called from any thread.
        """
        # Check memory cache first (thread-safe read)
        with self._cache_lock:
            if card_id in self.image_cache:
                cached_pixbuf = self.image_cache[card_id]
                return cached_pixbuf.scale_simple(width, height, GdkPixbuf.InterpType.BILINEAR)

        # Check disk cache
        disk_pixbuf = self._load_from_disk_cache(card_id)
        if disk_pixbuf:
            with self._cache_lock:
                self.image_cache[card_id] = disk_pixbuf
            logger.debug(f"Loaded card {card_id} from disk cache")
            return disk_pixbuf.scale_simple(width, height, GdkPixbuf.InterpType.BILINEAR)

        # Download from internet as fallback
        downloaded_pixbuf = self._download_and_cache_image(card_id)
        if downloaded_pixbuf:
            with self._cache_lock:
                self.image_cache[card_id] = downloaded_pixbuf
            return downloaded_pixbuf.scale_simple(width, height, GdkPixbuf.InterpType.BILINEAR)

        logger.error(f"Could not load image data for card {card_id}")
        return None

    def _create_pixbuf_from_data(self, image_data: bytes) -> GdkPixbuf.Pixbuf | None:
        """Create GdkPixbuf from image data bytes."""
        try:
            loader = GdkPixbuf.PixbufLoader()
            loader.write(image_data)
            loader.close()
            return loader.get_pixbuf()
        except Exception as e:
            logger.error(f"Could not create buffer from image data: {e}")
            return None

    def save_ownership_data(self, file_path: str | None = None) -> bool:
        """Save card ownership data to persistent storage."""
        # TODO: Implement actual persistence
        if file_path:
            logger.debug(f"Would save ownership data to: {file_path}")
        else:
            logger.debug("Would save ownership data to default location")
        return True

    def get_cache_info(self) -> dict:
        """Get information about the disk cache."""
        try:
            cache_files = list(self._cache_dir.glob("*.png"))
            total_size = sum(f.stat().st_size for f in cache_files)
            
            return {
                "cache_dir": str(self._cache_dir),
                "cached_cards": len(cache_files),
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "total_cards": self.count
            }
        except Exception as e:
            logger.error(f"Error getting cache info: {e}")
            return {"error": str(e)}

    def clear_cache(self) -> bool:
        """Clear the disk cache."""
        try:
            import shutil
            if self._cache_dir.exists():
                shutil.rmtree(self._cache_dir)
                self._cache_dir.mkdir(parents=True, exist_ok=True)
                # Clear memory cache too
                with self._cache_lock:
                    self.image_cache.clear()
                logger.info("Disk cache cleared")
                return True
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return False

    def __iter__(self) -> Iterator[Card]:
        """Iterate over all cards in database."""
        yield from self.cards.values()

    def _get_cache_file_path(self, card_id: int) -> Path:
        """Get the disk cache file path for a card."""
        return self._cache_dir / f"{card_id}.png"

    def _load_from_disk_cache(self, card_id: int) -> GdkPixbuf.Pixbuf | None:
        """Load card image from disk cache."""
        cache_file = self._get_cache_file_path(card_id)
        
        if not cache_file.exists():
            return None
        
        try:
            image_data = cache_file.read_bytes()
            return self._create_pixbuf_from_data(image_data)
        except Exception as e:
            logger.warning(f"Failed to load cached image for card {card_id}: {e}")
            try:
                cache_file.unlink()
            except:
                pass
            return None

    def _download_and_cache_image(self, card_id: int) -> GdkPixbuf.Pixbuf | None:
        """Download card image and save to disk cache."""
        url = NetworkConstants.IMAGE_BASE_URL.format(card_id=card_id)
        logger.debug(f"Downloading image for card {card_id}")

        try:
            response = self._session.get(
                url, 
                timeout=NetworkConstants.IMAGE_TIMEOUT_SECONDS
            )
            
            if response.status_code == 200:
                image_data = response.content
                logger.debug(f"Downloaded image for card {card_id}: {len(image_data)} bytes")
                
                # Save to disk cache
                cache_file = self._get_cache_file_path(card_id)
                try:
                    cache_file.write_bytes(image_data)
                    logger.debug(f"Cached image for card {card_id} to {cache_file}")
                except Exception as e:
                    logger.warning(f"Failed to save image cache for card {card_id}: {e}")
                
                # Create pixbuf
                return self._create_pixbuf_from_data(image_data)
            else:
                logger.warning(f"HTTP {response.status_code} when downloading artwork for card {card_id}")
                
        except requests.RequestException as e:
            logger.warning(f"Network error downloading artwork for card {card_id}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error downloading artwork for card {card_id}: {e}")

        return None

    def __del__(self):
        """Cleanup when database is destroyed."""
        try:
            self._session.close()
        except:
            pass
