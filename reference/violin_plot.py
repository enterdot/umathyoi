#!/usr/bin/env python3
"""
Clean Violin Plot Visualization - No thresholds, just pure distribution
"""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Gdk
import cairo
import math
import random

class ViolinPlotWidget(Gtk.DrawingArea):
    """Clean violin plot showing distribution shape"""
    
    def __init__(self, values, title=""):
        super().__init__()
        self.values = sorted(values)
        self.title = title
        self.min_val = 5
        self.max_val = 75
        self.set_size_request(300, 100)
        self.set_draw_func(self.on_draw)
        
    def calculate_kde(self, bandwidth=3.0):
        """Simple kernel density estimation using Gaussian kernels"""
        val_range = self.max_val - self.min_val
        
        # Create evaluation points
        n_points = 100
        x_points = [self.min_val + (i / n_points) * val_range for i in range(n_points + 1)]
        densities = []
        
        for x in x_points:
            # Gaussian kernel density estimation
            density = 0
            for val in self.values:
                diff = (x - val) / bandwidth
                density += math.exp(-0.5 * diff * diff)
            densities.append(density / (len(self.values) * bandwidth * math.sqrt(2 * math.pi)))
        
        return x_points, densities
    
    def on_draw(self, area, ctx, width, height):
        if not self.values:
            return
            
        padding = 30
        plot_width = width - 2 * padding
        plot_height = height - 40
        y_center = plot_height / 2 + 10
        
        val_range = self.max_val - self.min_val
        
        # Calculate KDE
        x_points, densities = self.calculate_kde(bandwidth=val_range * 0.06)
        max_density = max(densities) if densities else 1
        
        # Scale for violin width
        max_width = plot_height * 0.45
        
        def val_to_x(val):
            return padding + ((val - self.min_val) / val_range) * plot_width
        
        def density_to_y_offset(density):
            return (density / max_density) * max_width
        
        # Build violin path
        ctx.new_path()
        
        # Upper half
        for i in range(len(x_points)):
            x = val_to_x(x_points[i])
            y_offset = density_to_y_offset(densities[i])
            
            if i == 0:
                ctx.move_to(x, y_center)
            ctx.line_to(x, y_center - y_offset)
        
        # Lower half (mirror)
        for i in range(len(x_points) - 1, -1, -1):
            x = val_to_x(x_points[i])
            y_offset = density_to_y_offset(densities[i])
            ctx.line_to(x, y_center + y_offset)
        
        ctx.close_path()
        
        # Fill with subtle gradient
        ctx.set_source_rgba(0.3, 0.5, 0.8, 0.4)
        ctx.fill_preserve()
        
        # Stroke outline
        ctx.set_source_rgba(0.2, 0.3, 0.6, 0.9)
        ctx.set_line_width(2)
        ctx.stroke()
        
        # Draw center line
        ctx.set_source_rgba(0, 0, 0, 0.2)
        ctx.move_to(padding, y_center)
        ctx.line_to(width - padding, y_center)
        ctx.set_line_width(1)
        ctx.stroke()
        
        # Find peaks (local maxima) in the density
        peaks = []
        for i in range(1, len(densities) - 1):
            # Check if this point is higher than both neighbors
            if densities[i] > densities[i-1] and densities[i] > densities[i+1]:
                # Additional check: must be significant peak (>20% of max density)
                if densities[i] > max_density * 0.2:
                    peaks.append((x_points[i], densities[i]))
        
        # Draw peak indicators
        ctx.set_source_rgba(0.2, 0.2, 0.2, 0.8)
        ctx.set_line_width(2.5)
        
        for peak_val, peak_density in peaks:
            peak_x = val_to_x(peak_val)
            ctx.move_to(peak_x, y_center - max_width * 0.7)
            ctx.line_to(peak_x, y_center + max_width * 0.7)
            ctx.stroke()
        
        # Draw axis
        ctx.set_source_rgba(0.5, 0.5, 0.5, 0.8)
        ctx.move_to(padding, height - 15)
        ctx.line_to(width - padding, height - 15)
        ctx.set_line_width(1)
        ctx.stroke()
        
        # Labels
        ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        ctx.set_font_size(10)
        ctx.set_source_rgb(0.3, 0.3, 0.3)
        
        ctx.move_to(padding, height - 3)
        ctx.show_text(str(self.min_val))
        
        ctx.move_to(width - padding - 15, height - 3)
        ctx.show_text(str(self.max_val))
        
        # Peak labels
        if peaks:
            peak_text = "peak" + ("s" if len(peaks) > 1 else "") + ": " + ", ".join([f"{int(p[0])}" for p in peaks])
            extents = ctx.text_extents(peak_text)
            ctx.move_to((width - extents.width) / 2, height - 3)
            ctx.show_text(peak_text)

