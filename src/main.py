#!/usr/bin/env python

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Gdk', '4.0')
gi.require_version('Adw', '1')

from application import MainApplication
from utils import ApplicationConstants

if __name__ == '__main__':
    app = MainApplication(ApplicationConstants.NAME, ApplicationConstants.VERSION, ApplicationConstants.REVERSE_DNS)
    app.run()
