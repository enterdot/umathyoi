#!/usr/bin/env python

import warnings

warnings.filterwarnings("error")

from common import setup_logging, get_logger

setup_logging("debug")
logger = get_logger(__name__)

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
gi.require_version("Adw", "1")

from application import MainApplication

if __name__ == "__main__":
    app = MainApplication()
    app.run()
