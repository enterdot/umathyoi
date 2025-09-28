import logging
logger = logging.getLogger(__name__)

import gi
gi.require_version('Gdk', '4.0')
from gi.repository import GdkPixbuf

import json
from typing import Iterator
from pathlib import Path
from datetime import date

from .scenario import Scenario

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

                try:
                    release=date.fromisoformat(scenario_data["release"])
                except ValueError:
                    release=None

                facilities = {} # TODO: Claude please implement the code that fills this in

                scenario = Scenario(scenario_data["name"], scenario_id, release, facilities)

                self._scenarios[scenario_id] = scenario
                logger.debug(f"Scenario {scenario_id} added to database")
                
            except (KeyError, ValueError) as e:
                logger.warning(f"Skipping invalid data for scenario {scenario_data.get('scenario_id', 'unknown')}: {e}")

    def get_scenario_by_name(self, name: str) -> Scenario:
        pass

    def __iter__(self) -> Iterator[Scenario]:
        """Iterate over all scenarios in database."""
        yield from self._scenarios.values()
