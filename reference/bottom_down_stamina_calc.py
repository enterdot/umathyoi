#!/usr/bin/env python3
"""
Uma Musume Stamina Calculator - Minimal Test Version
Building from the bottom up with hardcoded values
"""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw
import math

class UmaMusumeCalculator:
    """Minimal calculator - building from the end formula backwards"""
    
    def __init__(self):
        # =============================================================================
        # TEST CONFIGURATION - Modify these values to test different scenarios
        # =============================================================================
        
        # Base stats
        self.speed = 1100
        self.stamina = 400
        self.power = 1100
        self.guts = 350
        self.wisdom = 350
        
        # Race parameters
        self.distance = 3000  # meters
        self.style = 'End'   # Front, Pace, Late, End
        self.mood = 'Bad'  # Awful, Bad, Normal, Good, Great
        
        # Aptitudes
        self.track_aptitude = 'B'     # S, A, B, C, D, E, F, G
        self.distance_aptitude = 'B'  # S, A, B, C, D, E, F, G
        self.style_aptitude = 'B'     # S, A, B, C, D, E, F, G
        
        # Conditions
        self.surface = 'Dirt'      # Turf, Dirt
        self.condition = 'Heavy'    # Firm, Good, Soft, Heavy
        self.recovery_percent = 0.0  # Net recovery effect (can be negative for debuffs)
        
        # =============================================================================
        # LOOKUP TABLES - Don't modify unless adding new game data
        # =============================================================================
        
        # Aptitude lookup table
        self.aptitude_data = {
            'S': {'speed': 1.05, 'accel': 1.0},
            'A': {'speed': 1.0, 'accel': 1.0},
            'B': {'speed': 0.9, 'accel': 1.0},
            'C': {'speed': 0.8, 'accel': 1.0},
            'D': {'speed': 0.6, 'accel': 1.0},
            'E': {'speed': 0.4, 'accel': 0.6},
            'F': {'speed': 0.2, 'accel': 0.5},
            'G': {'speed': 0.1, 'accel': 0.4}
        }
        
        # Mood lookup table
        self.mood_data = {
            'Great': 1.04,
            'Good': 1.02,
            'Normal': 1.0,
            'Bad': 0.98,
            'Awful': 0.96
        }
        
        # Style aptitude lookup table
        self.style_aptitude_data = {
            'S': 1.1,
            'A': 1.0,
            'B': 0.85,
            'C': 0.75,
            'D': 0.6,
            'E': 0.4,
            'F': 0.2,
            'G': 0.1
        }
        
        # Surface/condition lookup table
        self.surface_condition_data = {
            ('Turf', 'Firm'): {'speed': 0, 'power': 0, 'hp_coef': 1.0},
            ('Turf', 'Good'): {'speed': 0, 'power': -50, 'hp_coef': 1.0},
            ('Turf', 'Soft'): {'speed': 0, 'power': -50, 'hp_coef': 1.02},
            ('Turf', 'Heavy'): {'speed': -50, 'power': -50, 'hp_coef': 1.02},
            ('Dirt', 'Firm'): {'speed': 0, 'power': -100, 'hp_coef': 1.0},
            ('Dirt', 'Good'): {'speed': 0, 'power': -50, 'hp_coef': 1.0},
            ('Dirt', 'Soft'): {'speed': 0, 'power': -100, 'hp_coef': 1.01},
            ('Dirt', 'Heavy'): {'speed': -50, 'power': -100, 'hp_coef': 1.02}
        }
        
        # Aptitude lookup table
        self.aptitude_data = {
            'S': {'speed': 1.05, 'accel': 1.0},
            'A': {'speed': 1.0, 'accel': 1.0},
            'B': {'speed': 0.9, 'accel': 1.0},
            'C': {'speed': 0.8, 'accel': 1.0},
            'D': {'speed': 0.6, 'accel': 1.0},
            'E': {'speed': 0.4, 'accel': 0.6},
            'F': {'speed': 0.2, 'accel': 0.5},
            'G': {'speed': 0.1, 'accel': 0.4}
        }
    
    def get_distance_category(self):
        """Determine distance category based on race distance"""
        if self.distance <= 1400:
            return 'Sprint'
        elif self.distance <= 1800:
            return 'Mile'
        elif self.distance <= 2400:
            return 'Medium'
        else:
            return 'Long'
        
        # Mood lookup table
        self.mood_data = {
            'Great': 1.04,
            'Good': 1.02,
            'Normal': 1.0,
            'Bad': 0.98,
            'Awful': 0.96
        }
        
        # Style aptitude lookup table
        self.style_aptitude_data = {
            'S': 1.1,
            'A': 1.0,
            'B': 0.85,
            'C': 0.75,
            'D': 0.6,
            'E': 0.4,
            'F': 0.2,
            'G': 0.1
        }
        
        # Surface/condition lookup table
        self.surface_condition_data = {
            ('Turf', 'Firm'): {'speed': 0, 'power': 0, 'hp_coef': 1.0},
            ('Turf', 'Good'): {'speed': 0, 'power': -50, 'hp_coef': 1.0},
            ('Turf', 'Soft'): {'speed': 0, 'power': -50, 'hp_coef': 1.02},
            ('Turf', 'Heavy'): {'speed': -50, 'power': -50, 'hp_coef': 1.02},
            ('Dirt', 'Firm'): {'speed': 0, 'power': -100, 'hp_coef': 1.0},
            ('Dirt', 'Good'): {'speed': 0, 'power': -50, 'hp_coef': 1.0},
            ('Dirt', 'Soft'): {'speed': 0, 'power': -100, 'hp_coef': 1.01},
            ('Dirt', 'Heavy'): {'speed': -50, 'power': -100, 'hp_coef': 1.02}
        }
    
    def calculate_stamina_needed(self):
        """G57: Building up the calculation step by step"""
        
        print(f"=== Test Configuration ===")
        print(f"Stats: Speed={self.speed}, Stamina={self.stamina}, Power={self.power}, Guts={self.guts}, Wisdom={self.wisdom}")
        print(f"Race: {self.distance}m ({self.get_distance_category()}), Style={self.style}, Mood={self.mood}")
        print(f"Aptitudes: Track={self.track_aptitude}, Distance={self.distance_aptitude}, Style={self.style_aptitude}")
        print(f"Conditions: {self.surface}/{self.condition}, Recovery={self.recovery_percent}%")
        
        # F35: Actual stamina
        F35_actual_stamina = self.stamina
        
        # B34: Initial HP
        # Style lookup table
        style_data = {
            'Front': {'hp': 0.95, 'speed1': 1.0, 'speed2': 0.98, 'speed3': 0.962, 'accel1': 1.0, 'accel2': 1.0, 'accel3': 0.996},
            'Pace': {'hp': 0.89, 'speed1': 0.978, 'speed2': 0.991, 'speed3': 0.975, 'accel1': 0.985, 'accel2': 1.0, 'accel3': 0.996},
            'Late': {'hp': 1.0, 'speed1': 0.938, 'speed2': 0.998, 'speed3': 0.994, 'accel1': 0.975, 'accel2': 1.0, 'accel3': 1.0},
            'End': {'hp': 0.995, 'speed1': 0.931, 'speed2': 1.0, 'speed3': 1.0, 'accel1': 0.945, 'accel2': 1.0, 'accel3': 0.997}
        }
        
        style_hp_mult = style_data[self.style]['hp']
        speed1 = style_data[self.style]['speed1']
        speed2 = style_data[self.style]['speed2']
        speed3 = style_data[self.style]['speed3']
        accel_start = style_data[self.style]['accel1']
        accel_early = style_data[self.style]['accel2']
        accel_spurt = style_data[self.style]['accel3']
        
        B34_initial_hp = self.distance + 0.8 * F35_actual_stamina * style_hp_mult
        
        # B35: HP with skills
        recovery = self.recovery_percent  # Convert percentage to the same scale as K33+K34
        B35_hp_with_skills = B34_initial_hp * (1 + recovery / 100)
        
        # Base values
        B33_base_speed = 20 - (self.distance - 2000) / 1000
        
        # Surface/condition effects
        surface_data = self.surface_condition_data[(self.surface, self.condition)]
        B36_hp_coef = surface_data['hp_coef']
        surface_speed_bonus = surface_data['speed']
        surface_power_bonus = surface_data['power']
        
        # Apply mood multiplier and other adjustments to stats
        mood_mult = self.mood_data[self.mood]
        
        # F34: Speed with mood and surface skill bonuses
        F34_actual_speed = self.speed * mood_mult + surface_speed_bonus
        
        # F35: Stamina with mood
        F35_actual_stamina = self.stamina * mood_mult
        
        # F36: Power with mood and surface skill bonuses
        F36_actual_power = self.power * mood_mult + surface_power_bonus
        
        # F37: Guts with mood
        F37_actual_guts = self.guts * mood_mult
        
        # F38: Wisdom with mood and style aptitude multiplier
        # The style aptitude multiplier depends on the distance category
        distance_category = self.get_distance_category()
        style_wisdom_mult = self.style_aptitude_data[self.style_aptitude]
        F38_actual_wisdom = self.wisdom * mood_mult * style_wisdom_mult
        
        print(f"\n=== Stat Adjustments ({self.mood}) ===")
        print(f"Mood correction: {mood_mult}")
        print(f"Style aptitude {self.style_aptitude}: wisdom mult = {style_wisdom_mult}")
        print(f"Surface/condition ({self.surface}/{self.condition}): speed+{surface_speed_bonus}, power+{surface_power_bonus}, hp_coef={B36_hp_coef}")
        print(f"F34 (Speed): {self.speed} * {mood_mult} + {surface_speed_bonus} = {F34_actual_speed}")
        print(f"F35 (Stamina): {self.stamina} * {mood_mult} = {F35_actual_stamina}")
        print(f"F36 (Power): {self.power} * {mood_mult} + {surface_power_bonus} = {F36_actual_power}")
        print(f"F37 (Guts): {self.guts} * {mood_mult} = {F37_actual_guts}")
        print(f"F38 (Wisdom): {self.wisdom} * {mood_mult} * {style_wisdom_mult} = {F38_actual_wisdom}")
        print(f"Recovery: {self.recovery_percent}%")
        
        print(f"\n=== HP Calculation ===")
        print(f"B34 (initial HP): {B34_initial_hp:.2f}")
        print(f"B35 (HP with skills): {B35_hp_with_skills:.2f} (= {B34_initial_hp:.2f} * (1 + {recovery}/100))")
        
        B37_end_mult = 1 + (200 / math.sqrt(600 * F37_actual_guts))
        
        print(f"\n=== Style Lookup for {self.style} ===")
        print(f"HP mult: {style_hp_mult}, Speed: {speed1}/{speed2}/{speed3}, Accel: {accel_start}/{accel_early}/{accel_spurt}")
        
        # Wisdom factor
        F38_actual_wisdom = self.wisdom  # Now using class variable
        wisdom_factor = ((F38_actual_wisdom / 5500) * math.log10(F38_actual_wisdom * 0.1) - 0.65 / 2) * 0.01 * B33_base_speed
        
        # Speeds (calculating one at a time)
        start_begin = 3.0
        start_end = B33_base_speed * 0.85  # B42
        early_speed = B33_base_speed * speed1 + wisdom_factor  # B43
        
        # B45: Mid speed with mode multiplier
        # Base mid speed (B33 * speed2 + wisdom_factor)
        base_mid_speed = B33_base_speed * speed2 + wisdom_factor
        
        # L40: Mid-leg top speed before Modes (same as base_mid_speed)
        L40 = base_mid_speed
        
        # Mode multiplier for mid speed
        # L41 we calculated earlier, L42 = 0.05
        L41 = (self.distance / 24 / L40) / (self.distance / 24 / L40 + 3)
        L42 = 0.05
        if self.style != "Front":
            mode_speed_mult = 1 + L41 * (-0.055 * L42)
        else:
            mode_speed_mult = 1 + L41 * (0.04 * 0.2 * math.log10(F38_actual_wisdom * 0.1))
        
        mid_speed = base_mid_speed * mode_speed_mult  # B45
        
        # B55: Spurt speed calculation (now using the working formula)
        vlookup_col5 = speed3  # 0.975 for Pace
        F34_value = self.speed  # Speed stat
        distance_apt_lookup = self.aptitude_data[self.distance_aptitude]['speed']
        
        component1 = B33_base_speed * (vlookup_col5 + 0.01)
        component2 = math.sqrt(500 * F34_value) * distance_apt_lookup * 0.002
        spurt_speed = (component1 + component2) * 1.05 + component2  # B55
        
        print(f"\n=== Speed Calculations ===")
        print(f"B33 (base speed): {B33_base_speed:.3f}")
        print(f"Start begin: {start_begin:.3f}")
        print(f"Start end (B42): {start_end:.3f} (= {B33_base_speed:.3f} * 0.85)")
        print(f"Early speed (B43): {early_speed:.3f} (= {B33_base_speed:.3f} * {speed1} + {wisdom_factor:.3f})")
        print(f"Base mid speed: {base_mid_speed:.3f} (= {B33_base_speed:.3f} * {speed2} + {wisdom_factor:.3f})")
        print(f"L40 (mid speed before modes): {L40:.3f}")
        print(f"Mode speed mult: {mode_speed_mult:.6f} (L41={L41:.6f}, L42={L42})")
        print(f"Mid speed (B45): {mid_speed:.3f} (= {base_mid_speed:.3f} * {mode_speed_mult:.6f})")
        print(f"Component 1: {component1:.3f}, Component 2: {component2:.3f}")
        print(f"Spurt speed (B55): {spurt_speed:.3f} (= ({component1:.3f} + {component2:.3f}) * 1.05 + {component2:.3f})")
        
        # Acceleration modifiers - now using style lookup
        
        # Calculate accelerations
        F36_actual_power = self.power  # Now using class variable
        track_apt = self.aptitude_data[self.track_aptitude]['speed']
        dist_accel = self.aptitude_data[self.distance_aptitude]['accel']
        
        print(f"\n=== Aptitude Lookups ===")
        print(f"Track aptitude {self.track_aptitude}: speed={track_apt}")
        print(f"Distance aptitude {self.distance_aptitude}: accel={dist_accel}")
        
        base_accel = 0.0006 * math.sqrt(500 * F36_actual_power) * dist_accel * track_apt
        
        start_accel = 24.0 + base_accel * accel_start
        early_accel = base_accel * accel_start
        mid_accel = base_accel * accel_early
        spurt_accel = base_accel * accel_spurt  # D54 uses column 8 (Z = 0.996 for Pace)
        
        # G41: Start dash
        E41 = (start_end - start_begin) / start_accel
        G41 = 20 * B36_hp_coef * E41
        
        # G42: Early accel
        start_dist = (start_begin + start_end) / 2 * E41
        E42 = min(
            (early_speed - start_end) / early_accel,
            (-start_end + math.sqrt(start_end**2 + 2 * early_accel * (self.distance / 6 - start_dist))) / early_accel
        )
        G42 = 20 * B36_hp_coef * ((early_accel * E42 + start_end - B33_base_speed + 12)**3 - (start_end - B33_base_speed + 12)**3) / (3 * early_accel) / 144
        
        # G43: Early const
        early_accel_dist = (start_end + early_accel * E42 / 2) * E42
        early_const_dist = max(self.distance / 6 - (start_dist + early_accel_dist), 0)
        E43 = early_const_dist / early_speed
        G43 = 20 * B36_hp_coef * (early_speed - B33_base_speed + 12)**2 / 144 * E43
        
        # G44: Mid accel
        E44 = (mid_speed - early_speed) / mid_accel if mid_speed > early_speed else 0
        G44 = 20 * B36_hp_coef * ((mid_speed - B33_base_speed + 12)**3 - (early_speed - B33_base_speed + 12)**3) / (3 * mid_accel) / 144 if E44 > 0 else 0
        
        # G45: Mid const (with mode multiplier)
        mid_accel_dist = (early_speed + mid_speed) / 2 * E44
        mid_const_dist = self.distance / 2 - mid_accel_dist
        E45 = mid_const_dist / mid_speed
        G45_base = 20 * B36_hp_coef * (mid_speed - B33_base_speed + 12)**2 / 144 * E45
        
        # Mode multiplier for Pace (non-Front)
        mode_mult = 1 - 0.4 * L42 * L41
        G45 = G45_base * mode_mult
        
        # G54: Ideal spurt accel
        E54 = (spurt_speed - mid_speed) / spurt_accel
        G54 = 20 * B36_hp_coef * B37_end_mult * ((mid_speed + spurt_accel * E54 - B33_base_speed + 12)**3 - (mid_speed - B33_base_speed + 12)**3) / (3 * spurt_accel) / 144
        
        # G55: Ideal spurt const
        spurt_accel_dist = (mid_speed + spurt_speed) / 2 * E54
        spurt_const_dist = self.distance / 3 - spurt_accel_dist
        E55 = spurt_const_dist / spurt_speed
        G55 = 20 * B36_hp_coef * B37_end_mult * (spurt_speed - B33_base_speed + 12)**2 / 144 * E55
        
        # G56: Total HP
        G56_total_hp = G41 + G42 + G43 + G44 + G45 + G54 + G55
        
        print(f"\n=== Phase HP Calculations ===")
        print(f"G41 (start): {G41:.2f}")
        print(f"G42 (early accel): {G42:.2f}")
        print(f"G43 (early const): {G43:.2f}")
        print(f"G44 (mid accel): {G44:.2f}")
        print(f"G45 (mid const): {G45:.2f}")
        print(f"G54 (spurt accel): {G54:.2f}")
        print(f"G55 (spurt const): {G55:.2f}")
        print(f"G56 (total): {G56_total_hp:.2f}")
        
        # Final calculation
        stamina_needed = F35_actual_stamina + (G56_total_hp - B35_hp_with_skills) / 0.8 / style_hp_mult / (1 + recovery / 100)
        
        print(f"\n=== Final Result ===")
        print(f"Stamina needed: {stamina_needed:.1f}")
        
        return max(stamina_needed, 0)


