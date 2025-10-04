import gi
gi.require_version('Gdk', '4.0')
gi.require_version('GdkPixbuf', '2.0')
from gi.repository import GLib, Gdk, GdkPixbuf

def texture_from_pixbuf(pixbuf: GdkPixbuf.Pixbuf) -> Gdk.Texture:
    """Convert a GdkPixbuf to a GdkTexture."""
    width = pixbuf.get_width()
    height = pixbuf.get_height()
    rowstride = pixbuf.get_rowstride()
    has_alpha = pixbuf.get_has_alpha()
    
    # Get pixel data as bytes
    pixels = pixbuf.get_pixels()
    bytes_data = GLib.Bytes.new(pixels)
    
    # Determine memory format
    if has_alpha:
        format = Gdk.MemoryFormat.R8G8B8A8
    else:
        format = Gdk.MemoryFormat.R8G8B8
    
    return Gdk.MemoryTexture.new(width, height, format, bytes_data, rowstride)
