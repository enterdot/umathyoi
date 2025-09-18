import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Gdk', '4.0')
from gi.repository import Gtk, Gdk, GLib
from typing import TYPE_CHECKING

import threading
import asyncio
from modules import Card
from utils import auto_title_from_instance

if TYPE_CHECKING:
    from application import MainApplication
    from windows import MainWindow

class CardArtwork(Gtk.Box):
    """A widget that displays card artwork with async loading and placeholder."""
    
    def __init__(self, window: 'MainWindow', card: Card = None, width: int = 45, height: int = 60):
        """Initialize card artwork widget.
        
        Args:
            window: Parent window reference
            card: Card to retrieve artwork for, or None for empty
            width: Width of card artwork in pixels
            height: Height of card artwork in pixels
        """
        super().__init__()
        self.app: MainApplication = window.app
        self.window: MainWindow = window
        self.set_name(auto_title_from_instance(self))
        self.card = card
        self.width = width
        self.height = height
        self.set_size_request(width, height)
        
        # Create widgets
        self.artwork = Gtk.Picture()
        self.artwork.set_size_request(width, height)
        
        # Create consistent empty frame (same size as artwork)
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
        
        # Create frame for loading state (same size)
        self.loading_frame = Gtk.Frame()
        self.loading_frame.set_size_request(width, height)
        self.loading_frame.set_child(self.spinner)
        
        if card:
            self.load_card_artwork()
        else:
            self.show_empty_frame()
    
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
        if card:
            self.load_card_artwork()
        else:
            self.show_empty_frame()
    
    def load_card_artwork(self):
        """Load card artwork asynchronously."""
        if not self.card:
            self.show_empty_frame()
            return
            
        # Show loading spinner while loading
        self.show_loading()
        
        def load_artwork():
            async def _load():
                pixbuf = await self.app.card_db.load_card_image(
                    self.card.id, self.width, self.height
                )
                
                def update_idle():
                    self.show_artwork(pixbuf)
                    return False
                
                GLib.idle_add(update_idle)
            
            def run_async():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(_load())
                loop.close()
            
            thread = threading.Thread(target=run_async)
            thread.daemon = True
            thread.start()
        
        load_artwork()
