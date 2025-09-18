import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw
from utils import auto_title_from_instance


class Placeholder(Gtk.Box):
    """A placeholder widget for blocking out app layouts."""
    
    def __init__(self, name: str, description: str = "", **kwargs):
        kwargs.setdefault('orientation', Gtk.Orientation.VERTICAL)
        kwargs.setdefault('spacing', 6)
        kwargs.setdefault('halign', Gtk.Align.CENTER)
        kwargs.setdefault('valign', Gtk.Align.CENTER)
        
        super().__init__(**kwargs)
        self.set_name(f"{auto_title_from_instance(self)} for {name}")
        
        self.name_label = self.create_name_label(name)
        self.append(self.name_label)

        if description:
            self.description_label = self.create_description_label(description)            
            self.append(self.description_label)
        else:
            self.description_label = None

    @property
    def name(self) -> str:
        return self.name_label.get_label()
    
    @name.setter
    def name(self, value: str):
        self.name_label.set_text(value)
    
    @property
    def description(self) -> str:
        if self.description_label is None:
            return ""
        return self.description_label.get_label()
    
    @description.setter
    def description(self, value: str):
        if value:
            if self.description_label is None:
                self.description_label = self.create_description_label(value)
                self.append(self.description_label)
            else:
                self.description_label.set_text(value)
        else:
            if self.description_label is not None:
                self.remove(self.description_label)
                self.description_label = None
    
    def create_description_label(self, description: str):
        description_label = Gtk.Label(label=description)
        description_label.set_wrap(True)
        description_label.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        description_label.set_justify(Gtk.Justification.CENTER)
        description_label.add_css_class('dim-label')
        return description_label

    def create_name_label(self, name: str):
        name_label = Gtk.Label(label=name)
        name_label.set_wrap(True)
        name_label.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        name_label.set_justify(Gtk.Justification.CENTER)
        name_label.add_css_class('title-3')
        return name_label