class CalculatorWindow(Adw.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.calculator = UmaMusumeCalculator()
        
        self.set_title("Uma Musume Calculator - Minimal Test")
        self.set_default_size(600, 400)
        
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        header = Adw.HeaderBar()
        main_box.append(header)
        
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        content.set_margin_top(40)
        content.set_margin_bottom(40)
        content.set_margin_start(40)
        content.set_margin_end(40)
        content.set_valign(Gtk.Align.CENTER)
        
        title = Gtk.Label(label="Testing Phase Calculations")
        title.add_css_class("title-1")
        content.append(title)
        
        info = Gtk.Label(label="Building up G56 one phase at a time")
        info.add_css_class("dim-label")
        content.append(info)
        
        # Calculate button
        button = Gtk.Button(label="Calculate Required Stamina")
        button.connect("clicked", self._on_calculate)
        button.add_css_class("suggested-action")
        button.add_css_class("pill")
        content.append(button)
        
        # Result label
        self.result_label = Gtk.Label(label="Click to calculate")
        self.result_label.add_css_class("title-2")
        content.append(self.result_label)
        
        main_box.append(content)
        self.set_content(main_box)
    
    def _on_calculate(self, button):
        required = self.calculator.calculate_stamina_needed()
        self.result_label.set_markup(f'<span foreground="blue"><b>Required: {required:.1f}</b></span>')


class UmaMusumeApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id='com.example.umamusume.minimal')
        self.connect('activate', self.on_activate)
    
    def on_activate(self, app):
        self.win = CalculatorWindow(application=app)
        self.win.present()


if __name__ == '__main__':
    import sys
    app = UmaMusumeApp()
    sys.exit(app.run(None))
