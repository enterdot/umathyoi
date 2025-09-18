import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw
from typing import TYPE_CHECKING

from modules import Card
from widgets import CardSelection, DeckCarousel
from utils import auto_title_from_instance, auto_tag_from_instance

if TYPE_CHECKING:
    from application import MainApplication
    from windows.main_window import MainWindow


class DeckBuilderView(Adw.Bin):
    """Main deck builder view with card selection sidebar and deck carousel."""
    
    def __init__(self, window: 'MainWindow'):
        """Initialize deck builder view.
        
        Args:
            window: Parent window reference
        """
        super().__init__()
        self.app: MainApplication = window.app
        self.window: MainWindow = window
        self.setup_ui()
        self.setup_responsive_ui()
        self.connect_signals()

    def setup_ui(self) -> None:
        """Set up the main UI with navigation split view."""
        split_view = Adw.NavigationSplitView()
        split_view.set_vexpand(True)
        split_view.set_min_sidebar_width(260)
        split_view.set_max_sidebar_width(320)
        split_view.set_sidebar_width_fraction(0.35)

        sidebar_page = Adw.NavigationPage()
        sidebar_child = CardSelection(self.window)
        sidebar_page.set_child(sidebar_child)
        sidebar_page.set_tag(f"{auto_tag_from_instance(sidebar_child)}-nav-page")
        sidebar_page.set_title(f"{auto_tag_from_instance(sidebar_child)} Navigation Page")

        content_page = Adw.NavigationPage()
        content_child = DeckCarousel(self.window)
        content_page.set_child(content_child)
        content_page.set_tag(f"{auto_tag_from_instance(content_child)}-nav-page")
        content_page.set_title(f"{auto_tag_from_instance(content_child)} Navigation Page")

        sidebar_child.refresh_all_action_rows()

        split_view.set_sidebar(sidebar_page)
        split_view.set_content(content_page)
        split_view.set_show_content(True)  # show content by default when collapsed

        self.set_child(split_view)

    def setup_responsive_ui(self) -> None:
        """Set up responsive behavior for different screen sizes."""
        split_view = self.get_child()
        self.window.width_breakpoint.add_setter(split_view, "collapsed", True)

    def connect_signals(self) -> None:
        """Connect any additional signals (currently none needed)."""
        pass
