import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Gdk', '4.0')
from gi.repository import Gtk, Gdk, GLib

from modules import Card
from utils import auto_title_from_instance


class CardArtwork(Gtk.Box):
    """A widget that displays card artwork with async loading and placeholder."""
    
    def __init__(self, window, card: Card = None, width: int = 45, height: int = 60):
        """Initialize card artwork widget.
        
        Args:
            window: Parent window reference
            card: Card to retrieve artwork for, or None for empty
            width: Width of card artwork in pixels
            height: Height of card artwork in pixels
        """
        super().__init__()
        self.app = window.app
        self.window = window
        self.set_name(auto_title_from_instance(self))
        self.card = card
        self.width = width
        self.height = height
        self.set_size_request(width, height)
        
        # Create widgets
        self.artwork = Gtk.Picture()
        self.artwork.set_size_request(width, height)
        
        # Create consistent empty frame
        self.empty_frame = Gtk.Frame()
        self.empty_frame.set_size_request(width, height)
        self.empty_frame.add_css_class("empty-card-slot")
        
        # Add empty slot indicator
        empty_label = Gtk.Label()
        empty_label.set_text("+")
        empty_label.add_css_class("empty-slot-indicator")
        empty_label.set_halign(Gtk.Align.CENTER)
        empty_label.set_valign(Gtk.Align.CENTER)
        self.empty_frame.set_child(empty_label)
        
        # Create loading spinner
        self.spinner = Gtk.Spinner()
        self.spinner.set_size_request(width, height)
        self.spinner.set_halign(Gtk.Align.CENTER)
        self.spinner.set_valign(Gtk.Align.CENTER)
        
        # Create frame for loading state
        self.loading_frame = Gtk.Frame()
        self.loading_frame.set_size_request(width, height)
        self.loading_frame.set_child(self.spinner)
        
        self.load_card_artwork()

    
    def show_empty_frame(self):
        """Show consistent empty frame when card is None."""
        self._clear_children()
        self.append(self.empty_frame)
    
    def show_loading(self):
        """Show loading spinner in frame."""
        self._clear_children()
        self.spinner.start()
        self.append(self.loading_frame)
    
    def show_artwork(self, pixbuf):
        """Show the loaded artwork with consistent sizing."""
        self.spinner.stop()
        
        if pixbuf:
            texture = Gdk.Texture.new_for_pixbuf(pixbuf)
            self.artwork.set_paintable(texture)
            self.artwork.add_css_class("card")
            
            self._clear_children()
            self.append(self.artwork)
        else:
            # If loading failed, show empty frame
            self.show_empty_frame()
    
    def _clear_children(self):
        """Remove all child widgets."""
        child = self.get_first_child()
        while child:
            next_child = child.get_next_sibling()
            self.remove(child)
            child = next_child
    
    def set_card(self, card: Card):
        """Set a new card and load its artwork."""
        self.card = card
        self.load_card_artwork()
    
    def load_card_artwork(self):
        """Load card artwork asynchronously in background thread."""
        if not self.card:
            self.show_empty_frame()
            return
            
        # Show loading spinner while loading
        self.show_loading()
        
        def on_image_loaded(pixbuf):
            """Called on GTK main thread when image loads."""
            # Schedule UI update using GLib.idle_add for thread safety
            def update_ui():
                self.show_artwork(pixbuf)
                return False  # Don't repeat
            
            GLib.idle_add(update_ui)
        
        # Start background download
        self.app.card_db.load_card_image_async(
            self.card.id,
            self.width,
            self.height,
            on_image_loaded
        )
