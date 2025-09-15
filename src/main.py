#!/usr/bin/env python

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Gdk', '4.0')
gi.require_version('Adw', '1')

from application import MainApplication

# Application constants
app_name = "Umathyoi"
app_version = "0.0"
app_reverse_dns = "org.example.umathyoi"


if __name__ == '__main__':
    app = MainApplication(app_name, app_version, app_reverse_dns)
    app.run()
