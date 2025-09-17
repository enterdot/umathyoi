import gi
gi.require_version('Gdk', '4.0')
from gi.repository import GdkPixbuf

import json
import aiohttp
from typing import Optional, Iterator
from pathlib import Path

from .card import Rarity, CardType, Card


class CardDatabase:
    """Database for managing card data, images, and ownership information."""
    
    def __init__(self, cards_file: str = 'cards.json') -> None:
        """Initialize card database.
        
        Args:
            cards_file: Path to JSON file containing card data
        """
        self.cards: dict[int, Card] = {}
        self.image_cache: dict[int, GdkPixbuf.Pixbuf] = {}
        self.owned_copies: dict[int, int] = {}
        
        self._load_cards_from_file(cards_file)
        self._load_ownership_data()

    def _load_cards_from_file(self, cards_file: str) -> None:
        """Load card data from JSON file.
        
        Args:
            cards_file: Path to JSON file containing card definitions
            
        Raises:
            FileNotFoundError: If cards file doesn't exist
            ValueError: If cards file contains invalid data
        """
        try:
            with open(cards_file, 'r', encoding='utf-8') as f:
                cards_data = json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Cards file not found: {cards_file}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in cards file: {e}")

        for card_data in cards_data:
            try:
                self.cards[card_data["id"]] = Card(
                    id=card_data["id"],
                    name=card_data["name"],
                    view_name=card_data["view_name"],
                    rarity=Rarity(card_data["rarity"]),
                    type=CardType(card_data["type"]),
                    limit_breaks={int(k): v for k, v in card_data["limit_breaks"].items()}
                )
            except (KeyError, ValueError) as e:
                print(f"Warning: Skipping invalid card data for ID {card_data.get('id', 'unknown')}: {e}")

    def _load_ownership_data(self) -> None:
        """Load card ownership data from persistent storage.
        
        Note:
            Currently sets all cards to 3 copies for testing.
            Should be replaced with actual persistence when implemented.
        """
        # TODO: Load serialized ownership data from file
        # Format should be: {'card_id': owned_copies, ...}
        # where (owned_copies - 1) = max achievable limit break
        
        # Temporary: Set all cards to 3 copies for testing
        for card_id in self.cards:
            self.owned_copies[card_id] = 3

    def get_all_cards(self) -> Iterator[Card]:
        """Get iterator over all cards in database.
        
        Yields:
            Card instances in the database
        """
        yield from self.cards.values()

    def get_card(self, card: Card) -> Card | None:
        """Get card by Card instance.
        
        Args:
            card: Card instance to look up
            
        Returns:
            Card from database, or None if not found
        """
        return self.get_card_by_id(card.id)

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
        """Load and cache card artwork from remote server.
        
        Args:
            card_id: Card identifier
            width: Desired image width in pixels
            height: Desired image height in pixels
            
        Returns:
            Scaled pixbuf, or None if loading failed
        """
        # Check cache first
        cache_key = card_id
        if cache_key in self.image_cache:
            cached_pixbuf = self.image_cache[cache_key]
            return cached_pixbuf.scale_simple(width, height, GdkPixbuf.InterpType.BILINEAR)

        # Download image from remote server
        url = f"https://gametora.com/images/umamusume/supports/tex_support_card_{card_id}.png"

        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        image_data = await response.read()
                        pixbuf = self._create_pixbuf_from_data(image_data)
                        if pixbuf:
                            self.image_cache[cache_key] = pixbuf
                            return pixbuf.scale_simple(width, height, GdkPixbuf.InterpType.BILINEAR)
                    else:
                        print(f"HTTP {response.status} when loading artwork for card {card_id}")
        except aiohttp.ClientError as e:
            print(f"Network error loading artwork for card {card_id}: {e}")
        except Exception as e:
            print(f"Unexpected error loading artwork for card {card_id}: {e}")

        return None  # Caller handles fallback

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
            print(f"Error creating pixbuf from image data: {e}")
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
            print(f"Would save ownership data to: {file_path}")
        else:
            print("Would save ownership data to default location")
        return True
