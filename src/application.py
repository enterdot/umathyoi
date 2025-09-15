import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Gio, Adw

from modules import CardDatabase, Deck, CardStats, DeckList
from windows import MainWindow

# Global app instance for widgets to access
_app_instance = None


def get_app():
    """Get the current application instance."""
    return _app_instance


class MainApplication(Adw.Application):
    """Main application class handling application-level logic and data."""
    
    def __init__(self, app_name: str, app_version: str, app_reverse_dns: str):
        super().__init__(application_id=app_reverse_dns)
        
        global _app_instance
        _app_instance = self
        
        self.app_name = app_name
        self.app_version = app_version

        self.connect('activate', self.on_activate)
        
        self._init_data()
        self._setup_actions()
    
    def _init_data(self):
        """Initialize application data (card database and decks)."""
        self.card_db = CardDatabase()
        self.card_stats = CardStats()
        self.deck_list = DeckList()

        self.decks: list[Deck] = []
        self.active_deck: int = 0
        # TODO: Load from last session instead, this is just to test
        # If no deck create an empty one at index 0
        self._create_test_decks()  
 
    
    def _create_test_decks(self):
        """Create test decks for development."""
        # Old way using a simple list
        deck1 = Deck("Deck 1")
        for card_id, level in ((30024, 0), (20028, 3), (20019, 1), (30025, 0), (20017, 2), (30032, 4)):
            card = self.card_db.get_card_by_id(card_id)
            deck1.add_card(card, level)
        deck1.remove_card_at_slot(2)
        print(deck1)
        
        deck2 = Deck("Deck 2")
        for card_id, level in ((20015, 1), (20028, 1), (30025, 4), (20019, 4), (20017, 0), (30032, 3)):
            card = self.card_db.get_card_by_id(card_id)
            deck2.add_card(card, level)
        deck2.remove_card_at_slot(3)
        deck2.remove_card_at_slot(4)
        print(deck2)
        
        self.decks = [deck1, deck2]
        
        #New way using a DeckList
        self.deck_list = DeckList(decks=self.decks)
    
    def _setup_actions(self):
        """Set up application actions and keyboard shortcuts."""
        self.create_action('preferences', self.on_preferences)
        self.create_action('about', self.on_about)
        
        self.set_accels_for_action("app.preferences", ["<Ctrl>comma"])
        self.set_accels_for_action("app.about", ["F1"])
    
    def create_action(self, name: str, callback) -> None:
        """Create and add an action to the application."""
        action = Gio.SimpleAction.new(name, None)
        action.connect('activate', callback)
        self.add_action(action)
    
    def on_activate(self, app):
        """Handle application activation."""
        window = MainWindow(self, self.app_name)
        window.present()
    
    def on_preferences(self, action, param):
        """Handle preferences action."""
        print("Preferences dialog coming soon!")
    
    def on_about(self, action, param):
        """Handle about action."""
        window = self.get_active_window()
        about_dialog = Adw.AboutWindow(
            transient_for=window,
            application_name=self.app_name,
            application_icon="applications-games-symbolic",
            developer_name=f"{self.app_name} Team",
            version=self.app_version,
            license_type=Gtk.License.GPL_3_0
        )
        about_dialog.present()
