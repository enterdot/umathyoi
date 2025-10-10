import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, GLib

from modules import Card
from common import auto_title_from_instance, texture_from_pixbuf


class CardArtwork(Gtk.Box):
    """A widget that displays card artwork with async loading and placeholder."""

    def __init__(
        self, window, card: Card = None, width: int = 45, height: int = 60
    ):
        """Initialize card artwork widget."""
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

        # Empty frame (for no card)
        self.empty_frame = Gtk.Frame()
        self.empty_frame.set_size_request(width, height)
        self.empty_frame.add_css_class("empty-card-slot")

        empty_icon = Gtk.Image()
        empty_icon.set_from_icon_name("list-add-symbolic")
        empty_icon.set_pixel_size(24)
        empty_icon.set_halign(Gtk.Align.CENTER)
        empty_icon.set_valign(Gtk.Align.CENTER)
        empty_icon.add_css_class("empty-slot-indicator")
        self.empty_frame.set_child(empty_icon)

        # Loading frame (spinner)
        self.spinner = Gtk.Spinner()
        self.spinner.set_size_request(width, height)
        self.spinner.set_halign(Gtk.Align.CENTER)
        self.spinner.set_valign(Gtk.Align.CENTER)

        self.loading_frame = Gtk.Frame()
        self.loading_frame.set_size_request(width, height)
        self.loading_frame.set_child(self.spinner)

        # Error frame (for load failures)
        self.error_frame = Gtk.Frame()
        self.error_frame.set_size_request(width, height)
        self.error_frame.add_css_class("error-card-slot")

        error_icon = Gtk.Image()
        error_icon.set_from_icon_name("dialog-error-symbolic")
        error_icon.set_pixel_size(24)
        error_icon.set_halign(Gtk.Align.CENTER)
        error_icon.set_valign(Gtk.Align.CENTER)
        error_icon.add_css_class("error-slot-indicator")
        self.error_frame.set_child(error_icon)

        self.load_card_artwork()

    def show_empty_frame(self):
        """Show empty frame when no card is assigned."""
        self._clear_children()
        self.append(self.empty_frame)

    def show_loading(self):
        """Show loading spinner."""
        self._clear_children()
        self.spinner.start()
        self.append(self.loading_frame)

    def show_error(self):
        """Show error state when loading fails."""
        self.spinner.stop()
        self._clear_children()
        self.append(self.error_frame)

    def show_artwork(self, pixbuf):
        """Show the loaded artwork."""
        self.spinner.stop()

        if pixbuf:
            texture = texture_from_pixbuf(pixbuf)
            self.artwork.set_paintable(texture)
            self.artwork.add_css_class("card")

            self._clear_children()
            self.append(self.artwork)
        else:
            # Loading failed, show error state
            self.show_error()

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

        # Show loading spinner
        self.show_loading()

        def on_image_loaded(pixbuf):
            """Called on GTK main thread when image loads."""

            def update_ui():
                self.show_artwork(pixbuf)
                return False

            GLib.idle_add(update_ui)

        # Start background download
        self.app.card_db.load_card_image_async(
            self.card.id, self.width, self.height, on_image_loaded
        )
