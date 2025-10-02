import logging
logger = logging.getLogger(__name__)

import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gdk, Gtk, GLib

from modules import Card
from modules import Deck
from .card_artwork import CardArtwork
from utils import auto_title_from_instance, UIConstants, CardConstants


class CardSlot(Gtk.Box):
    """Widget representing a single card slot in a deck with artwork and limit break selector."""
    
    def __init__(self, window, width: int, height: int):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.app = window.app
        self.window = window

        self.width = width
        self.height = height

        self.setup_ui()
        self.connect_signals()
        
        self.set_name(auto_title_from_instance(self))
    
    def setup_ui(self) -> None:

        #TODO: see if we can remove set_size_request and set_hexpand/set_vexpand
        # wobble might be gone now that we use a stack for the various card slot states

        # Lock size to prevent wobble
        self.set_size_request(self.width, self.height)
        self.set_hexpand(False)
        self.set_vexpand(False)

        # Stack holds all possible states
        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.NONE)
        self.stack.set_transition_duration(0)
        
        # Empty state
        empty_frame = Gtk.Frame()
        empty_frame.set_size_request(self.width, self.height)
        empty_frame.add_css_class("empty-card-slot")
        
        empty_label = Gtk.Label()
        empty_label.set_text("+")
        empty_label.add_css_class("empty-slot-indicator")
        empty_label.set_halign(Gtk.Align.CENTER)
        empty_label.set_valign(Gtk.Align.CENTER)
        empty_frame.set_child(empty_label)
        
        # Loading state
        loading_frame = Gtk.Frame()
        loading_frame.set_size_request(self.width, self.height)
        
        self.spinner = Gtk.Spinner()
        self.spinner.set_size_request(self.width, self.height)
        self.spinner.set_halign(Gtk.Align.CENTER)
        self.spinner.set_valign(Gtk.Align.CENTER)
        loading_frame.set_child(self.spinner)
        
        # Artwork state
        self.artwork = Gtk.Picture()
        self.artwork.set_size_request(self.width, self.height)
        
        # Error state
        error_frame = Gtk.Frame()
        error_frame.set_size_request(self.width, self.height)
        error_frame.add_css_class("error-card-slot")
        
        error_icon = Gtk.Image()
        error_icon.set_from_icon_name("dialog-error-symbolic")
        error_icon.set_pixel_size(24)
        error_icon.add_css_class("error-slot-indicator")
        error_icon.set_halign(Gtk.Align.CENTER)
        error_icon.set_valign(Gtk.Align.CENTER)
        error_frame.set_child(error_icon)
        
        # Add all states to stack
        self.stack.add_named(empty_frame, "empty")
        self.stack.add_named(loading_frame, "loading")
        self.stack.add_named(self.artwork, "artwork")
        self.stack.add_named(error_frame, "error")
        
        self.append(self.stack)

        # Limit break selector
        limit_break_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        limit_break_box.set_halign(Gtk.Align.FILL)
        limit_break_box.set_visible(True)
        
        self.limit_break_adjustment = Gtk.Adjustment(
            value=self.limit_break, lower=CardConstants.MIN_LIMIT_BREAK, upper=CardConstants.MAX_LIMIT_BREAK, step_increment=1, page_increment=1
        )
        self.limit_break_scale = Gtk.Scale(
            orientation=Gtk.Orientation.HORIZONTAL, 
            adjustment=self.limit_break_adjustment
        )
        self.limit_break_scale.set_draw_value(False)
        self.limit_break_scale.set_round_digits(0)
        self.limit_break_scale.set_digits(0)
        self.limit_break_scale.set_hexpand(True)
        
        # Add limit break marks
        for i in range(CardConstants.MAX_LIMIT_BREAK + 1):
            self.limit_break_scale.add_mark(i, Gtk.PositionType.BOTTOM, str(i))
        
        limit_break_box.append(self.limit_break_scale)
        self.append(limit_break_box)

        # Initialize click controller as None
        self._click_controller = None

        # Start in empty state
        self.show_empty()

    def connect_signals(self) -> None:
        """Connect widget signals."""
        # Limit break handler is set externally via set_limit_break_changed_handler()
        self._limit_break_handler_id = None
    
    @property
    def card(self) -> Card | None:
        if not hasattr(self, '_card'):
            self._card = None
        return self._card
    
    @card.setter
    def card(self, card: Card | None) -> None:
        if card and self.card is not card:
            self._card = card
            self.load_card_artwork(self._card)
            self.limit_break_scale.set_sensitive(True)
        elif not card:
            self._card = None
            self.show_empty()
            self.limit_break_scale.set_sensitive(False)

    @property
    def limit_break(self) -> int:
        if not hasattr(self, '_limit_break'):
            self._limit_break = CardConstants.MIN_LIMIT_BREAK
        return self._limit_break
    
    @limit_break.setter
    def limit_break(self, limit_break: int) -> None:
        if not CardConstants.MIN_LIMIT_BREAK <= limit_break <= CardConstants.MAX_LIMIT_BREAK:
            raise ValueError(f"{limit_break=} is not in range [{CardConstants.MIN_LIMIT_BREAK}, {CardConstants.MAX_LIMIT_BREAK}]")
        self._limit_break = limit_break
        # Block signal to prevent triggering callback during programmatic updates
        if self._limit_break_handler_id is not None:
            self.limit_break_scale.handler_block(self._limit_break_handler_id)
        self.limit_break_adjustment.set_value(limit_break)
        if self._limit_break_handler_id is not None:
            self.limit_break_scale.handler_unblock(self._limit_break_handler_id)
    
    def show_empty(self):
        """Show empty slot indicator."""
        self.stack.set_visible_child_name("empty")
    
    def show_loading(self):
        """Show loading spinner."""
        self.spinner.start()
        self.stack.set_visible_child_name("loading")
    
    def show_artwork(self, pixbuf):
        """Show card artwork."""
        self.spinner.stop()
        
        if pixbuf:
            texture = Gdk.Texture.new_for_pixbuf(pixbuf)
            self.artwork.set_paintable(texture)
            self.artwork.add_css_class("card")
            self.stack.set_visible_child_name("artwork")
        else:
            self.show_error()
    
    def show_error(self):
        """Show error state."""
        self.spinner.stop()
        self.stack.set_visible_child_name("error")
    
    def load_card_artwork(self, card):
        """Load card artwork asynchronously."""
        self.show_loading()
        
        def on_image_loaded(pixbuf):
            def update_ui():
                self.show_artwork(pixbuf)
                return False
            
            GLib.idle_add(update_ui)
        
        self.app.card_db.load_card_image_async(
            card.id,
            self.width,
            self.height,
            on_image_loaded
        )

    def set_click_handler(self, callback: callable, *args) -> None:
        """Set click handler for this card slot.
        
        Args:
            callback: Function to call when clicked
            *args: Additional arguments to pass to callback
        """
        self.remove_click_handler()
        
        if callback:
            click_gesture = Gtk.GestureClick()
            click_gesture.connect("pressed", lambda gesture, n_press, x, y: callback(*args))
            self.add_controller(click_gesture)
            self._click_controller = click_gesture
    
    def remove_click_handler(self) -> None:
        """Remove the current click handler if one exists."""
        if self._click_controller:
            self.remove_controller(self._click_controller)
            self._click_controller = None

    def set_limit_break_changed_handler(self, callback: callable, *args) -> None:
        """Set handler for limit break scale changes.
        
        Args:
            callback: Function to call when limit break changes
            *args: Additional arguments to pass to callback
        """
        self.remove_limit_break_changed_handler()
        
        if callback:
            self._limit_break_handler_id = self.limit_break_scale.connect(
                "value-changed",
                lambda scale: callback(int(scale.get_value()), *args)
            )
    
    def remove_limit_break_changed_handler(self) -> None:
        """Remove the current limit break change handler if one exists."""
        if self._limit_break_handler_id is not None:
            self.limit_break_scale.disconnect(self._limit_break_handler_id)
            self._limit_break_handler_id = None
