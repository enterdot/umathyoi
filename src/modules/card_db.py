import logging
logger = logging.getLogger(__name__)

import gi
gi.require_version('Gdk', '4.0')
from gi.repository import GdkPixbuf

import json
import aiohttp
import asyncio
from typing import Iterator
from pathlib import Path
import hashlib
from platformdirs import user_cache_dir

from .card import Rarity, CardType, Card
from utils import ApplicationConstants, CardConstants, NetworkConstants, auto_title_from_instance


class CardDatabase:
    """Database for managing card data, images, and ownership information."""
    
    def __init__(self, cards_file: str = ApplicationConstants.CARDS_JSON) -> None:
        """Initialize card database.
        
        Args:
            cards_file: Path to JSON file containing card data
        """
        self.cards: dict[int, Card] = {}
        self.image_cache: dict[int, GdkPixbuf.Pixbuf] = {}
        self.owned_copies: dict[int, int] = {}
        
        # Shared HTTP session and semaphore for connection limiting
        self._session: aiohttp.ClientSession | None = None
        self._connection_semaphore = asyncio.Semaphore(NetworkConstants.MAX_CONCURRENT_CONNECTIONS)
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

    async def __aenter__(self):
        """Async context manager entry."""
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self._close_session()

    async def _ensure_session(self) -> None:
        """Ensure HTTP session is created."""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=NetworkConstants.IMAGE_TIMEOUT_SECONDS)
            connector = aiohttp.TCPConnector(
                limit=20,  # Total connection pool size
                limit_per_host=10,  # Max connections per host
                ttl_dns_cache=300,  # DNS cache TTL
                use_dns_cache=True,
            )
            self._session = aiohttp.ClientSession(
                timeout=timeout,
                connector=connector
            )

    async def _close_session(self) -> None:
        """Close HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

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
                card_id=card_data["support_id"]
                self.cards[card_id] = Card(
                    id=card_id,
                    name=card_data["url_name"],
                    view_name=card_data["char_name"],
                    rarity=Rarity(card_data["rarity"]),
                    type=self._map_name_to_card_type(card_data["type"]),
                    effects=card_data.get("effects", []),
                    unique_effects=card_data.get("unique", {}).get("effects", []),
                    unique_effects_unlock_level=card_data.get("unique", {}).get("level", 0)
                )
                logger.debug(f"Card {card_id} added to database")
                
            except (KeyError, ValueError) as e:
                logger.warning(f"Skipping invalid data for card {card_data.get('support_id', 'unknown')}: {e}")

    def _map_name_to_card_type(self, name: str) -> CardType:
        """Map type name to CardType enum.
        
        Args:
            name: Type name
            
        Returns:
            Corresponding CardType enum value
        """
        type_mapping = {
            'speed': CardType.speed,
            'stamina': CardType.stamina,
            'power': CardType.power,
            'guts': CardType.guts,
            'intelligence': CardType.wit,
            'friend': CardType.pal
        }
        return type_mapping.get(name, CardType.pal)  # Default to PAL for unknown types #TODO: raise RuntimeException instead

    def _load_ownership_data(self) -> None:
        """Load card ownership data from persistent storage.
        
        Note:
            Currently sets all cards to 3 copies for testing.
            Should be replaced with actual persistence when implemented.
        """
        # TODO: Load serialized ownership data from file
        # Format should be: {'card_id': owned_copies, ...}
        # where (owned_copies - 1) = max achievable limit break
        
        # Temporary: Set all cards to default copies for testing
        for card_id in self.cards:
            self.owned_copies[card_id] = CardConstants.DEFAULT_OWNED_COPIES

    def get_card_by_id(self, card_id: int) -> Card | None:
        """Get card by ID.
        
        Args:
            card_id: Unique card identifier
            
        Returns:
            Card instance, or None if not found
        """
        return self.cards.get(card_id)

    def get_cards_by_rarity(self, rarity: Rarity) -> Iterator[Card]:
        """Get all cards of specified rarity.
        
        Args:
            rarity: Card rarity to filter by
            
        Yields:
            Cards matching the specified rarity
        """
        for card in self.cards.values():
            if card.rarity == rarity:
                yield card

    def get_cards_by_type(self, card_type: CardType) -> Iterator[Card]:
        """Get all cards of specified type.
        
        Args:
            card_type: Card type to filter by
            
        Yields:
            Cards matching the specified type
        """
        for card in self.cards.values():
            if card.type == card_type:
                yield card

    def search_cards(self, name_query: str | None = None, rarity: Rarity | None = None, 
                    card_type: CardType | None = None, min_owned: int | None = None) -> Iterator[Card]:
        """Search cards with multiple filter criteria.
        
        Args:
            name_query: Partial name to search for (case insensitive)
            rarity: Filter by card rarity
            card_type: Filter by card type
            min_owned: Minimum number of owned copies
            
        Yields:
            Cards matching all specified criteria
        """
        for card in self.cards.values():
            # Name filter
            if name_query and (name_query.lower() not in card.name.lower() and 
                              name_query.lower() not in card.view_name.lower()):
                continue
                
            # Rarity filter
            if rarity and card.rarity != rarity:
                continue
                
            # Type filter
            if card_type and card.type != card_type:
                continue
                
            # Ownership filter
            if min_owned and self.owned_copies[card.id] < min_owned:
                continue
                
            yield card

    def get_owned_copies(self, card_id: int) -> int:
        """Get the number of owned copies for a card.
        
        Args:
            card_id: Card identifier
            
        Returns:
            Number of owned copies (0 if card not found)
        """
        return self.owned_copies.get(card_id, 0)

    def set_owned_copies(self, card_id: int, copies: int) -> None:
        """Set the number of owned copies for a card.
        
        Args:
            card_id: Card identifier
            copies: Number of copies (minimum 0)
        """
        if copies < 0:
            copies = 0
        self.owned_copies[card_id] = copies

    def get_owned_limit_break(self, card_id: int) -> int:
        """Get the maximum limit break level achievable with owned copies.
        
        Args:
            card_id: Card identifier
            
        Returns:
            Maximum limit break level (0-4)
        """
        owned = self.get_owned_copies(card_id)
        return max(0, owned - 1)

    async def load_card_image(self, card_id: int, width: int, height: int) -> GdkPixbuf.Pixbuf | None:
        """Load and cache card artwork from remote server or disk cache.
        
        Args:
            card_id: Card identifier
            width: Desired image width in pixels
            height: Desired image height in pixels
            
        Returns:
            Scaled pixbuf, or None if loading failed
        """
        # Check memory cache first
        cache_key = card_id
        if cache_key in self.image_cache:
            cached_pixbuf = self.image_cache[cache_key]
            return cached_pixbuf.scale_simple(width, height, GdkPixbuf.InterpType.BILINEAR)

        # Check disk cache
        disk_pixbuf = await self._load_from_disk_cache(card_id)
        if disk_pixbuf:
            self.image_cache[cache_key] = disk_pixbuf
            logger.debug(f"Loaded card {card_id} from disk cache")
            return disk_pixbuf.scale_simple(width, height, GdkPixbuf.InterpType.BILINEAR)

        # Download from internet as fallback
        downloaded_pixbuf = await self._download_and_cache_image(card_id)
        if downloaded_pixbuf:
            self.image_cache[cache_key] = downloaded_pixbuf
            return downloaded_pixbuf.scale_simple(width, height, GdkPixbuf.InterpType.BILINEAR)

        logger.error(f"Could not load image data for card {card_id}")
        return None

    def _create_pixbuf_from_data(self, image_data: bytes) -> GdkPixbuf.Pixbuf | None:
        """Create GdkPixbuf from image data bytes.
        
        Args:
            image_data: Raw image data
            
        Returns:
            Pixbuf instance, or None if creation failed
        """
        try:
            loader = GdkPixbuf.PixbufLoader()
            loader.write(image_data)
            loader.close()
            return loader.get_pixbuf()
        except Exception as e:
            logger.error(f"Could not create buffer from image data: {e}")
            return None

    def save_ownership_data(self, file_path: str | None = None) -> bool:
        """Save card ownership data to persistent storage.
        
        Args:
            file_path: Optional custom file path for saving
            
        Returns:
            True if save was successful, False otherwise
            
        Note:
            Implementation pending - currently just returns True
        """
        # TODO: Implement actual persistence
        # Should save self.owned_copies to JSON file
        if file_path:
            logger.debug(f"Would save ownership data to: {file_path}")
        else:
            logger.debug("Would save ownership data to default location")
        return True

    def get_cache_info(self) -> dict:
        """Get information about the disk cache.
        
        Returns:
            Dictionary with cache statistics
        """
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
        """Clear the disk cache.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            import shutil
            if self._cache_dir.exists():
                shutil.rmtree(self._cache_dir)
                self._cache_dir.mkdir(parents=True, exist_ok=True)
                logger.info("Disk cache cleared")
                return True
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return False


    def __iter__(self) -> Iterator[Card]:
        """Iterate over all cards in database.
        
        Yields:
            Card instances in the database
        """
        yield from self.cards.values()

    def _get_cache_file_path(self, card_id: int) -> Path:
        """Get the disk cache file path for a card.
        
        Args:
            card_id: Card identifier
            
        Returns:
            Path to cached image file
        """
        return self._cache_dir / f"{card_id}.png"

    async def _load_from_disk_cache(self, card_id: int) -> GdkPixbuf.Pixbuf | None:
        """Load card image from disk cache.
        
        Args:
            card_id: Card identifier
            
        Returns:
            Pixbuf from cache, or None if not cached
        """
        cache_file = self._get_cache_file_path(card_id)
        
        if not cache_file.exists():
            return None
        
        try:
            # Load image data from disk
            image_data = cache_file.read_bytes()
            return self._create_pixbuf_from_data(image_data)
        except Exception as e:
            logger.warning(f"Failed to load cached image for card {card_id}: {e}")
            # Remove corrupted cache file
            try:
                cache_file.unlink()
            except:
                pass
            return None

    async def _download_and_cache_image(self, card_id: int) -> GdkPixbuf.Pixbuf | None:
        """Download card image and save to disk cache.
        
        Args:
            card_id: Card identifier
            
        Returns:
            Downloaded pixbuf, or None if download failed
        """
        # Ensure session exists
        await self._ensure_session()
        
        # Use semaphore to limit concurrent connections
        async with self._connection_semaphore:
            url = NetworkConstants.IMAGE_BASE_URL.format(card_id=card_id)
            logger.debug(f"Downloading image for card {card_id}")

            try:
                async with self._session.get(url) as response:
                    if response.status == 200:
                        image_data = await response.read()
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
                        logger.warning(f"HTTP {response.status} when downloading artwork for card {card_id}")
            except aiohttp.ClientError as e:
                logger.warning(f"Network error downloading artwork for card {card_id}: {e}")
            except Exception as e:
                logger.error(f"Unexpected error downloading artwork for card {card_id}: {e}")

        return None

    def __del__(self):
        """Cleanup when database is destroyed."""
        if self._session and not self._session.closed:
            # Can't await in __del__, so we schedule the cleanup
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(self._close_session())
            except:
                pass  # Ignore errors during cleanup
