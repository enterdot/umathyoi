import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw
from typing import TYPE_CHECKING

from modules import Card, Deck
from .card_slot import CardSlot
from .placeholder import Placeholder
from utils import auto_tag_from_instance, auto_title_from_instance, UIConstants

if TYPE_CHECKING:
    from application import MainApplication
    from windows import MainWindow


class DeckCarousel(Adw.Bin):
    """Carousel widget displaying multiple decks with visual scaling animations."""
    
    def __init__(self, window: 'MainWindow'):
        """Initialize deck carousel.
        
        Args:
            window: Parent window reference
        """
        super().__init__()
        self.app: MainApplication = window.app
        self.window: MainWindow = window
        self.setup_ui()
        self.connect_signals()
        
    def setup_ui(self) -> None:
        """Set up the carousel UI components."""
        container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        container.set_spacing(UIConstants.CAROUSEL_SPACING)
        container.set_margin_bottom(UIConstants.CAROUSEL_MARGIN)
        container.set_margin_top(UIConstants.CAROUSEL_MARGIN)
        
        self.carousel = Adw.Carousel()
        self.carousel.set_allow_mouse_drag(True)
        self.carousel.set_allow_scroll_wheel(True)
        self.carousel.set_allow_long_swipes(True)
        self.carousel.set_reveal_duration(UIConstants.CAROUSEL_REVEAL_DURATION)
        self.carousel.set_spacing(UIConstants.CAROUSEL_MIN_SPACING)
        self.carousel.set_vexpand(True)
        self.carousel.set_valign(Gtk.Align.CENTER)
            
        # Create pages for all decks in deck list
        for slot, deck in self.app.deck_list:
            self.carousel.append(self.create_carousel_page(slot, deck))

        self.update_carousel_hints(self.carousel)

        # Deck efficiency placeholder
        deck_efficiency = Placeholder("Deck Efficiency Box")
        deck_efficiency.set_vexpand(False)
        deck_efficiency.set_valign(Gtk.Align.END)
        deck_efficiency.set_margin_bottom(UIConstants.DECK_EFFICIENCY_MARGIN_BOTTOM)
        
        container.append(self.carousel)
        container.append(deck_efficiency)
        self.set_child(container)
    
    def connect_signals(self) -> None:
        """Connect carousel and deck event signals."""
        # Carousel navigation signals
        self.carousel.connect("page-changed", self._on_page_changed)
        self.carousel.connect("notify::position", self._on_notify_position)
        
        # Window resize signals for responsive spacing
        self.window.connect("notify::default-width", self._on_window_width_changed)
        self.window.connect("notify::default-height", self._on_window_height_changed)
        
        # Active deck change signals
        self.app.deck_list.slot_activated.subscribe(self._on_active_deck_changed)
        
        # Active deck content change signals
        self.app.deck_list.card_added_to_active_deck_at_slot.subscribe(self._on_card_added_to_active_deck)
        self.app.deck_list.card_removed_from_active_deck_at_slot.subscribe(self._on_card_removed_from_active_deck)
        self.app.deck_list.limit_break_set_for_active_deck_at_slot.subscribe(self._on_limit_break_changed_in_active_deck)

    def update_carousel_spacing(self, carousel: Adw.Carousel) -> None:
        """Update carousel spacing based on window width for responsive design.
        
        Args:
            carousel: Carousel widget to update
        """
        nav_page = self.get_parent()
        nav_page_width = float(nav_page.get_width())
        
        if hasattr(self, 'last_nav_page_width'):
            if not hasattr(carousel, 'target_spacing'):
                carousel.target_spacing = float(carousel.get_spacing())
            carousel.target_spacing += (nav_page_width - self.last_nav_page_width) / 2
            carousel.set_spacing(round(max(carousel.minimum_spacing, carousel.target_spacing)))
        
        self.last_nav_page_width = float(nav_page_width)
    
    def update_carousel_hints(self, carousel: Adw.Carousel) -> None:
        """Update visual hints (scaling) for carousel pages based on position.
        
        Args:
            carousel: Carousel widget to update
        """
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

    def create_carousel_page(self, deck_slot: int, deck: Deck) -> Adw.NavigationPage:
        """Create a carousel page for a deck.
        
        Args:
            deck_slot: Slot number of the deck in deck list
            deck: Deck to display
            
        Returns:
            Navigation page containing the deck grid
        """
        deck_grid = self._create_deck_grid(deck)
        return Adw.NavigationPage.new_with_tag(
            deck_grid, 
            f"Deck {deck_slot + 1}", 
            f"deck_carousel_{deck_slot}"
        )

    def _create_deck_grid(self, deck: Deck) -> Gtk.Grid:
        """Create the grid widget for a deck.
        
        Args:
            deck: Deck to create grid for
            
        Returns:
            Grid widget containing card slots
        """
        deck_grid = Gtk.Grid()
        deck_grid.set_row_spacing(UIConstants.DECK_GRID_SPACING)
        deck_grid.set_column_spacing(UIConstants.DECK_GRID_SPACING)

        for slot, card, limit_break in deck:
            card_slot_widget = self._create_card_slot_widget(card, limit_break, deck, slot)
            row, col = divmod(slot, 3) # TODO: magic number, replace with half of max deck size constant
            deck_grid.attach(card_slot_widget, col, row, 1, 1)
        
        return deck_grid
        
    
    def _create_card_slot_widget(self, card: Card | None, limit_break: int, deck: Deck, slot: int) -> CardSlot:
        """Create a card slot widget for the deck grid.
        
        Args:
            card: Card to display, or None for empty slot
            limit_break: Current limit break level
            deck: Deck the slot is bound to
            slot: Slot position in deck
            
        Returns:
            Configured CardSlot widget
        """
        card_slot = CardSlot(self.window, card, limit_break, UIConstants.CARD_SLOT_WIDTH, UIConstants.CARD_SLOT_HEIGHT, deck=deck, slot=slot)
        
        # Add click handler for card removal if slot contains a card
        if card is not None:
            click_gesture = Gtk.GestureClick()
            click_gesture.connect("pressed", self._on_card_slot_clicked, slot)
            card_slot.add_controller(click_gesture)
            card_slot._click_controller = click_gesture  # Store reference for removal
        else:
            card_slot._click_controller = None  # Initialize as None for empty slots
        
        return card_slot

    def _refresh_carousel_page(self, deck_slot: int) -> None:
        """Refresh a specific carousel page to reflect current deck state.
        
        Args:
            deck_slot: Slot number of deck to refresh
        """
        if 0 <= deck_slot < self.carousel.get_n_pages():
            _, deck = list(self.app.deck_list)[deck_slot]
            
            # Get the navigation page and replace its grid
            nav_page = self.carousel.get_nth_page(deck_slot)
            new_grid = self._create_deck_grid(deck)
            nav_page.set_child(new_grid)

    def _update_single_card_slot(self, deck_slot: int, card_slot: int, card: Card | None, limit_break: int) -> None:
        """Update a single card slot in the carousel using in-place updates.
        
        Args:
            deck_slot: Slot number of deck in carousel
            card_slot: Slot number of card in deck
            card: New card to display, or None for empty
            limit_break: New limit break level
        """
        if 0 <= deck_slot < self.carousel.get_n_pages():
            nav_page = self.carousel.get_nth_page(deck_slot)
            deck_grid = nav_page.get_child()
            
            # Find the specific card slot widget using grid position
            row, col = divmod(card_slot, 3)
            card_slot_widget = deck_grid.get_child_at(col, row)
            
            if card_slot_widget and isinstance(card_slot_widget, CardSlot):
                # Update existing widget in-place
                if card_slot_widget.set_card(card):
                    self._update_card_slot_click_handler(card_slot_widget, card_slot, card)
                card_slot_widget.set_limit_break(limit_break)

    def _update_card_slot_click_handler(self, card_slot_widget: CardSlot, slot: int, card: Card | None) -> None:
        """Update click handler for card slot based on whether it contains a card.
        
        Args:
            card_slot_widget: CardSlot widget to update
            slot: Slot position
            card: Card in slot, or None if empty
        """
        # Remove existing click handler if present
        if hasattr(card_slot_widget, '_click_controller') and card_slot_widget._click_controller:
            card_slot_widget.remove_controller(card_slot_widget._click_controller)
            card_slot_widget._click_controller = None
        
        # Add click handler only if slot contains a card
        if card is not None:
            click_gesture = Gtk.GestureClick()
            click_gesture.connect("pressed", self._on_card_slot_clicked, slot)
            card_slot_widget.add_controller(click_gesture)
            card_slot_widget._click_controller = click_gesture

    # Event handlers
    def _on_window_width_changed(self, window: Gtk.Window, param) -> None:
        """Handle window width changes for responsive spacing."""
        self.update_carousel_spacing(self.carousel)

    def _on_window_height_changed(self, window: Gtk.Window, param) -> None:
        """Handle window height changes (currently unused)."""
        pass

    def _on_page_changed(self, carousel: Adw.Carousel, page_index: int) -> None:
        """Handle carousel page changes to update active deck.
        
        Args:
            carousel: Carousel that changed
            page_index: New active page index
        """
        self.app.deck_list.active_slot = page_index

    def _on_notify_position(self, carousel: Adw.Carousel, param) -> None:
        """Handle carousel position changes for visual hints.
        
        Args:
            carousel: Carousel with position change
            param: Parameter spec (unused)
        """
        self.update_carousel_hints(carousel)

    def _on_active_deck_changed(self, deck_list, **kwargs) -> None:
        """Handle when the active deck changes - refresh current page.
        
        Args:
            deck_list: DeckList that triggered the event
            **kwargs: Event parameters
        """
        pass

    def _on_card_added_to_active_deck(self, deck_list, **kwargs) -> None:
        """Handle when a card is added to the active deck.
        
        Args:
            deck_list: DeckList that triggered the event
            **kwargs: Event parameters including 'card' and 'slot'
        """
        card = kwargs.get('card')
        card_slot = kwargs.get('slot')
        if card is not None and card_slot is not None:
            self._update_single_card_slot(self.app.deck_list.active_slot, card_slot, card, 0)

    def _on_card_removed_from_active_deck(self, deck_list, **kwargs) -> None:
        """Handle when a card is removed from the active deck.
        
        Args:
            deck_list: DeckList that triggered the event
            **kwargs: Event parameters including 'slot'
        """
        card_slot = kwargs.get('slot')
        if card_slot is not None:
            self._update_single_card_slot(self.app.deck_list.active_slot, card_slot, None, 0)

    def _on_limit_break_changed_in_active_deck(self, deck_list, **kwargs) -> None:
        """Handle when a limit break level changes in the active deck.
        
        Args:
            deck_list: DeckList that triggered the event
            **kwargs: Event parameters including 'slot' and 'limit_break'
        """
        card_slot = kwargs.get('slot')
        limit_break = kwargs.get('limit_break')
        if card_slot is not None and limit_break is not None:
            # Get current card at that slot
            active_deck = self.app.deck_list.active_deck
            card = active_deck.get_card_at_slot(card_slot) if active_deck else None
            self._update_single_card_slot(self.app.deck_list.active_slot, card_slot, card, limit_break)

    def _on_card_slot_clicked(self, gesture: Gtk.GestureClick, n_press: int, x: float, y: float, slot: int) -> None:
        """Handle clicking on a card in the deck to remove it.
        
        Args:
            gesture: Click gesture that triggered
            n_press: Number of button presses
            x: X coordinate of click
            y: Y coordinate of click
            slot: Slot position of clicked card
        """
        active_deck = self.app.deck_list.active_deck
        if active_deck:
            active_deck.remove_card_at_slot(slot)
