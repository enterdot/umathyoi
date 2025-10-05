import logging

logger = logging.getLogger(__name__)

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw

from common import auto_title_from_instance


class TurnSettings(Adw.Bin):
    """Widget for configuring efficiency calculator turn settings."""

    SETTINGS_MARGIN: int = 40

    def __init__(self, window):
        """Initialize turn settings widget."""
        super().__init__()
        self.app = window.app
        self.window = window
        self.setup_ui()

        logger.debug(f"{auto_title_from_instance(self)} initialized")

    def setup_ui(self) -> None:
        """Set up the turn settings UI components."""
        # TODO: Replace placeholder with actual settings controls
        # This will include:
        # - Facility type selection
        # - Facility level
        # - Number of cards on facility
        # - Current mood
        # - Energy level
        # - Fan count
        # - Any other turn-specific parameters

        container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        container.set_margin_bottom(TurnSettings.SETTINGS_MARGIN)

        label = Gtk.Label(label="Turn Settings")
        label.add_css_class("title-3")

        placeholder_text = Gtk.Label(label="Efficiency Calculator configuration will go here")
        placeholder_text.add_css_class("dim-label")

        container.append(label)
        container.append(placeholder_text)

        self.set_child(container)
