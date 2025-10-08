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
    MIN_PLOTS_WIDTH: int = 400

    def __init__(self, window):
        """Initialize deck inspector."""
        super().__init__()
        self.app = window.app
        self.window = window
        self.setup_ui()

        logger.debug(f"{auto_title_from_instance(self)} initialized")

    def setup_ui(self) -> None:
        """Set up the deck inspector UI components with split view."""
        # Use OverlaySplitView for deck+settings on left, plots on right
        split_view = Adw.OverlaySplitView()
        split_view.set_sidebar_position(Gtk.PackType.END)  # Plots on the right
        #split_view.set_show_sidebar(True)
        #split_view.set_enable_hide(True)
        #split_view.set_enable_show(True)
        split_view.set_min_sidebar_width(DeckInspector.MIN_PLOTS_WIDTH)
        split_view.set_sidebar_width_fraction(0.35)
        
        # Left side: Carousel + Turn Settings
        left_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        left_container.set_spacing(DeckInspector.VERTICAL_SPACING)
        left_container.set_margin_bottom(DeckInspector.MARGIN)
        left_container.set_margin_top(DeckInspector.MARGIN)

        # Deck carousel
        self.deck_carousel = DeckCarousel(self.window)
        self.deck_carousel.set_vexpand(True)

        # Turn settings for efficiency calculator
        self.turn_settings = TurnSettings(self.window)
        self.turn_settings.set_vexpand(False)
        self.turn_settings.set_valign(Gtk.Align.END)

        left_container.append(self.deck_carousel)
        left_container.append(self.turn_settings)

        # Right side: Efficiency plots
        self.efficiency_plots = EfficiencyPlots(self.window)

        # Assemble split view
        split_view.set_content(left_container)
        split_view.set_sidebar(self.efficiency_plots)

        self.set_child(split_view)
