import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw

from modules import Card, CardStats
from widgets import CardArtwork
from utils import auto_tag_from_instance, auto_title_from_instance

class CardSelection(Adw.Bin):
    
    def __init__(self, window):
        super().__init__()
        self.app = window.app
        self.window = window

        self.setup_ui()
        self.connect_signals()

    @property
    def list_box(self):
        return self._list_box

    @list_box.setter
    def list_box(self, list_box):
        self._list_box = list_box

    @property
    def action_rows(self):
        row = self.list_box.get_first_child()
        while row:
            yield row
            row = row.get_next_sibling()  

    def setup_ui(self):
        view_stack = Adw.ViewStack()
        view_stack.add_named(self._create_card_list_view(), "card_selection_view")
        view_stack.add_named(self._create_stats_info_view(), "stats_info_view")
        self.set_child(view_stack)

    def connect_signals(self):
        self.app.deck_list.slot_deactivated.subscribe(self._on_active_deck_deactivated)
        self.app.deck_list.slot_activated.subscribe(self._on_active_deck_activated)

    def refresh_all_action_rows(self):
        for row in self.action_rows:
            if row.card in self.app.deck_list.active_deck:
                self.select_row(row)
            else:
                self.deselect_row(row)

    def select_row(self, row):
        row.set_visible(False)
    
    def deselect_row(self, row):
        row.set_visible(True)

    def _create_card_list_view(self):
        list_box = Gtk.ListBox()
        list_box.set_selection_mode(Gtk.SelectionMode.NONE)
        list_box.add_css_class("boxed-list-separate")
        
        list_box.connect("row-activated", self._on_card_row_activated)
        
        click_gesture = Gtk.GestureClick()
        click_gesture.connect("pressed", self._on_card_list_view_clicked, list_box)
        list_box.add_controller(click_gesture)
        
        cards = self.app.card_db.get_all_cards()
        for card in sorted(cards, key=lambda c: c.view_name):
            row = Adw.ActionRow()
            row.card = card
            row.set_title(card.view_name)
            row.set_activatable(True)
            
            thumbnail = CardArtwork(card, 45, 60)
            row.add_prefix(thumbnail)
            
            info_button = Gtk.Button()
            info_button.set_icon_name("dialog-information-symbolic")
            info_button.add_css_class("flat")
            info_button.add_css_class("circular")
            info_button.connect("clicked", self._on_card_info_button_clicked, card)
            row.add_suffix(info_button)
            list_box.append(row)
        
        list_box.set_margin_start(18)
        list_box.set_margin_end(18)
        list_box.set_margin_top(12)
        list_box.set_margin_bottom(12)
        
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled_window.set_child(list_box)
        
        self.list_box = list_box
        return scrolled_window
    
    def _create_stats_info_view(self):
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        
        header_bar = Adw.HeaderBar()
        header_bar.add_css_class("flat")
        back_button = Gtk.Button()
        back_button.set_icon_name("go-previous-symbolic")
        back_button.add_css_class("flat")
        back_button.connect("clicked", self._on_stats_info_view_back_button_clicked)
        header_bar.pack_start(back_button)
        
        content.append(header_bar)
        
        # Artwork display
        card_artwork = CardArtwork(None, 45*3, 60*3)
        card_artwork.set_halign(Gtk.Align.CENTER)
        
        content.append(card_artwork)

        # Limit Break selector
        limit_break_selector = Gtk.Box()
        limit_break_selector.set_halign(Gtk.Align.CENTER)
        
        value = self.app.card_stats.get_limit_break()
        slider_adjustment = Gtk.Adjustment(value=value, lower=0, upper=4, step_increment=1, page_increment=1)
        slider_scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=slider_adjustment)
        slider_scale.set_draw_value(False)
        slider_scale.set_round_digits(0)
        
        #TODO: the max limit breaks should be stored somewhere instead of being hardcoded
        for i in range(5):
            slider_scale.add_mark(i, Gtk.PositionType.BOTTOM, str(i))

        slider_scale.connect("value-changed", self._on_stats_info_view_slider_changed)
        limit_break_selector.append(slider_scale)
        
        add_button = Gtk.Button()
        add_button.set_icon_name("list-add-symbolic")
        add_button.add_css_class("flat")
        add_button.connect("clicked", self._on_stats_info_view_add_button_clicked)
        limit_break_selector.append(add_button)
        
        content.append(limit_break_selector)
        
        # Separator
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        
        content.append(separator)
        
        # Stats display area
        stats_scrolled_window = Gtk.ScrolledWindow()
        self.app.card_stats.card_changed.subscribe(self._update_stats_scrolled_window)

        content.append(stats_scrolled_window)
        
        return content

    # Callback events
    def _update_stats_scrolled_window(self, caller, **kwargs):
        print(f"{caller}: {kwargs} for {self.app.card_stats}")

    def _on_active_deck_deactivated(self, caller, **kwargs):
        self.list_box.set_visible(False)
    
    def _on_active_deck_activated(self, caller, **kwargs):
        self.refresh_all_action_rows()
        self.list_box.set_visible(True)
    
    # UI events

    def _on_card_row_activated(self, list_box, row):
        if self.app.deck_list.active_deck.is_full:
            return
        if self.app.deck_list.active_deck.add_card(row.card) is not None:
            self.select_row(row)
        elif self.app.deck_list.active_deck.remove_card(row.card) is not None:
            self.deselect_row(row)
        else:
            raise RuntimeError(f"Could not add or remove {row.card} to {self.app.deck_list.active_deck} even though it's not full") 
    
    def _on_card_list_view_clicked(self, gesture, n_press, x, y, list_box):
        split_view = list_box.get_ancestor(Adw.NavigationSplitView)
        split_view.set_show_content(True)
    
    def _on_card_info_button_clicked(self, info_button, card: Card):
        self.app.card_stats.card = card
        view_stack = info_button.get_ancestor(Adw.ViewStack)
        view_stack.set_visible_child_name("stats_info_view")
    
    def _on_stats_info_view_back_button_clicked(self, button):
        view_stack = button.get_ancestor(Adw.ViewStack)
        view_stack.set_visible_child_name("card_selection_view")
    
    def _on_stats_info_view_slider_changed(self, slider):
        limit_break = int(slider.get_value())
        self.app.card_stats.limit_break = limit_break
    
    def _on_stats_info_view_add_button_clicked(self, button):
        card_stats = self.app.card_stats
        print(f"Adding {card_stats.card.view_name} at limit break {card_stats.limit_break} to deck")
    

