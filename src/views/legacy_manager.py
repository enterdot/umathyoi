import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw

from widgets import Placeholder

class LegacyManagerView(Adw.Bin):
    
    def __init__(self, window):
        super().__init__()
        self.app = window.app
        self.window = window
        self.setup_ui()
        self.setup_responsive_ui()
        self.connect_signals()

    def setup_ui(self):
        self.set_child(Placeholder("Legacy Manager", "Coming soon..."))

    def setup_responsive_ui(self):
        pass

    def connect_signals(self):
        pass
