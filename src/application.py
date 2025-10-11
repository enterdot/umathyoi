import logging

logger = logging.getLogger(__name__)

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Gio, Adw

from modules import CardDatabase, ScenarioDatabase, CharacterDatabase, SkillDatabase
from modules import (
    Deck,
    CardView,
    DeckList,
    EfficiencyCalculator,
    Character,
    StatType,
    Aptitude,
)
from windows import MainWindow
from common import auto_title_from_instance


class MainApplication(Adw.Application):
    """Main application class handling application-level logic and data."""

    NAME: str = "Umathyoi"
    VERSION: str = "0.0"

    def __init__(self):
        """Initialize the main application."""
        super().__init__(application_id=f"com.{MainApplication.NAME.lower()}")

        self.name = MainApplication.NAME
        self.version = MainApplication.VERSION

        logger.info(f"Starting {self.name} version {self.version}")

        self.connect("activate", self.on_activate)

        self._init_data()
        self._setup_actions()
        logger.info("Main application setup completed")

        logger.debug(f"{auto_title_from_instance(self)} initialized")

    def _init_data(self) -> None:
        """Initialize application data (card database and decks)."""

        logger.info("Loading databases and user configurations")
        self.card_db = CardDatabase()
        self.scenario_db = ScenarioDatabase()
        self.character_db = CharacterDatabase()
        self.skill_db = SkillDatabase()

        for character in self.character_db:
            self.character_db.load_character_portrait_async(character.id, 16, 16, lambda x: x)

        for skill in self.skill_db:
            self.skill_db.load_skill_icon_async(skill.id, 16, 16, lambda x: x)

        self.card_view = CardView()

        # Initialize deck list with test data
        # TODO: load from dconf for session persistence
        test_decks = self._create_test_decks()
        self.deck_list = DeckList(decks=test_decks)

        # Initialize with first scenario and a generic character
        # TODO: load from dconf for session persistence
        character = Character(0, 0, "placeholder", "placeholder", [0] * 5, [Aptitude.A] * 10)
        scenario = self.scenario_db.scenarios[0]
        self.efficiency_calculator = EfficiencyCalculator(
            self.deck_list, scenario, character
        )

    def _create_test_decks(self) -> list[Deck]:
        """Create test decks for development and testing."""
        # Test deck 1 - Power focused
        deck1 = Deck()
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

        logger.debug(f"Created first test deck: {deck1}")

        # Test deck 2 - Speed focused
        deck2 = Deck()
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

        logger.debug(f"Created second test deck: {deck2}")

        return [deck1, deck2]

    def _setup_actions(self) -> None:
        """Set up application actions and keyboard shortcuts."""
        self.create_action("preferences", self._on_preferences)
        self.create_action("about", self._on_about)

        # Set keyboard shortcuts
        self.set_accels_for_action("app.preferences", ["<Ctrl>comma"])
        self.set_accels_for_action("app.about", ["F1"])

    def create_action(self, name: str, callback) -> None:
        """Create and add an action to the application."""
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.add_action(action)

    def on_activate(self, app: Adw.Application) -> None:
        """Handle application activation by creating and presenting main window."""
        window = MainWindow(self, self.name)
        window.present()

    def _on_preferences(self, action: Gio.SimpleAction, param) -> None:
        """Handle preferences action.

        Note:
            Currently shows placeholder message. Should open preferences dialog
            when implemented.
        """
        logger.debug("Preferences dialog not yet implemented")

    def _on_about(self, action: Gio.SimpleAction, param) -> None:
        """Handle about action by showing about dialog."""
        window = self.get_active_window()
        if window:
            about_dialog = Adw.AboutWindow(
                transient_for=window,
                application_name=self.name,
                application_icon="applications-games-symbolic",
                developer_name=f"{self.name} Team",
                version=self.version,
                license_type=Gtk.License.MIT_X11,
            )
            about_dialog.present()
