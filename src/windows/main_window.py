import logging

logger = logging.getLogger(__name__)

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Gdk, Adw

from views import DeckBuilder, LegacyManager, BannerPlanner, PullChance, RaceSimulator
from common import auto_title_from_instance


class MainWindow(Adw.ApplicationWindow):
    """Main application window with responsive design and CSS styling."""

    DEFAULT_BREAKPOINT_WIDTH: int = 848
    MIN_WINDOW_WIDTH: int = 560
    MIN_WINDOW_HEIGHT: int = 1240
    DEFAULT_WINDOW_WIDTH: int = 1200
    DEFAULT_WINDOW_HEIGHT: int = 1240
    CSS_TRANSITION_DURATION: int = 200

    def __init__(self, app, app_name: str):
        """Initialize main window."""

        super().__init__(application=app)
        self.app = app

        self.set_title(app_name)
        self.set_default_size(MainWindow.DEFAULT_WINDOW_WIDTH, MainWindow.DEFAULT_WINDOW_HEIGHT)
        self.set_size_request(MainWindow.MIN_WINDOW_WIDTH, MainWindow.MIN_WINDOW_HEIGHT)

        self.width_breakpoint: Adw.Breakpoint
        self.height_breakpoint: Adw.Breakpoint
        self._setup_breakpoints(MainWindow.DEFAULT_BREAKPOINT_WIDTH, None)

        self._load_css()
        self._setup_ui()

        logger.info(f"Presenting {auto_title_from_instance(self)} ({MainWindow.DEFAULT_WINDOW_WIDTH} by {MainWindow.DEFAULT_WINDOW_HEIGHT})")
        self.present()

        logger.debug(f"{auto_title_from_instance(self)} initialized")

    def _setup_breakpoints(self, width: int | None, height: int | None) -> None:
        """Set up responsive breakpoints for different screen sizes.

        Args:
            width: Breakpoint width in pixels, or None to skip
            height: Breakpoint height in pixels, or None to skip
        """
        if width:
            self.width_breakpoint = Adw.Breakpoint.new(Adw.BreakpointCondition.parse(f"max-width: {str(width)}sp"))
            self.add_breakpoint(self.width_breakpoint)
        if height:
            self.height_breakpoint = Adw.Breakpoint.new(Adw.BreakpointCondition.parse(f"max-height: {str(height)}sp"))
            self.add_breakpoint(self.height_breakpoint)

    def _setup_ui(self) -> None:
        """Set up the main window UI components."""
        header_bar = Adw.HeaderBar()
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        view_stack = Adw.ViewStack()
        view_switcher = Adw.ViewSwitcher()
        view_switcher.set_stack(view_stack)

        deck_builder_view = DeckBuilder(self)
        legacy_manager_view = LegacyManager(self)
        banner_planner_view = BannerPlanner(self)
        pull_chance_view = PullChance(self)
        race_simulator_view = RaceSimulator(self)

        view_stack.add_titled(deck_builder_view, "deck_builder", "Deck Builder")
        view_stack.add_titled(legacy_manager_view, "legacy_manager", "Legacy Manager")
        view_stack.add_titled(banner_planner_view, "banner_planner", "Banner Planner")
        view_stack.add_titled(pull_chance_view, "pull_chance", "Pull Chance")
        view_stack.add_titled(race_simulator_view, "race_simulator", "Race Simulator")

        header_bar.set_title_widget(view_switcher)
        main_box.append(header_bar)
        main_box.append(view_stack)

        self.set_content(main_box)

    def _load_css(self) -> None:
        """Load custom CSS styling for the application."""
        css_provider = Gtk.CssProvider()
        css = f"""
            /* Carousel animations */

            .carousel-side {{
                transform: scale(0.85);
                transition: transform {MainWindow.CSS_TRANSITION_DURATION}ms ease;
                opacity: 0.8;
            }}

            .carousel-active {{
                transform: scale(1.0);
                transition: transform {MainWindow.CSS_TRANSITION_DURATION}ms ease;
                opacity: 1.0;
            }}

            .empty-card-slot {{
                background-color: alpha(@theme_fg_color, 0.1);
                border: 2px dashed alpha(@theme_fg_color, 0.3);
                border-radius: 8px;
            }}

            .empty-slot-indicator {{
                font-size: 24px;
                font-weight: bold;
                color: alpha(@theme_fg_color, 0.5);
            }}

            .error-card-slot {{
                background-color: alpha(@error_color, 0.1);
                border: 2px solid alpha(@error_color, 0.3);
                border-radius: 8px;
            }}

            .error-slot-indicator {{
                font-size: 24px;
                font-weight: bold;
                color: @error_color;
            }}

            .card-in-deck {{
                opacity: 0.5;
            }}

            .card-in-deck:hover {{
                opacity: 0.6;  /* Slight feedback on hover */
            }}
        """

        css_provider.load_from_string(css)

        Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
