import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk

from modules.card import Card
from modules.deck import Deck
from .card_artwork import CardArtwork
from utils import auto_title_from_instance


class CardSlot(Gtk.Box):
    """Widget representing a single card slot in a deck with artwork and limit break selector."""
    
    def __init__(self, card: Card | None = None, limit_break: int = 0, width: int = 164, height: int = 219, deck: Deck | None = None, slot: int | None = None):
        """Initialize card slot widget.
        
        Args:
            card: Card to display, or None for empty slot
            limit_break: Current limit break level (0-4)
            width: Width of card artwork in pixels
            height: Height of card artwork in pixels
            deck: Reference to containing deck for event synchronization
            slot: Slot position in deck (0-based)
        """
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.set_name(auto_title_from_instance(self))
        
        self._card = card
        self._limit_break = limit_break
        self.width = width
        self.height = height
        self._deck = deck
        self._slot = slot
        
        self.setup_ui()
        self.connect_signals()

    @property
    def card(self) -> Card | None:
        """Currently displayed card."""
        return self._card

    @property
    def limit_break(self) -> int:
        """Current limit break level."""
        return self._limit_break

    @property
    def deck(self) -> Deck | None:
        """Reference to containing deck."""
        return self._deck

    @property
    def slot(self) -> int | None:
        """Slot position in deck."""
        return self._slot
    
    def setup_ui(self) -> None:
        """Set up the UI components."""
        # Card artwork
        self.card_art = CardArtwork(self._card, self.width, self.height)
        self.append(self.card_art)
        
        # Limit break selector
        self.limit_break_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.limit_break_box.set_halign(Gtk.Align.FILL)
        self.limit_break_box.set_visible(True)
        
        self.limit_break_adjustment = Gtk.Adjustment(
            value=self._limit_break, lower=0, upper=4, step_increment=1, page_increment=1
        )
        self.limit_break_scale = Gtk.Scale(
            orientation=Gtk.Orientation.HORIZONTAL, 
            adjustment=self.limit_break_adjustment
        )
        self.limit_break_scale.set_draw_value(False)
        self.limit_break_scale.set_round_digits(0)
        self.limit_break_scale.set_digits(0)
        self.limit_break_scale.set_hexpand(True)
        
        # Add limit break marks (0-4)
        for i in range(5):
            self.limit_break_scale.add_mark(i, Gtk.PositionType.BOTTOM, str(i))
        
        self.limit_break_box.append(self.limit_break_scale)
        self.append(self.limit_break_box)
    
    def connect_signals(self) -> None:
        """Connect widget signals."""
        self.limit_break_scale.connect("value-changed", self._on_limit_break_changed)
        
        # Subscribe to deck events if we have a deck reference
        if self._deck is not None:
            self._deck.limit_break_set_at_slot.subscribe(self._on_deck_limit_break_changed)
    
    def _on_limit_break_changed(self, scale: Gtk.Scale) -> None:
        """Handle limit break change from UI - update deck."""
        new_limit_break = int(scale.get_value())
        if self._deck is not None and self._slot is not None:
            # Update the deck - this will trigger the event
            self._deck.set_limit_break_at_slot(new_limit_break, self._slot)
        # Don't update self._limit_break here - let the event callback handle it
    
    def _on_deck_limit_break_changed(self, deck: Deck, **kwargs) -> None:
        """Handle limit break change from deck - update UI."""
        slot = kwargs.get('slot')
        limit_break = kwargs.get('limit_break')
        
        # Only update if this event is for our slot
        if slot == self._slot and limit_break is not None:
            self._limit_break = limit_break
            # Update UI without triggering the signal to avoid infinite loops
            self.limit_break_scale.handler_block_by_func(self._on_limit_break_changed)
            self.limit_break_adjustment.set_value(limit_break)
            self.limit_break_scale.handler_unblock_by_func(self._on_limit_break_changed)
    
    def set_card(self, card: Card | None) -> bool:
        """Set the card for this slot (in-place update).
        
        Args:
            card: New card to display, or None for empty slot
            
        Returns:
            True if card was changed, False if already set to same card
        """
        if self._card is not card:
            self._card = card
            self.card_art.set_card(card)
            return True
        return False
    
    def set_limit_break(self, limit_break: int) -> bool:
        """Set the limit break level (in-place update).
        
        Args:
            limit_break: New limit break level (0-4)
            
        Returns:
            True if limit break was changed, False if already set to same level
        """
        if self._limit_break != limit_break:
            self._limit_break = limit_break
            # Block signal to prevent triggering deck update
            self.limit_break_scale.handler_block_by_func(self._on_limit_break_changed)
            self.limit_break_adjustment.set_value(limit_break)
            self.limit_break_scale.handler_unblock_by_func(self._on_limit_break_changed)
            return True
        return False
    
    def clear(self) -> None:
        """Clear the slot (remove card and reset limit break level)."""
        self.set_card(None)
        self.set_limit_break(0)
