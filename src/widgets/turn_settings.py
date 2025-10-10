import logging

logger = logging.getLogger(__name__)

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw

from modules import Mood, Facility, FacilityType, EfficiencyCalculator
from common import auto_title_from_instance


class TurnSettings(Adw.Bin):
    """Widget for configuring efficiency calculator turn settings."""

    MARGIN: int = 0
    SPACING: int = 10

    def __init__(self, window):
        """Initialize turn settings widget."""
        super().__init__()
        self.app = window.app
        self.window = window
        self.calculator: EfficiencyCalculator = self.app.efficiency_calculator

        self.setup_ui()
        self.connect_signals()

        logger.debug(f"{auto_title_from_instance(self)} initialized")

    def setup_ui(self) -> None:
        """Set up the turn settings UI components."""
        container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        container.set_margin_bottom(TurnSettings.MARGIN)
        container.set_spacing(TurnSettings.SPACING)

        # Title
        title = Gtk.Label(label="Turn Settings")
        title.add_css_class("title-3")
        title.set_halign(Gtk.Align.START)
        container.append(title)

        # Settings group
        settings_group = Adw.PreferencesGroup()

        # Mood selection
        self.mood_row = Adw.ComboRow(title="Mood")
        mood_model = Gtk.StringList()
        for mood in Mood:
            mood_model.append(str(mood))
        self.mood_row.set_model(mood_model)
        # Set to calculator's current mood
        self.mood_row.set_selected(self.calculator.mood.value + 2)
        settings_group.add(self.mood_row)

        # Max Energy spin button
        self.max_energy_row = Adw.ActionRow(title="Max Energy")
        self.max_energy_spin = Gtk.SpinButton(
            adjustment=Gtk.Adjustment(
                value=self.calculator.max_energy,
                lower=EfficiencyCalculator.MIN_MAX_ENERGY,
                upper=EfficiencyCalculator.MAX_ENERGY,
                step_increment=4,
                page_increment=4,
            )
        )
        self.max_energy_spin.set_digits(0)
        self.max_energy_row.add_suffix(self.max_energy_spin)
        settings_group.add(self.max_energy_row)

        # Energy slider
        self.energy_row = Adw.ActionRow(title="Energy")
        self.energy_adjustment = Gtk.Adjustment(
            value=self.calculator.energy,
            lower=EfficiencyCalculator.MIN_ENERGY,
            upper=self.calculator.max_energy,
            step_increment=5,
            page_increment=10,
        )
        self.energy_scale = Gtk.Scale(
            orientation=Gtk.Orientation.HORIZONTAL,
            adjustment=self.energy_adjustment,
        )
        self.energy_scale.set_hexpand(True)
        self.energy_scale.set_value_pos(Gtk.PositionType.RIGHT)
        self.energy_scale.set_digits(0)
        self.energy_row.add_suffix(self.energy_scale)
        settings_group.add(self.energy_row)

        # Fan count spin button
        self.fan_count_row = Adw.ActionRow(title="Fan Count")
        self.fan_count_spin = Gtk.SpinButton(
            adjustment=Gtk.Adjustment(
                value=self.calculator.fan_count,
                lower=EfficiencyCalculator.MIN_FANS,
                upper=EfficiencyCalculator.MAX_FANS,
                step_increment=10000,
                page_increment=100000,
            )
        )
        self.fan_count_spin.set_digits(0)
        self.fan_count_row.add_suffix(self.fan_count_spin)
        settings_group.add(self.fan_count_row)

        container.append(settings_group)

        # Facility levels group
        facility_group = Adw.PreferencesGroup()
        facility_group.set_title("Facility Levels")
        facility_group.set_description(
            "Set the training facility levels for the scenario"
        )

        # Create facility level controls
        self.facility_spins = {}
        for facility_type in FacilityType:
            row = Adw.ActionRow(title=f"{facility_type.name.title()} Facility")
            spin = Gtk.SpinButton(
                adjustment=Gtk.Adjustment(
                    value=self.calculator.facility_levels[facility_type],
                    lower=Facility.MIN_LEVEL,
                    upper=Facility.MAX_LEVEL,
                    step_increment=1,
                )
            )
            spin.set_digits(0)
            row.add_suffix(spin)
            facility_group.add(row)
            self.facility_spins[facility_type] = spin

        container.append(facility_group)

        self.set_child(container)

    def connect_signals(self) -> None:
        """Connect widget signals to update calculator settings."""
        self.mood_row.connect("notify::selected", self._on_mood_changed)
        self.energy_scale.connect("value-changed", self._on_energy_changed)
        self.max_energy_spin.connect(
            "value-changed", self._on_max_energy_changed
        )
        self.fan_count_spin.connect("value-changed", self._on_fan_count_changed)

        for facility_type, spin in self.facility_spins.items():
            spin.connect(
                "value-changed", self._on_facility_level_changed, facility_type
            )

    def _on_mood_changed(self, combo_row, param) -> None:
        """Handle mood selection change."""
        selected = combo_row.get_selected()
        mood = list(Mood)[selected]
        logger.debug(f"Mood changed to: {mood}")
        self.calculator.mood = mood

    def _on_energy_changed(self, scale) -> None:
        """Handle energy slider change."""
        energy = int(scale.get_value())
        logger.debug(f"Energy changed to: {energy}")
        self.calculator.energy = energy

    def _on_max_energy_changed(self, spin_button) -> None:
        """Handle max energy change."""
        max_energy = int(spin_button.get_value())
        logger.debug(f"Max energy changed to: {max_energy}")

        # Update calculator
        self.calculator.max_energy = max_energy

        # Update energy slider's upper bound
        self.energy_adjustment.set_upper(max_energy)

        # If current energy exceeds new max, clamp it
        if self.energy_adjustment.get_value() > max_energy:
            self.energy_adjustment.set_value(max_energy)

    def _on_fan_count_changed(self, spin_button) -> None:
        """Handle fan count change."""
        fan_count = int(spin_button.get_value())
        logger.debug(f"Fan count changed to: {fan_count}")
        self.calculator.fan_count = fan_count

    def _on_facility_level_changed(
        self, spin_button, facility_type: FacilityType
    ) -> None:
        """Handle facility level change."""
        level = int(spin_button.get_value())
        logger.debug(f"{facility_type.name} facility level changed to: {level}")

        # Update the specific facility level in the calculator
        facility_levels = self.calculator.facility_levels.copy()
        facility_levels[facility_type] = level
        self.calculator.facility_levels = facility_levels
