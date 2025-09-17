import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Gio, Adw

from modules import CardDatabase, Deck, CardStats, DeckList
from windows import MainWindow
from utils import Logger

class MainApplication(Adw.Application):
    """Main application class handling application-level logic and data."""
    
    def __init__(self, app_name: str, app_version: str, app_reverse_dns: str):
        """Initialize the main application.
        
        Args:
            app_name: Display name of the application
            app_version: Version string
            app_reverse_dns: Reverse DNS identifier for the application
        """
        super().__init__(application_id=app_reverse_dns)
        
        self.app_name = app_name
        self.app_version = app_version

        Logger.info(f"Initializing {self.app_name} version {self.app_version}")

        self.connect('activate', self.on_activate)
        
        self._init_data()
        self._setup_actions()
    
    def _init_data(self) -> None:
        """Initialize application data (card database and decks)."""
        self.card_db = CardDatabase()
        self.card_stats = CardStats()
        
        # Initialize deck list with test data
        # TODO: Replace with session persistence when implemented
        test_decks = self._create_test_decks()
        self.deck_list = DeckList(decks=test_decks)
    
    def _create_test_decks(self) -> list[Deck]:
        """Create test decks for development and testing.
        
        Returns:
            List of test decks with sample cards
            
        Note:
            This method should be replaced with proper session loading
            when data persistence is implemented.
        """
        # Test deck 1 - Power focused
        deck1 = Deck("Power Deck")
        test_cards_1 = [
            (30024, 0),  # Oguri Cap
            (20028, 3),  # Zenno Rob Roy
            (20019, 1),  # Nice Nature
            (30025, 0),  # Special Week
            (20017, 2),  # Meisho Doto
            (30032, 4),  # Yaeno Muteki
        ]
        
        for card_id, limit_break in test_cards_1:
            card = self.card_db.get_card_by_id(card_id)
            if card:
                deck1.add_card(card, limit_break)
        
        # Remove one card to show partial deck
        deck1.remove_card_at_slot(2)

        Logger.debug("Created test deck 1", name=deck1.name, card_count=deck1.card_count, cards=[c.id for _, c, _ in deck1 if c])

        # Test deck 2 - Speed focused
        deck2 = Deck("Speed Deck")
        test_cards_2 = [
            (20015, 1),  # Marvelous Sunday
            (20028, 1),  # Zenno Rob Roy
            (30025, 4),  # Special Week
            (20019, 4),  # Nice Nature
            (20017, 0),  # Meisho Doto
            (30032, 3),  # Yaeno Muteki
        ]
        
        for card_id, limit_break in test_cards_2:
            card = self.card_db.get_card_by_id(card_id)
            if card:
                deck2.add_card(card, limit_break)
        
        # Remove some cards to show different configurations
        deck2.remove_card_at_slot(3)
        deck2.remove_card_at_slot(4)

        Logger.debug("Created test deck 2", name=deck2.name, card_count=deck2.card_count, cards=[c.id for _, c, _ in deck1 if c])

        return [deck1, deck2]
    
    def _setup_actions(self) -> None:
        """Set up application actions and keyboard shortcuts."""
        self.create_action('preferences', self._on_preferences)
        self.create_action('about', self._on_about)
        
        # Set keyboard shortcuts
        self.set_accels_for_action("app.preferences", ["<Ctrl>comma"])
        self.set_accels_for_action("app.about", ["F1"])
    
    def create_action(self, name: str, callback) -> None:
        """Create and add an action to the application.
        
        Args:
            name: Action name
            callback: Function to call when action is activated
        """
        action = Gio.SimpleAction.new(name, None)
        action.connect('activate', callback)
        self.add_action(action)
    
    def on_activate(self, app: Adw.Application) -> None:
        """Handle application activation by creating and presenting main window.
        
        Args:
            app: Application instance (self)
        """
        window = MainWindow(self, self.app_name)
        window.present()
    
    def _on_preferences(self, action: Gio.SimpleAction, param) -> None:
        """Handle preferences action.
        
        Args:
            action: Action that was activated
            param: Action parameters (unused)
            
        Note:
            Currently shows placeholder message. Should open preferences dialog
            when implemented.
        """
        Logger.debug("Preferences dialog not yet implemented")
    
    def _on_about(self, action: Gio.SimpleAction, param) -> None:
        """Handle about action by showing about dialog.
        
        Args:
            action: Action that was activated
            param: Action parameters (unused)
        """
        window = self.get_active_window()
        if window:
            about_dialog = Adw.AboutWindow(
                transient_for=window,
                application_name=self.app_name,
                application_icon="applications-games-symbolic",
                developer_name=f"{self.app_name} Team",
                version=self.app_version,
                license_type=Gtk.License.MIT_X11
            )
            about_dialog.present()
