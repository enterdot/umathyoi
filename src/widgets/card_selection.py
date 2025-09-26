import logging
logger = logging.getLogger(__name__)

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw
from typing import TYPE_CHECKING

from modules import Card, CardInspector
from .card_artwork import CardArtwork
from utils import auto_tag_from_instance, auto_title_from_instance, UIConstants, CardConstants

if TYPE_CHECKING:
    from application import MainApplication
    from windows import MainWindow


class CardSelection(Adw.Bin):
    """Card selection sidebar with card list and detailed stats view."""
    
    def __init__(self, window: 'MainWindow'):
        """Initialize card selection widget.
        
        Args:
            window: Parent window reference
        """
        super().__init__()
        self.app: MainApplication = window.app
        self.window: MainWindow = window
        self._list_box: Gtk.ListBox | None = None

        self.setup_ui()
        self.connect_signals()
        
        logger.debug(f"{auto_title_from_instance(self)} initialized")

    @property
    def list_box(self) -> Gtk.ListBox:
        """Main card list box widget."""
        return self._list_box

    @list_box.setter
    def list_box(self, list_box: Gtk.ListBox) -> None:
        """Set the main card list box widget."""
        self._list_box = list_box

    @property
    def action_rows(self):
        """Generator yielding all action rows in the list box."""
        row = self.list_box.get_first_child()
        while row:
            yield row
            row = row.get_next_sibling()

    def setup_ui(self) -> None:
        """Set up the card selection UI with view stack."""
        view_stack = Adw.ViewStack()
        view_stack.add_named(self._create_card_list_view(), "card_selection_view")
        view_stack.add_named(self._create_stats_info_view(), "stats_info_view")
        self.set_child(view_stack)

    def connect_signals(self) -> None:
        """Connect all event signals."""
        # Deck list events for active deck changes
        self.app.deck_list.slot_deactivated.subscribe(self._on_active_deck_deactivated)
        self.app.deck_list.slot_activated.subscribe(self._on_active_deck_activated)
        
        # Active deck card change events
        self.app.deck_list.card_added_to_active_deck_at_slot.subscribe(self._on_active_deck_card_added)
        self.app.deck_list.card_removed_from_active_deck_at_slot.subscribe(self._on_active_deck_card_removed)

        # Card inspector events
        self.app.card_inspector.card_changed.subscribe(self._on_card_inspector_changed)

    def refresh_all_action_rows(self) -> None:
        """Refresh visibility of all action rows based on current active deck state."""
        active_deck = self.app.deck_list.active_deck
        if not active_deck:
            return
            
        for row in self.action_rows:
            if row.card in active_deck:
                self._hide_row(row)
            else:
                self._show_row(row)

    def _hide_row(self, row: Adw.ActionRow) -> None:
        """Hide row when card is added to deck.
        
        Args:
            row: Action row to hide
        """
        row.set_visible(False)
    
    def _show_row(self, row: Adw.ActionRow) -> None:
        """Show row when card is removed from deck.
        
        Args:
            row: Action row to show
        """
        row.set_visible(True)

    def _create_card_list_view(self) -> Gtk.ScrolledWindow:
        """Create the main card list view.
        
        Returns:
            Scrolled window containing the card list
        """
        list_box = Gtk.ListBox()
        list_box.set_selection_mode(Gtk.SelectionMode.NONE)
        list_box.add_css_class("boxed-list-separate")
        
        # Connect list box signals
        list_box.connect("row-activated", self._on_card_row_activated)
        
        click_gesture = Gtk.GestureClick()
        click_gesture.connect("pressed", self._on_card_list_view_clicked, list_box)
        list_box.add_controller(click_gesture)
        
        self._populate_card_list(list_box)
        
        # Set margins
        list_box.set_margin_start(UIConstants.CARD_LIST_MARGIN)
        list_box.set_margin_end(UIConstants.CARD_LIST_MARGIN)
        list_box.set_margin_top(UIConstants.CARD_LIST_PADDING_VERTICAL)
        list_box.set_margin_bottom(UIConstants.CARD_LIST_PADDING_VERTICAL)
        
        # Wrap in scrolled window
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled_window.set_child(list_box)
        
        self.list_box = list_box
        return scrolled_window

    def _populate_card_list(self, list_box: Gtk.ListBox) -> None:
        """Populate the card list with all available cards.
        
        Args:
            list_box: List box to populate
        """
        logger.debug(f"Populating card selection list with {self.app.card_db.count} cards")
        for card in sorted(self.app.card_db, key=lambda c: c.view_name):
            row = self._create_card_action_row(card)
            list_box.append(row)

    def _create_card_action_row(self, card: Card) -> Adw.ActionRow:
        """Create an action row for a card.
        
        Args:
            card: Card to create row for
            
        Returns:
            Configured action row
        """
        row = Adw.ActionRow()
        row.card = card  # Store card reference
        row.set_title(card.view_name)
        row.set_activatable(True)
        
        # Add card thumbnail
        thumbnail = CardArtwork(self.window, card, UIConstants.CARD_THUMBNAIL_WIDTH, UIConstants.CARD_THUMBNAIL_HEIGHT)
        row.add_prefix(thumbnail)
        
        # Add info button
        info_button = self._create_info_button(card)
        row.add_suffix(info_button)
        
        return row

    def _create_info_button(self, card: Card) -> Gtk.Button:
        """Create info button for card row.
        
        Args:
            card: Card for the info button
            
        Returns:
            Configured info button
        """
        info_button = Gtk.Button()
        info_button.set_icon_name("dialog-information-symbolic")
        info_button.add_css_class("flat")
        info_button.add_css_class("circular")
        info_button.connect("clicked", self._on_card_info_button_clicked, card)
        return info_button
    
    def _create_stats_info_view(self) -> Gtk.Box:
        """Create the detailed card stats view.
        
        Returns:
            Box containing the stats view components
        """
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        
        # Header with back button
        header_bar = self._create_stats_header()
        content.append(header_bar)
        
        # Large card artwork display
        card_artwork = CardArtwork(self.window, None, UIConstants.CARD_THUMBNAIL_WIDTH * UIConstants.STATS_ARTWORK_SCALE, UIConstants.CARD_THUMBNAIL_HEIGHT * UIConstants.STATS_ARTWORK_SCALE)
        card_artwork.set_halign(Gtk.Align.CENTER)
        content.append(card_artwork)

        # Limit break selector with add button
        limit_break_selector = self._create_limit_break_selector()
        content.append(limit_break_selector)
        
        # Separator
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        content.append(separator)
        
        # Stats display area (placeholder for now)
        stats_scrolled_window = Gtk.ScrolledWindow()
        content.append(stats_scrolled_window)
        
        return content

    def _create_stats_header(self) -> Adw.HeaderBar:
        """Create header bar for stats view with back button.
        
        Returns:
            Configured header bar
        """
        header_bar = Adw.HeaderBar()
        header_bar.add_css_class("flat")
        
        back_button = Gtk.Button()
        back_button.set_icon_name("go-previous-symbolic")
        back_button.add_css_class("flat")
        back_button.connect("clicked", self._on_stats_info_view_back_button_clicked)
        header_bar.pack_start(back_button)
        
        return header_bar

    def _create_limit_break_selector(self) -> Gtk.Box:
        """Create limit break selector with slider and add button.
        
        Returns:
            Box containing selector components
        """
        limit_break_selector = Gtk.Box()
        limit_break_selector.set_halign(Gtk.Align.CENTER)
        
        # Limit break slider
        current_value = self.app.card_inspector.limit_break
        slider_adjustment = Gtk.Adjustment(
            value=current_value, 
            lower=CardConstants.MIN_LIMIT_BREAKS, 
            upper=CardConstants.MAX_LIMIT_BREAKS, 
            step_increment=1, 
            page_increment=1
        )
        slider_scale = Gtk.Scale(
            orientation=Gtk.Orientation.HORIZONTAL, 
            adjustment=slider_adjustment
        )
        slider_scale.set_draw_value(False)
        slider_scale.set_round_digits(0)
        
        # Add marks for each limit break level
        for i in range(CardConstants.MAX_LIMIT_BREAKS + 1):
            slider_scale.add_mark(i, Gtk.PositionType.BOTTOM, str(i))

        slider_scale.connect("value-changed", self._on_stats_info_view_slider_changed)
        limit_break_selector.append(slider_scale)
        
        # Add button
        add_button = Gtk.Button()
        add_button.set_icon_name("list-add-symbolic")
        add_button.add_css_class("flat")
        add_button.connect("clicked", self._on_stats_info_view_add_button_clicked)
        limit_break_selector.append(add_button)
        
        return limit_break_selector

    # Event handlers for deck changes
    def _on_active_deck_card_added(self, deck_list, **kwargs) -> None:
        """Handle when a card is added to the active deck.
        
        Args:
            deck_list: DeckList that triggered the event
            **kwargs: Event parameters including 'card'
        """
        card = kwargs.get('card')
        if card:
            for row in self.action_rows:
                if row.card == card:
                    self._hide_row(row)
                    break

    def _on_active_deck_card_removed(self, deck_list, **kwargs) -> None:
        """Handle when a card is removed from the active deck.
        
        Args:
            deck_list: DeckList that triggered the event
            **kwargs: Event parameters including 'card'
        """
        card = kwargs.get('card')
        if card:
            for row in self.action_rows:
                if row.card == card:
                    self._show_row(row)
                    break

    def _on_active_deck_deactivated(self, deck_list, **kwargs) -> None:
        """Handle when active deck is deactivated.
        
        Args:
            deck_list: DeckList that triggered the event
            **kwargs: Event parameters
        """
        self.list_box.set_visible(False)
    
    def _on_active_deck_activated(self, deck_list, **kwargs) -> None:
        """Handle when active deck is activated.
        
        Args:
            deck_list: DeckList that triggered the event
            **kwargs: Event parameters
        """
        self.refresh_all_action_rows()
        self.list_box.set_visible(True)

    def _on_card_inspector_changed(self, card_inspector: CardInspector, **kwargs) -> None:
        """Handle when card stats selection changes.
        
        Args:
            card_inspector: CardInspector instance that changed
            **kwargs: Event parameters including 'card' and 'prev_card'
        """
        # TODO: Update the large artwork display when card changes
        # This would be implemented when stats view is fully developed
        to_card_id = kwargs.get("card").id
        from_card_id = kwargs.get("prev_card").id if kwargs.get("prev_card") else "none"
        logger.debug(f"Callback on info panel updates from card {to_card_id} to card {from_card_id}")

    # UI event handlers
    def _on_card_row_activated(self, list_box: Gtk.ListBox, row: Adw.ActionRow) -> None:
        """Handle when a card row is activated (clicked).
        
        Args:
            list_box: List box containing the row
            row: Activated action row
        """
        active_deck = self.app.deck_list.active_deck
        if not active_deck:
            logger.error(f"No active deck")
            return

        logger.debug(f"Try adding card {row.card.id} to active deck from row '{row.get_title()}'")
        active_deck.add_card(row.card)

    
    def _on_card_list_view_clicked(self, gesture: Gtk.GestureClick, n_press: int, x: float, y: float, list_box: Gtk.ListBox) -> None:
        """Handle clicking on the card list view.
        
        Args:
            gesture: Click gesture
            n_press: Number of presses
            x: X coordinate
            y: Y coordinate
            list_box: List box that was clicked
        """
        split_view = list_box.get_ancestor(Adw.NavigationSplitView)
        if split_view:
            split_view.set_show_content(True)
    
    def _on_card_info_button_clicked(self, info_button: Gtk.Button, card: Card) -> None:
        """Handle clicking the info button on a card.
        
        Args:
            info_button: Info button that was clicked
            card: Card to show info for
        """
        self.app.card_inspector.card = card
        view_stack = info_button.get_ancestor(Adw.ViewStack)
        if view_stack:
            view_stack.set_visible_child_name("stats_info_view")
    
    def _on_stats_info_view_back_button_clicked(self, button: Gtk.Button) -> None:
        """Handle clicking the back button in stats info view.
        
        Args:
            button: Back button that was clicked
        """
        view_stack = button.get_ancestor(Adw.ViewStack)
        if view_stack:
            view_stack.set_visible_child_name("card_selection_view")
    
    def _on_stats_info_view_slider_changed(self, slider: Gtk.Scale) -> None:
        """Handle limit break slider change in stats info view.
        
        Args:
            slider: Scale widget that changed
        """
        limit_break = int(slider.get_value())
        self.app.card_inspector.limit_break = limit_break
    
    def _on_stats_info_view_add_button_clicked(self, button: Gtk.Button) -> None:
        """Handle clicking the add button in stats info view.
        
        Args:
            button: Add button that was clicked
        """
        card_inspector = self.app.card_inspector
        active_deck = self.app.deck_list.active_deck
        logger.debug(f"Try adding card {card_inspector.card.id} at limit break {card_inspector.limit_break} to active deck from info panel")
        active_deck.add_card(card_inspector.card, card_inspector.limit_break)
