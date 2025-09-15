import gi
gi.require_version('Gdk', '4.0')
from gi.repository import GdkPixbuf

import json
import aiohttp
from typing import Optional, Iterator

from .card import Rarity, CardType, Card


class CardDatabase:
    def __init__(self) -> None:
        self.cards: dict[int, Card] = {}
        self.image_cache: dict[int, GdkPixbuf.Pixbuf] = {}
        self.owned_copies: dict[int, int] = {}

        # TODO: load serialised data on owned cards:
        # Need to save 'card_id' and 'owned_copies'
        # (owned_copies - 1) -> limit_break
        # Once that's done, use the data in the next loop which sets
        # owned copies to 3 for all cards

        with open('cards.json') as f:
            cards_data = json.load(f)

        for card_data in cards_data:
            self.cards[card_data["id"]] = Card(
                id=card_data["id"],
                name=card_data["name"],
                view_name=card_data["view_name"],
                rarity=Rarity(card_data["rarity"]),
                type=CardType(card_data["type"]),
                limit_breaks={int(k): v for k, v in card_data["limit_breaks"].items()}
            )
            self.owned_copies[card_data["id"]] = 3

    def get_all_cards(self) -> Iterator[Card]:
        yield from self.cards.values()

    def get_card(self, card: Card) -> Optional[Card]:
        return self.get_card_by_id(card.id)

    def get_card_by_id(self, card_id: int) -> Optional[Card]:
        return self.cards.get(card_id)

    def get_cards_by_rarity(self, rarity: Rarity) -> Iterator[Card]:
        for card in self.cards.values():
            if card.rarity == rarity:
                yield card

    def get_cards_by_type(self, card_type: CardType) -> Iterator[Card]:
        for card in self.cards.values():
            if card.type == card_type:
                yield card

    def search_cards(self, name_query: str | None = None, rarity: Rarity | None = None, card_type: CardType | None = None, min_owned: int | None = None) -> Iterator[Card]:
        for card in self.cards.values():
            if name_query and (name_query.lower() not in card.name.lower() and name_query.lower() not in card.view_name.lower()):
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
        """Get the limit break level achievable with owned copies of a card."""
        owned = self.get_owned_copies(card_id)
        return max(0, owned - 1)

    async def load_card_image(self, card_id: int, width: int, height: int) -> Optional[GdkPixbuf.Pixbuf]:
        cache_key = card_id
        if cache_key in self.image_cache:
            cached_pixbuf = self.image_cache[cache_key]
            return cached_pixbuf.scale_simple(width, height, GdkPixbuf.InterpType.BILINEAR)

        url = f"https://gametora.com/images/umamusume/supports/tex_support_card_{card_id}.png"

        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        image_data = await response.read()
                        loader = GdkPixbuf.PixbufLoader()
                        loader.write(image_data)
                        loader.close()
                        pixbuf = loader.get_pixbuf()
                        if pixbuf:
                            self.image_cache[cache_key] = pixbuf
                            return pixbuf.scale_simple(width, height, GdkPixbuf.InterpType.BILINEAR)
        except Exception as e:
            print(f"Failed to load artwork for card {card_id}: {e}")

        return None  # caller handles fallback
