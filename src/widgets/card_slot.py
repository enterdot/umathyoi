import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk

from modules.card import Card
from .card_artwork import CardArtwork
from utils import auto_title_from_instance


class CardSlot(Gtk.Box):
    """A widget representing a single card slot in a deck with artwork and level selector."""
    
    def __init__(self, card: Card = None, level: int = 0, width: int = 164, height: int = 219):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.set_name(auto_title_from_instance(self))
        
        self.card = card
        self.level = level
        self.width = width
        self.height = height
        
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
        #self.level_scale.set_has_origin(True)
        self.level_scale.set_hexpand(True)
        
        # Add level marks
        for i in range(5):
            self.level_scale.add_mark(i, Gtk.PositionType.BOTTOM, str(i))
        
        self.level_box.append(self.level_scale)
        self.append(self.level_box)
    
    # TODO: ask to explain this signal and emit methods, could they use Event?
    def connect_signals(self):
        """Connect widget signals."""
        self.level_scale.connect("value-changed", self._on_level_changed)
    
    def _on_level_changed(self, scale):
        """Handle level change."""
        self.level = int(scale.get_value())
        # Emit a custom signal or call a callback if needed
        self.emit_level_changed()
    
    def emit_level_changed(self):
        """Override this method or connect to it for level change notifications."""
        pass
    
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


