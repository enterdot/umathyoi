import logging

logger = logging.getLogger(__name__)

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw

from modules import Card, Deck
from .card_slot import CardSlot
from common import auto_title_from_instance


class DeckCarousel(Adw.Bin):
    """Carousel widget displaying multiple decks with visual scaling animations."""

    HINTS_SPACING: int = 60
    REVEAL_DURATION: int = 200
    GRID_SPACING: int = 30
    CARD_SLOT_WIDTH: int = 150
    CARD_SLOT_HEIGHT: int = 200

    def __init__(self, window):
        """Initialize deck carousel."""
        super().__init__()
        self.app = window.app
        self.window = window
        self.setup_ui()
        self.connect_signals()

        logger.debug(f"{auto_title_from_instance(self)} initialized")

    def setup_ui(self) -> None:
        """Set up the carousel UI components."""
        self.carousel = Adw.Carousel()
        self.carousel.set_allow_mouse_drag(True)
        self.carousel.set_allow_scroll_wheel(True)
        self.carousel.set_allow_long_swipes(True)
        self.carousel.set_reveal_duration(DeckCarousel.REVEAL_DURATION)
        self.carousel.set_spacing(DeckCarousel.HINTS_SPACING)

        # Create pages for all decks in deck list
        for deck_slot, deck in self.app.deck_list:
            self.carousel.append(self.create_carousel_page(deck_slot, deck))

        self.update_carousel_hints(self.carousel)
        self.set_child(self.carousel)

    def connect_signals(self) -> None:
        """Connect carousel and deck event signals."""
        # Carousel navigation signals
        self.carousel.connect("page-changed", self._on_page_changed)
        self.carousel.connect("notify::position", self._on_notify_position)

        # Window resize signals for responsive spacing
        self.window.connect(
            "notify::default-width", self._on_window_width_changed
        )
        self.window.connect(
            "notify::default-height", self._on_window_height_changed
        )

        # Active deck change signals
        self.app.deck_list.slot_activated.subscribe(
            self._on_active_deck_changed
        )

        # Active deck content change signals
        self.app.deck_list.card_added_to_active_deck_at_slot.subscribe(
            self._on_card_added_to_active_deck
        )
        self.app.deck_list.card_removed_from_active_deck_at_slot.subscribe(
            self._on_card_removed_from_active_deck
        )
        self.app.deck_list.limit_break_set_for_active_deck_at_slot.subscribe(
            self._on_limit_break_changed_in_active_deck
        )
        self.app.deck_list.mute_toggled_for_active_deck_at_slot.subscribe(
            self._on_mute_toggled_in_active_deck
        )

    def update_carousel_spacing(self, carousel: Adw.Carousel) -> None:
        """Update carousel spacing based on window width for responsive design."""
        nav_page = self.get_parent()
        nav_page_width = float(nav_page.get_width())

        if hasattr(self, "last_nav_page_width"):
            if not hasattr(carousel, "target_spacing"):
                carousel.target_spacing = float(carousel.get_spacing())
            carousel.target_spacing += (
                nav_page_width - self.last_nav_page_width
            ) / 2
            carousel.set_spacing(
                round(max(DeckCarousel.HINTS_SPACING, carousel.target_spacing))
            )

        self.last_nav_page_width = float(nav_page_width)

    def update_carousel_hints(self, carousel: Adw.Carousel) -> None:
        """Update visual hints (scaling) for carousel pages based on position."""
        position = carousel.get_position()
        current_page_index = round(position)

        for page_index in range(carousel.get_n_pages()):
            page = carousel.get_nth_page(page_index)
            distance = abs(page_index - current_page_index)

            if distance == 0:
                page.remove_css_class("carousel-side")
                page.add_css_class("carousel-active")
            else:
                page.remove_css_class("carousel-active")
                page.add_css_class("carousel-side")

    def create_carousel_page(
        self, deck_slot: int, deck: Deck
    ) -> Adw.NavigationPage:
        """Create a carousel page for a deck."""
        deck_grid = self._create_deck_grid(deck)
        logger.debug(f"Created grid for deck {deck}")
        return Adw.NavigationPage.new_with_tag(
            deck_grid, f"Deck {deck_slot}", f"deck_carousel_{deck_slot}"
        )

    def _create_deck_grid(self, deck: Deck) -> Gtk.Grid:
        """Create the grid widget for a deck."""
        deck_grid = Gtk.Grid()
        deck_grid.set_row_spacing(DeckCarousel.GRID_SPACING)
        deck_grid.set_column_spacing(DeckCarousel.GRID_SPACING)

        for slot, card, limit_break, muted in deck:
            card_slot_widget = self._create_card_slot(
                slot, card, limit_break, muted
            )
            row, col = divmod(slot, deck.size // 2)
            deck_grid.attach(card_slot_widget, col, row, 1, 1)

        deck_grid.deck = deck
        return deck_grid

    def _create_card_slot(
        self,
        slot: int,
        card: Card | None,
        limit_break: int = Card.MIN_LIMIT_BREAK,
        muted: bool = False,
    ) -> CardSlot:
        """Create a card slot widget for the deck grid."""
        card_slot_widget = CardSlot(
            self.window,
            DeckCarousel.CARD_SLOT_WIDTH,
            DeckCarousel.CARD_SLOT_HEIGHT,
        )
        card_slot_widget.card = card
        card_slot_widget.limit_break = limit_break
        card_slot_widget.muted = muted

        # Add click handler only if card is present
        if card is not None:
            card_slot_widget.set_click_handler(self._on_card_slot_clicked, slot)

        # Add limit break change handler
        card_slot_widget.set_limit_break_changed_handler(
            self._on_limit_break_changed, slot
        )

        # Add mute change handler
        card_slot_widget.set_mute_changed_handler(self._on_mute_changed, slot)

        return card_slot_widget

    def _update_card_slot(
        self,
        deck_page: int,
        slot: int,
        card: Card | None,
        limit_break: int,
        muted: bool = False,
    ) -> None:
        """Update a single card slot in the carousel using in-place updates."""
        if 0 <= deck_page < self.carousel.get_n_pages():
            nav_page = self.carousel.get_nth_page(deck_page)
            deck_grid = nav_page.get_child()

            # Find the specific card slot widget using grid position
            row, col = divmod(slot, deck_grid.deck.size // 2)
            card_slot_widget = deck_grid.get_child_at(col, row)

            if card_slot_widget and isinstance(card_slot_widget, CardSlot):
                # Update existing widget in-place
                card_slot_widget.card = card
                card_slot_widget.limit_break = limit_break
                card_slot_widget.muted = muted

                # Update click handler based on whether card is present
                if card is not None:
                    card_slot_widget.set_click_handler(
                        self._on_card_slot_clicked, slot
                    )
                else:
                    card_slot_widget.remove_click_handler()

    def _on_card_slot_clicked(self, slot: int) -> None:
        """Handle clicking on a card in the deck to remove it."""
        active_deck = self.app.deck_list.active_deck
        if active_deck:
            logger.debug(
                f"Attempt removing card at slot {slot} from active deck"
            )
            active_deck.remove_card_at_slot(slot)

    def _on_limit_break_changed(self, new_limit_break: int, slot: int) -> None:
        """Handle limit break change from card slot scale."""
        active_deck = self.app.deck_list.active_deck
        if active_deck:
            logger.debug(
                f"Setting limit break to {new_limit_break} for slot={slot} in active deck"
            )
            active_deck.set_limit_break_at_slot(slot, new_limit_break)

    def _on_mute_changed(self, muted: bool, slot: int) -> None:
        """Handle mute toggle from card slot button."""
        active_deck = self.app.deck_list.active_deck
        if active_deck:
            logger.debug(
                f"Setting mute to {muted} for slot={slot} in active deck"
            )
            active_deck.set_mute_at_slot(slot, muted)

    # UI events
    def _on_window_width_changed(self, window: Gtk.Window, param) -> None:
        """Handle window width changes for responsive spacing."""
        self.update_carousel_spacing(self.carousel)

    def _on_window_height_changed(self, window: Gtk.Window, param) -> None:
        """Handle window height changes (currently unused)."""
        pass

    def _on_page_changed(self, carousel: Adw.Carousel, page_index: int) -> None:
        """Handle carousel page changes to update active deck."""
        self.app.deck_list.active_slot = page_index

    def _on_notify_position(self, carousel: Adw.Carousel, param) -> None:
        """Handle carousel position changes for visual hints."""
        self.update_carousel_hints(carousel)

    # State events
    def _on_active_deck_changed(self, deck_list, **kwargs) -> None:
        """Handle when the active deck changes."""
        pass

    def _on_card_added_to_active_deck(self, deck_list, **kwargs) -> None:
        """Handle when a card is added to the active deck."""
        card = kwargs.get("card")
        slot = kwargs.get("slot")
        if card is not None and slot is not None:
            self._update_card_slot(
                self.app.deck_list.active_slot,
                slot,
                card,
                Card.MIN_LIMIT_BREAK,
                False,
            )

    def _on_card_removed_from_active_deck(self, deck_list, **kwargs) -> None:
        """Handle when a card is removed from the active deck."""
        slot = kwargs.get("slot")
        if slot is not None:
            self._update_card_slot(
                self.app.deck_list.active_slot,
                slot,
                None,
                Card.MIN_LIMIT_BREAK,
                False,
            )

    def _on_limit_break_changed_in_active_deck(
        self, deck_list, **kwargs
    ) -> None:
        """Handle when a limit break level changes in the active deck."""
        slot = kwargs.get("slot")
        limit_break = kwargs.get("limit_break")
        if slot is not None and limit_break is not None:
            # Get current card and mute state at that slot
            active_deck = self.app.deck_list.active_deck
            if active_deck:
                card = active_deck.get_card_at_slot(slot)
                muted = active_deck.is_muted_at_slot(slot)
                self._update_card_slot(
                    self.app.deck_list.active_slot,
                    slot,
                    card,
                    limit_break,
                    muted,
                )

    def _on_mute_toggled_in_active_deck(self, deck_list, **kwargs) -> None:
        """Handle when mute state changes in the active deck."""
        slot = kwargs.get("slot")
        muted = kwargs.get("muted")
        if slot is not None and muted is not None:
            # Get current card and limit break at that slot
            active_deck = self.app.deck_list.active_deck
            if active_deck:
                card = active_deck.get_card_at_slot(slot)
                limit_break = active_deck.get_limit_break_at_slot(slot)
                self._update_card_slot(
                    self.app.deck_list.active_slot,
                    slot,
                    card,
                    limit_break,
                    muted,
                )
