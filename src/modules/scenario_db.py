import logging
logger = logging.getLogger(__name__)

import gi
gi.require_version('Gdk', '4.0')
from gi.repository import GdkPixbuf

import json
from typing import Iterator
from pathlib import Path
from datetime import date
from utils import GameplayConstants

from .scenario import Scenario, FacilityType

class ScenarioDatabase:
    """Database for managing scenario data."""
    
    def __init__(self, scenarios_file: str = ApplicationConstants.SCENARIOS_JSON) -> None:
        """Initialize scenario database."""
        self._scenarios: dict[int, Scenario] = {}

        try:
            self._load_scenarios_from_file(scenarios_file)
        except Exception as e:
            logger.error(f"Could not load scenarios from {cards_file}: {e}")
            import sys
            sys.exit(1)
        
        logger.debug(f"{auto_title_from_instance(self)} initialized")

    @property
    def count(self) -> int:
        return len(self._scenarios)

    def _load_scenarios_from_file(self, scenarios_file: str) -> None:
        """Load scenario data from JSON file."""

        try:
            with open(scenarios_file, 'r', encoding='utf-8') as f:
                file_data = json.load(f)
                logger.info(f"Loaded scenario data from {f.name}")
        except FileNotFoundError:
            raise FileNotFoundError(f"Scenarios file {scenarios_file} not found.")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in scenarios file: {e}")

        scenarios_data = file_data['data']
        metadata = file_data.get('metadata', {})

        logger.info(f"Loading data: {len(scenarios_data)} scenarios")
        if 'updated_at' in metadata:
                logger.info(f"Data updated at: {metadata['updated_at']}")

        self._load_scenarios(scenarios_data)

        logger.info(f"Loaded data for {self.count} cards")

    def _load_scenarios(self, scenarios_data: dict) -> None:
        """Load scenarios."""
        for scenario_data in scenarios_data:
            try:
                scenario_id=scenario_data["scenario_id"]
                scenario_name=scenario_data["name"]
                try:
                    release=date.fromisoformat(scenario_data["release"])
                except ValueError:
                    release=None
                facilities = _create_facilities_from_scenario_data(scenario_data)
                scenario = Scenario(scenario_name, scenario_id, release, facilities)
                self._scenarios[scenario_id] = scenario
                logger.debug(f"Scenario {scenario_id} added to database")
                
            except (KeyError, ValueError) as e:
                logger.warning(f"Skipping invalid data for scenario {scenario_data.get('scenario_id', 'unknown')}: {e}")

    def _create_facilities_from_scenario_data(scenario_data: dict) -> dict[FacilityType, Facility]:
        """Create facilities dictionary from scenario JSON data."""
        facilities = {}
        
        facilities_data = scenario_data.get("facilities", {})
        
        for facility_name, facility_levels_data in facilities_data.items():
            try:
                facility_type = _parse_facility_type(facility_name)
                facility = create_facility_from_data(facility_type, facility_levels_data)
                facilities[facility_type] = facility
                
            except (ValueError, KeyError) as e:
                logger.warning(f"Skipping invalid facility '{facility_name}': {e}")
                continue
        
        return facilities

    def _create_facility_from_data(facility_type: FacilityType, facility_data: dict) -> Facility:
        """Create a Facility instance from JSON data."""
        stat_gain = {}
        skill_points_gain = {}
        energy_gain = {}
        
        # Parse each level's data
        for level_str, level_data in facility_data.items():
            level = int(level_str)
            
            # Parse stat gains for this level
            level_stat_gains = {}
            for stat_name, value in level_data.items():
                if stat_name == 'skill_points':
                    skill_points_gain[level] = value
                elif stat_name == 'energy':
                    energy_gain[level] = value
                else:
                    # Convert stat name to FacilityType enum
                    facility_type = _parse_stat_type(stat_name)
                    if facility_type:
                        level_stat_gains[facility_type] = value
            
            stat_gain[level] = level_stat_gains
        
        # Create facility with min level as default
        return Facility(
            type=facility_type,
            level=GameplayConstants.MIN_FACILITY_LEVEL,
            stat_gain=stat_gain,
            skill_points_gain=skill_points_gain,
            energy_gain=energy_gain
        )

    def _parse_stat_type(stat_name: str) -> FacilityType | None:
        """Parse stat name string to FacilityType enum."""
        stat_mapping = {
            'speed': FacilityType.speed,
            'stamina': FacilityType.stamina,
            'power': FacilityType.power,
            'guts': FacilityType.guts,
            'wit': FacilityType.wit,
        }
        return stat_mapping.get(stat_name.lower())

    def _parse_facility_type(facility_name: str) -> FacilityType:
        """Parse facility name to FacilityType enum."""
        facility_mapping = {
            'speed': FacilityType.speed,
            'stamina': FacilityType.stamina, 
            'power': FacilityType.power,
            'guts': FacilityType.guts,
            'wit': FacilityType.wit,
        }
        
        facility_type = facility_mapping.get(facility_name.lower())
        if not facility_type:
            raise ValueError(f"Unknown facility type: {facility_name}")
        
        return facility_type


    def get_scenario_by_name(self, name: str) -> Scenario:
        pass

    def __iter__(self) -> Iterator[Scenario]:
        """Iterate over all scenarios in database."""
        yield from self._scenarios.values()