class MainWindow(Adw.ApplicationWindow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_title("Violin Plot Distribution Viewer")
        self.set_default_size(700, 800)
        
        # Dataset 1: Spiky - mostly low values with rare high spikes
        dataset1 = (
            [random.randint(8, 18) for _ in range(35)] +  # Cluster at low end
            [random.randint(15, 25) for _ in range(10)] +  # Small middle group
            [random.randint(65, 74) for _ in range(8)]     # Rare high values
        )
        
        # Dataset 2: Consistent - most values slightly below average, some above
        dataset2 = (
            [random.randint(25, 35) for _ in range(30)] +  # Main cluster below avg
            [random.randint(35, 45) for _ in range(15)] +  # Some at average
            [random.randint(45, 60) for _ in range(8)]     # Few above average
        )
        
        # Dataset 3: Almost flat - heavily concentrated in below-average range
        dataset3 = (
            [random.randint(15, 30) for _ in range(45)] +  # Heavy concentration
            [random.randint(30, 40) for _ in range(8)]     # Small tail
        )
        
        # Dataset 4: Bimodal - two distinct peaks (low and high)
        dataset4 = (
            [random.randint(10, 20) for _ in range(20)] +  # Low cluster
            [random.randint(55, 70) for _ in range(25)] +  # High cluster
            [random.randint(30, 45) for _ in range(8)]     # Gap filler
        )
        
        # Dataset 5: Right-skewed - gradual increase with long tail to high values
        dataset5 = (
            [random.randint(20, 30) for _ in range(15)] +
            [random.randint(30, 40) for _ in range(20)] +
            [random.randint(40, 50) for _ in range(12)] +
            [random.randint(50, 65) for _ in range(8)] +
            [random.randint(65, 74) for _ in range(3)]
        )
        
        # Dataset 6: U-shaped - values at extremes, few in middle
        dataset6 = (
            [random.randint(5, 15) for _ in range(18)] +   # Low extreme
            [random.randint(25, 35) for _ in range(8)] +   # Sparse middle
            [random.randint(60, 74) for _ in range(22)]    # High extreme
        )
        
        # Dataset 7: Normal-ish - bell curve centered around 40
        dataset7 = (
            [random.randint(15, 25) for _ in range(8)] +
            [random.randint(25, 35) for _ in range(15)] +
            [random.randint(35, 45) for _ in range(20)] +
            [random.randint(45, 55) for _ in range(15)] +
            [random.randint(55, 65) for _ in range(8)]
        )
        
        # Dataset 8: Heavy high concentration - opposite of dataset 1
        dataset8 = (
            [random.randint(5, 15) for _ in range(8)] +    # Rare low values
            [random.randint(35, 50) for _ in range(12)] +  # Middle transition
            [random.randint(55, 70) for _ in range(35)]    # Heavy high cluster
        )
        
        # Create scrolled window
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        
        # Main box
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=25)
        main_box.set_margin_top(20)
        main_box.set_margin_bottom(20)
        main_box.set_margin_start(20)
        main_box.set_margin_end(20)
        
        # Add title
        title = Gtk.Label()
        title.set_markup("<span size='x-large' weight='bold'>Distribution Patterns</span>")
        title.set_margin_bottom(10)
        main_box.append(title)
        
        # Add datasets
        datasets = [
            ("Spiky Pattern: Mostly low with rare high spikes", dataset1),
            ("Consistent Pattern: Clustered below average", dataset2),
            ("Flat Pattern: Heavy concentration in low range", dataset3),
            ("Bimodal Pattern: Two distinct clusters", dataset4),
            ("Right-Skewed: Gradual tail to high values", dataset5),
            ("U-Shaped: Values at extremes", dataset6),
            ("Normal Distribution: Bell curve around center", dataset7),
            ("High Concentration: Mostly high values", dataset8)
        ]
        
        for desc, data in datasets:
            # Dataset description
            label = Gtk.Label()
            label.set_markup(f"<b>{desc}</b>")
            label.set_xalign(0)
            main_box.append(label)
            
            # Violin plot
            violin = ViolinPlotWidget(data, desc)
            main_box.append(violin)
            
            # Stats summary
            mean_val = sum(data) / len(data)
            median_val = sorted(data)[len(data) // 2]
            stats = Gtk.Label()
            stats.set_markup(f"<small>Mean: {mean_val:.1f} | Median: {median_val} | Count: {len(data)}</small>")
            stats.set_xalign(0)
            stats.set_margin_bottom(5)
            main_box.append(stats)
            
            # Separator
            main_box.append(Gtk.Separator())
        
        scrolled.set_child(main_box)
        self.set_content(scrolled)

class Application(Adw.Application):
    def __init__(self):
        super().__init__(application_id="com.example.ViolinViewer")
        
    def do_activate(self):
        win = MainWindow(application=self)
        win.present()

if __name__ == "__main__":
    app = Application()
    app.run(None)
