import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk

from modules.card import Card
from modules.deck import Deck
from .card_artwork import CardArtwork
from utils import auto_title_from_instance


class CardSlot(Gtk.Box):
    """A widget representing a single card slot in a deck with artwork and level selector."""
    
    def __init__(self, card: Card = None, level: int = 0, width: int = 164, height: int = 219, deck: Deck = None, slot_index: int = None):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.set_name(auto_title_from_instance(self))
        
        self.card = card
        self.level = level
        self.width = width
        self.height = height
        self.deck = deck  # NEW: Reference to deck
        self.slot_index = slot_index  # NEW: Index in deck
        
        self.setup_ui()
        self.connect_signals()
    
    def setup_ui(self):
        """Set up the UI components."""
        # Card artwork
        self.card_art = CardArtwork(self.card, self.width, self.height)
        self.append(self.card_art)
        
        # Level selector
        self.level_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.level_box.set_halign(Gtk.Align.FILL)
        self.level_box.set_visible(True)
        
        self.level_adjustment = Gtk.Adjustment(
            value=self.level, lower=0, upper=4, step_increment=1, page_increment=1
        )
        self.level_scale = Gtk.Scale(
            orientation=Gtk.Orientation.HORIZONTAL, 
            adjustment=self.level_adjustment
        )
        self.level_scale.set_draw_value(False)
        self.level_scale.set_round_digits(0)
        self.level_scale.set_digits(0)
        self.level_scale.set_hexpand(True)
        
        # Add level marks
        for i in range(5):
            self.level_scale.add_mark(i, Gtk.PositionType.BOTTOM, str(i))
        
        self.level_box.append(self.level_scale)
        self.append(self.level_box)
    
    def connect_signals(self):
        """Connect widget signals."""
        self.level_scale.connect("value-changed", self._on_level_changed)
        
        # NEW: Subscribe to deck events if we have a deck reference
        if self.deck is not None:
            self.deck.limit_break_set_at_slot.subscribe(self._on_deck_limit_break_changed)
    
    def _on_level_changed(self, scale):
        """Handle level change from UI - update deck."""
        new_level = int(scale.get_value())
        if self.deck is not None and self.slot_index is not None:
            # Update the deck - this will trigger the event
            self.deck.set_limit_break_at_slot(new_level, self.slot_index)
        # Don't update self.level here - let the event callback handle it
    
    def _on_deck_limit_break_changed(self, deck, **kwargs):
        """Handle limit break change from deck - update UI."""
        index = kwargs.get('index')
        limit_break = kwargs.get('limit_break')
        
        # Only update if this event is for our slot
        if index == self.slot_index and limit_break is not None:
            self.level = limit_break
            # Update UI without triggering the signal to avoid infinite loops
            self.level_scale.handler_block_by_func(self._on_level_changed)
            self.level_adjustment.set_value(limit_break)
            self.level_scale.handler_unblock_by_func(self._on_level_changed)
    
    def set_card(self, card: Card):
        """Set the card for this slot."""
        self.card = card
        self.card_art.set_card(card)
    
    def get_card(self) -> Card:
        """Get the current card."""
        return self.card
    
    def set_level(self, level: int):
        """Set the limit break level."""
        self.level = level
        self.level_adjustment.set_value(level)
    
    def get_level(self) -> int:
        """Get the current limit break level."""
        return self.level
    
    def clear(self):
        """Clear the slot (remove card and reset level)."""
        self.set_card(None)
        self.set_level(0)
