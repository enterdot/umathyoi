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
        
        container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=40)
        
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
        self.carousel.connect("page-changed", self.on_page_changed)
        self.carousel.connect("notify::position", self.on_notify_position)
        self.window.connect("notify::default-width", self.on_window_width_changed)
        self.window.connect("notify::default-height", self.on_window_height_changed)

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
            
    def create_carousel_page(self, slot: int, deck: Deck):
        deck_grid = Gtk.Grid()
        deck_grid.set_row_spacing(24)
        deck_grid.set_column_spacing(24)

        for index, card, limit_break in deck:
            card_slot = self.create_card_slot(card, limit_break, index)
            deck_grid.attach(card_slot, index % 3, index // 3, 1, 1)
        
        return Adw.NavigationPage.new_with_tag(deck_grid, "Deck Carousel", "deck_carousel")
    
    def create_card_slot(self, card: Card, level: int, slot_index: int):
        """Create a card slot widget for the deck grid."""
        card_slot = CardSlot(card, level, 150, 200)
        # TODO: Implement, connect signals, etc...
        return card_slot
