import logging
logger = logging.getLogger(__name__)

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Gdk, Adw
from typing import TYPE_CHECKING

from views import DeckBuilderView
from views import LegacyManagerView
from utils import UIConstants, auto_title_from_instance

if TYPE_CHECKING:
    from application import MainApplication


class MainWindow(Adw.ApplicationWindow):
    """Main application window with responsive design and CSS styling."""
    
    def __init__(self, app: 'MainApplication', app_name: str):
        """Initialize main window.
        
        Args:
            app: Application instance
            app_name: Display name for window title
        """
        super().__init__(application=app)
        self.app: MainApplication = app
        
        self.set_title(app_name)
        self.set_default_size(UIConstants.DEFAULT_WINDOW_WIDTH, UIConstants.DEFAULT_WINDOW_HEIGHT)
        self.set_size_request(UIConstants.MIN_WINDOW_WIDTH, UIConstants.MIN_WINDOW_HEIGHT)

        self.width_breakpoint: Adw.Breakpoint
        self.height_breakpoint: Adw.Breakpoint
        self._setup_breakpoints(UIConstants.DEFAULT_BREAKPOINT_WIDTH, None)

        self._load_css()
        self._setup_ui()

        logger.info(f"Presenting {auto_title_from_instance(self)} ({UIConstants.DEFAULT_WINDOW_WIDTH} by {UIConstants.DEFAULT_WINDOW_HEIGHT})")
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

        deck_builder_view = DeckBuilderView(self)
        legacy_manager_view = LegacyManagerView(self)

        view_stack.add_titled(deck_builder_view, "deck_builder_view", "Deck Builder")
        view_stack.add_titled(legacy_manager_view, "legacy_manager_view", "Legacy Manager")
        
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
                transition: transform {UIConstants.CSS_TRANSITION_DURATION}ms ease;
                opacity: 0.8;
            }}

            .carousel-active {{
                transform: scale(1.0);
                transition: transform {UIConstants.CSS_TRANSITION_DURATION}ms ease;
                opacity: 1.0;
            }}

            /* Empty card slot styling */

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
        """
        css_provider.load_from_data(css.encode())
        
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
