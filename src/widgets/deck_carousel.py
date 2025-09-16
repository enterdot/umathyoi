import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw

from modules import Card, Deck
from widgets import CardSlot, Placeholder
from utils import auto_tag_from_instance, auto_title_from_instance

class DeckCarousel(Adw.Bin):
    
    def __init__(self, window):
        super().__init__()
        self.app = window.app
        self.window = window
        self.setup_ui()
        self.connect_signals()
        
    def setup_ui(self):
        
        container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        container.set_spacing(20)
        container.set_margin_bottom(30)
        container.set_margin_top(30)
        
        self.carousel = Adw.Carousel()
        self.carousel.set_allow_mouse_drag(True)
        self.carousel.set_allow_scroll_wheel(True)
        self.carousel.set_allow_long_swipes(True)
        self.carousel.set_reveal_duration(200)
        self.carousel.minimum_spacing = 30
        self.carousel.set_spacing(self.carousel.minimum_spacing)
        self.carousel.set_vexpand(True)
        self.carousel.set_valign(Gtk.Align.CENTER)
            
        for slot, deck in self.app.deck_list:
            self.carousel.append(self.create_carousel_page(slot, deck))

        self.update_carousel_hints(self.carousel)

        deck_efficency = Placeholder("Deck Efficency Box")
        deck_efficency.set_vexpand(False)  # Don't expand
        deck_efficency.set_valign(Gtk.Align.END)  # Stay at bottom
        deck_efficency.set_margin_bottom(40)
        
        container.append(self.carousel)
        container.append(deck_efficency)
        self.set_child(container)
    
    def connect_signals(self):
        # Existing carousel signals
        self.carousel.connect("page-changed", self.on_page_changed)
        self.carousel.connect("notify::position", self.on_notify_position)
        self.window.connect("notify::default-width", self.on_window_width_changed)
        self.window.connect("notify::default-height", self.on_window_height_changed)
        
        # Subscribe to deck events for real-time updates
        self.app.deck_list.slot_activated.subscribe(self._on_active_deck_changed)
        for slot, deck in self.app.deck_list:
            # TODO: use partial instead
            deck.card_added_at_slot.subscribe(self._on_card_added_to_deck)
            deck.card_removed_at_slot.subscribe(self._on_card_removed_from_deck)
            deck.limit_break_set_at_slot.subscribe(self._on_limit_break_changed)

    def update_carousel_spacing(self, carousel):
        nav_page = self.get_parent()
        nav_page_width = float(nav_page.get_width())
        if hasattr(self, 'last_nav_page_width'):
            if not hasattr(carousel, 'target_spacing'):
                carousel.target_spacing = float(carousel.get_spacing())
            carousel.target_spacing += (nav_page_width - self.last_nav_page_width) / 2
            carousel.set_spacing(round(max(carousel.minimum_spacing, carousel.target_spacing)))
        self.last_nav_page_width = float(nav_page_width)
    
    def update_carousel_hints(self, carousel):
        position = carousel.get_position()
        current_page_index = round(position)

        for nth_page_index in range(carousel.get_n_pages()):
            nth_page = carousel.get_nth_page(nth_page_index)
            distance = abs(nth_page_index - current_page_index)
            if distance == 0:
                nth_page.remove_css_class("carousel-side")
                nth_page.add_css_class("carousel-active")
            else:
                nth_page.remove_css_class("carousel-active")
                nth_page.add_css_class("carousel-side")

    def on_window_width_changed(self, window, param):
        self.update_carousel_spacing(self.carousel)

    def on_window_height_changed(self, window, param):
        pass

    def on_page_changed(self, carousel, page_index):
        self.app.deck_list.active_slot = page_index

    def on_notify_position(self, carousel, param):
        self.update_carousel_hints(carousel)

    # Event handlers for deck state changes
    def _on_active_deck_changed(self, caller, **kwargs):
        """Handle when the active deck changes - refresh current page."""
        current_page_index = round(self.carousel.get_position())
        self._refresh_carousel_page(current_page_index)

    def _on_card_added_to_deck(self, deck, **kwargs):
        """Handle when a card is added to any deck."""
        deck_slot = self.app.deck_list.find_deck_slot(deck)  # Use DeckList method
        if deck_slot is not None:
            card = kwargs.get('card')
            index = kwargs.get('index')
            self._update_single_card_slot(deck_slot, index, card, 0)  # New card starts at level 0

    def _on_card_removed_from_deck(self, deck, **kwargs):
        """Handle when a card is removed from any deck."""
        deck_slot = self.app.deck_list.find_deck_slot(deck)  # Use DeckList method
        if deck_slot is not None:
            index = kwargs.get('index')
            self._update_single_card_slot(deck_slot, index, None, 0)  # Empty slot

    def _on_limit_break_changed(self, deck, **kwargs):
        """Handle when a limit break level changes in any deck."""
        deck_slot = self.app.deck_list.find_deck_slot(deck)  # Use DeckList method
        if deck_slot is not None:
            index = kwargs.get('index')
            limit_break = kwargs.get('limit_break')
            # Get current card at that slot
            card = deck.get_card_at_slot(index)
            self._update_single_card_slot(deck_slot, index, card, limit_break)

    def _refresh_carousel_page(self, slot_index):
        return # TODO: is it safe to remove?
        # the state of the carousel page only would've changed if there was a 
        # way to add cards to a non-active deck, if that feature was ever added
        # we should have a more sophisticated way of updating the page instead
        # of just creating a whole new deck grid which causes flickering.
        """Refresh a specific carousel page to reflect current deck state."""
        if 0 <= slot_index < self.carousel.get_n_pages():
            _, deck = list(self.app.deck_list)[slot_index]
            
            # Get the navigation page and its grid
            nav_page = self.carousel.get_nth_page(slot_index)
            old_grid = nav_page.get_child()
            
            # Create new grid with current deck state
            new_grid = self._create_deck_grid(deck)
            
            # Replace the old grid
            nav_page.set_child(new_grid)

    def _update_single_card_slot(self, deck_slot, card_index, card, limit_break):
        """Update a single card slot in the carousel using in-place updates."""
        if 0 <= deck_slot < self.carousel.get_n_pages():
            nav_page = self.carousel.get_nth_page(deck_slot)
            deck_grid = nav_page.get_child()
            
            # Find the specific card slot widget (at grid position)
            row, col = divmod(card_index, 3)
            card_slot = deck_grid.get_child_at(col, row)
            
            if card_slot and isinstance(card_slot, CardSlot):
                # Update existing widget in-place instead of replacing it
                if card_slot.set_card(card):
                    self._update_card_slot_click_handler(card_slot, card_index, card)

                card_slot.set_level(limit_break)

    def _update_card_slot_click_handler(self, card_slot, slot_index, card):
        if card is None:
            card_slot.remove_controller(card_slot._click_controller)
            card_slot._click_controller = None
        else:
            click_gesture = Gtk.GestureClick()
            click_gesture.connect("pressed", self._on_card_slot_clicked, slot_index)
            card_slot.add_controller(click_gesture)
            card_slot._click_controller = click_gesture  # Store reference for later removal
            
    def create_carousel_page(self, slot: int, deck: Deck):
        """Create a carousel page for a deck."""
        deck_grid = self._create_deck_grid(deck)
        return Adw.NavigationPage.new_with_tag(deck_grid, f"Deck {slot + 1}", f"deck_carousel_{slot}")

    def _create_deck_grid(self, deck: Deck):
        """Create the grid widget for a deck."""
        deck_grid = Gtk.Grid()
        deck_grid.set_row_spacing(24)
        deck_grid.set_column_spacing(24)

        for index, card, limit_break in deck:
            card_slot = self.create_card_slot(card, limit_break, index)
            # TODO: update to use divmod like _update_single_card_slot
            deck_grid.attach(card_slot, index % 3, index // 3, 1, 1)
        
        return deck_grid
    
    def create_card_slot(self, card: Card, level: int, slot_index: int):
        """Create a card slot widget for the deck grid."""
        active_deck = self.app.deck_list.active_deck
        card_slot = CardSlot(card, level, 150, 200, deck=active_deck, slot_index=slot_index)
        
        # Add click handler for card removal and store reference
        if card is not None:  # Only add click handler if there's a card
            click_gesture = Gtk.GestureClick()
            click_gesture.connect("pressed", self._on_card_slot_clicked, slot_index)
            card_slot.add_controller(click_gesture)
            card_slot._click_controller = click_gesture  # Store reference
        else:
            card_slot._click_controller = None  # Initialize as None for empty slots
        
        return card_slot

    def _on_card_slot_clicked(self, gesture, n_press, x, y, slot_index):
        """Handle clicking on a card in the deck to remove it."""
        active_deck = self.app.deck_list.active_deck
        if active_deck:
            active_deck.remove_card_at_slot(slot_index)
