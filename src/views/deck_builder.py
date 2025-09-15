import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw

from modules import Card
from widgets import CardSlot, CardSelection, DeckCarousel
from utils import auto_title_from_instance, auto_tag_from_instance

class DeckBuilderView(Adw.Bin):
    
    def __init__(self, window):
        super().__init__()
        self.app = window.app
        self.window = window
        self.setup_ui()
        self.setup_responsive_ui()
        self.connect_signals()

    def setup_ui(self):
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

        split_view.set_sidebar(sidebar_page)
        split_view.set_content(content_page)
        split_view.set_show_content(True)  # show content by default when collapsed

        self.set_child(split_view)

    def setup_responsive_ui(self):
        split_view = self.get_child()
        self.window.width_breakpoint.add_setter(split_view, "collapsed", True)

    def connect_signals(self):
        pass
