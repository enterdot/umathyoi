import logging

logger = logging.getLogger(__name__)

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw

from .deck_carousel import DeckCarousel
from .turn_settings import TurnSettings
from .efficiency_plots import EfficiencyPlots
from common import auto_title_from_instance


class DeckInspector(Adw.Bin):
    """Container widget for deck carousel, turn settings, and efficiency plots."""

    VERTICAL_SPACING: int = 10
    MARGIN: int = 40

    def __init__(self, window):
        """Initialize deck inspector."""
        super().__init__()
        self.app = window.app
        self.window = window
        self.setup_ui()

        logger.debug(f"{auto_title_from_instance(self)} initialized")

    def setup_ui(self) -> None:
        """Set up the deck inspector UI components."""
        container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        container.set_spacing(DeckInspector.VERTICAL_SPACING)
        container.set_margin_bottom(DeckInspector.MARGIN)
        container.set_margin_top(DeckInspector.MARGIN)

        # Deck carousel
        self.deck_carousel = DeckCarousel(self.window)
        self.deck_carousel.set_vexpand(True)

        # Turn settings for efficiency calculator
        self.turn_settings = TurnSettings(self.window)
        self.turn_settings.set_vexpand(False)
        self.turn_settings.set_valign(Gtk.Align.END)

        # Efficiency plots (placeholder for now)
        self.efficiency_plots = EfficiencyPlots(self.window)
        self.efficiency_plots.set_vexpand(False)

        container.append(self.deck_carousel)
        container.append(self.turn_settings)
        # Plots will be added later when implemented
        # container.append(self.efficiency_plots)

        self.set_child(container)
