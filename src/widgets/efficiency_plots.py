import logging

logger = logging.getLogger(__name__)

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw
import cairo
import math

from modules import FacilityType, StatType
from common import auto_title_from_instance


class ViolinPlot(Gtk.DrawingArea):
    """Violin plot widget showing distribution of stat gains."""

    def __init__(self, values: list[int], title: str, min_val: int, max_val: int):
        super().__init__()
        self.values = sorted(values) if values else []
        self.title = title
        self.min_val = min_val
        self.max_val = max_val
        self.set_size_request(250, 80)
        self.set_draw_func(self.on_draw)

    def calculate_kde(self, bandwidth: float = 3.0) -> tuple[list[float], list[float]]:
        """Kernel density estimation using Gaussian kernels."""
        if not self.values:
            return [], []

        val_range = self.max_val - self.min_val
        if val_range == 0:
            val_range = 1

        # Create evaluation points
        n_points = 100
        x_points = [self.min_val + (i / n_points) * val_range for i in range(n_points + 1)]
        densities = []

        for x in x_points:
            density = 0
            for val in self.values:
                diff = (x - val) / bandwidth
                density += math.exp(-0.5 * diff * diff)
            densities.append(density / (len(self.values) * bandwidth * math.sqrt(2 * math.pi)))

        return x_points, densities

    def on_draw(self, area, ctx, width, height):
        if not self.values:
            # Draw empty state
            ctx.set_source_rgba(0.5, 0.5, 0.5, 0.3)
            ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
            ctx.set_font_size(12)
            text = "No data"
            extents = ctx.text_extents(text)
            ctx.move_to((width - extents.width) / 2, height / 2)
            ctx.show_text(text)
            return

        padding = 30
        plot_width = width - 2 * padding
        plot_height = height - 30
        y_center = plot_height / 2 + 5

        val_range = self.max_val - self.min_val
        if val_range == 0:
            val_range = 1

        # Calculate KDE
        x_points, densities = self.calculate_kde(bandwidth=val_range * 0.06)
        max_density = max(densities) if densities else 1
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

        # Fill with gradient
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

        # Find and draw peaks
        peaks = []
        for i in range(1, len(densities) - 1):
            if densities[i] > densities[i - 1] and densities[i] > densities[i + 1]:
                if densities[i] > max_density * 0.2:
                    peaks.append((x_points[i], densities[i]))

        ctx.set_source_rgba(0.2, 0.2, 0.2, 0.8)
        ctx.set_line_width(2.5)
        for peak_val, peak_density in peaks:
            peak_x = val_to_x(peak_val)
            ctx.move_to(peak_x, y_center - max_width * 0.7)
            ctx.line_to(peak_x, y_center + max_width * 0.7)
            ctx.stroke()

        # Draw axis
        ctx.set_source_rgba(0.5, 0.5, 0.5, 0.8)
        ctx.move_to(padding, height - 10)
        ctx.line_to(width - padding, height - 10)
        ctx.set_line_width(1)
        ctx.stroke()

        # Labels
        ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        ctx.set_font_size(10)
        ctx.set_source_rgb(0.3, 0.3, 0.3)

        # Min label
        ctx.move_to(padding, height - 1)
        ctx.show_text(str(self.min_val))

        # Max label
        max_text = str(self.max_val)
        extents = ctx.text_extents(max_text)
        ctx.move_to(width - padding - extents.width, height - 1)
        ctx.show_text(max_text)

        # Peak labels
        if peaks:
            peak_text = "peak" + ("s" if len(peaks) > 1 else "") + ": " + ", ".join([f"{int(p[0])}" for p in peaks])
            extents = ctx.text_extents(peak_text)
            ctx.move_to((width - extents.width) / 2, height - 1)
            ctx.show_text(peak_text)


class EfficiencyPlots(Adw.Bin):
    """Widget for displaying efficiency calculation results as violin plots."""

    SPACING: int = 10
    MARGIN: int = 20

    def __init__(self, window):
        """Initialize efficiency plots widget."""
        super().__init__()
        self.app = window.app
        self.window = window
        self.calculator = self.app.efficiency_calculator

        self.setup_ui()
        self.connect_signals()

        logger.debug(f"{auto_title_from_instance(self)} initialized")

    def setup_ui(self) -> None:
        """Set up the efficiency plots UI components."""
        self.scrolled_window = Gtk.ScrolledWindow()
        self.scrolled_window.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.scrolled_window.set_vexpand(True)

        self.main_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.main_container.set_spacing(EfficiencyPlots.SPACING)
        self.main_container.set_margin_start(EfficiencyPlots.MARGIN)
        self.main_container.set_margin_end(EfficiencyPlots.MARGIN)
        self.main_container.set_margin_top(EfficiencyPlots.MARGIN)
        self.main_container.set_margin_bottom(EfficiencyPlots.MARGIN)

        # Initial empty state
        self._show_empty_state()

        self.scrolled_window.set_child(self.main_container)
        self.set_child(self.scrolled_window)

    def connect_signals(self) -> None:
        """Connect to calculator events."""
        self.calculator.calculation_finished.subscribe(self._on_calculation_finished)

    def _show_empty_state(self) -> None:
        """Show message when no calculation has been run."""
        empty_label = Gtk.Label(label="Run a calculation to see results")
        empty_label.add_css_class("dim-label")
        self.main_container.append(empty_label)

    def _on_calculation_finished(self, calculator, **kwargs) -> None:
        """Update plots when calculation finishes."""
        logger.debug("Updating efficiency plots with new results")
        self.update_plots()

    def update_plots(self) -> None:
        """Update violin plots with latest calculator results."""
        # Clear existing plots (keep title)
        child = self.main_container.get_first_child()
        while child:
            next_child = child.get_next_sibling()
            if child != self.main_container.get_first_child():  # Keep title
                self.main_container.remove(child)
            child = next_child

        # Get results
        if not hasattr(self.calculator, "_aggregated_stat_gains"):
            self._show_empty_state()
            return

        results = self.calculator.get_results()
        if not results:
            self._show_empty_state()
            return

        # Create plots for each facility
        for facility_type in FacilityType:
            facility_group = Adw.PreferencesGroup()
            facility_group.set_title(f"{facility_type.name.title()} Training")

            # Get raw data for this facility
            facility_gains = self.calculator._aggregated_stat_gains[facility_type]
            facility_skill_points = self.calculator._aggregated_skill_points[facility_type]

            # Create plots for each stat
            for stat_type in StatType:
                values = facility_gains[stat_type]
                if not values or all(v == 0 for v in values):
                    continue

                stat_data = results["per_facility"][facility_type]["stats"][stat_type]

                # Create row with stats and violin plot
                row = Adw.ActionRow(title=stat_type.name.title())
                row.set_subtitle(f"Mean: {stat_data['mean']:.1f} | Range: {stat_data['min']}-{stat_data['max']}")

                # Create violin plot
                violin = ViolinPlot(values, stat_type.name, stat_data["min"], stat_data["max"])
                row.add_suffix(violin)

                facility_group.add(row)

            # Skill points plot
            if facility_skill_points and not all(v == 0 for v in facility_skill_points):
                sp_data = results["per_facility"][facility_type]["skill_points"]

                row = Adw.ActionRow(title="Skill Points")
                row.set_subtitle(f"Mean: {sp_data['mean']:.1f} | Range: {sp_data['min']}-{sp_data['max']}")

                violin = ViolinPlot(facility_skill_points, "Skill Points", sp_data["min"], sp_data["max"])
                row.add_suffix(violin)

                facility_group.add(row)

            self.main_container.append(facility_group)
