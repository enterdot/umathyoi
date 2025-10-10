#!/usr/bin/env python

"""
This tool fetches data from Gametora's JSON APIs and stores it with minimal
transformation, preserving the original structure for maximum flexibility.
"""

from common import setup_logging, get_logger
from pathlib import Path

setup_logging("info")
logger = get_logger(Path(__file__).name)

import json
import asyncio
import aiohttp
import argparse

from pathlib import Path
from typing import Any
from dataclasses import dataclass
from datetime import datetime

from modules import CardDatabase, SkillDatabase, CharacterDatabase


@dataclass
class GametoraEndpoint:
    """Configuration for a Gametora data endpoint"""

    name: str
    url: str
    output_file: str
    description: str


MANIFEST_URL = "https://gametora.com/data/manifests/umamusume.json"


async def fetch_gametora_manifest() -> dict[str, str] | None:
    """Fetch Gametora manifest with current file hashes"""
    try:
        logger.debug(f"Fetching Gametora manifest from {MANIFEST_URL}")

        async with aiohttp.ClientSession() as session:
            async with session.get(MANIFEST_URL) as response:
                if response.status == 200:
                    manifest = await response.json()
                    logger.debug(
                        f"Fetched manifest with {len(manifest)} entries"
                    )
                    return manifest
                else:
                    logger.error(
                        f"HTTP {response.status} when fetching manifest"
                    )
                    return None

    except Exception as e:
        logger.error(f"Error fetching manifest: {e}")
        return None


def build_endpoints_from_manifest(
    manifest: dict[str, str],
) -> dict[str, GametoraEndpoint]:
    """Build endpoint configurations from manifest data"""

    endpoints = {}

    # Support cards endpoint
    if "support-cards" in manifest:
        cards_hash = manifest["support-cards"]
        endpoints["cards"] = GametoraEndpoint(
            name="support_cards",
            url=f"https://gametora.com/data/umamusume/support-cards.{cards_hash}.json",
            output_file=CardDatabase.CARDS_JSON,
            description="Support cards with stats, effects, and skills",
        )
        logger.debug(f"Cards endpoint: {endpoints['cards'].url}")

    # Skills endpoint
    if "skills" in manifest:
        skills_hash = manifest["skills"]
        endpoints["skills"] = GametoraEndpoint(
            name="skills",
            url=f"https://gametora.com/data/umamusume/skills.{skills_hash}.json",
            output_file=SkillDatabase.SKILLS_JSON,
            description="Skills that can be learned by characters and granted by cards",
        )
        logger.debug(f"Skills endpoint: {endpoints['skills'].url}")

    # Characters endpoint
    if "character-cards" in manifest:
        characters_hash = manifest["character-cards"]
        endpoints["characters"] = GametoraEndpoint(
            name="characters",
            url=f"https://gametora.com/data/umamusume/character-cards.{characters_hash}.json",
            output_file=CharacterDatabase.CHARACTERS_JSON,
            description="Characters with name, stats and aptitudes",
        )
        logger.debug(f"Characters endpoint: {endpoints['characters'].url}")

    return endpoints


class GametoraScraperBase:
    """Base class for Gametora data scrapers with minimal cleanup"""

    def __init__(self, endpoint: GametoraEndpoint):
        self.endpoint = endpoint
        self.session: aiohttp.ClientSession | None = None

    async def fetch_data(self) -> list[dict[str, Any]] | None:
        """Fetch raw data from Gametora endpoint"""
        try:
            logger.debug(
                f"Fetching {self.endpoint.description} from {self.endpoint.url}"
            )

            async with aiohttp.ClientSession() as session:
                async with session.get(self.endpoint.url) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.debug(
                            f"Fetched {len(data)} {self.endpoint.name} records"
                        )
                        return data
                    else:
                        logger.error(
                            f"HTTP {response.status} when fetching {self.endpoint.name}"
                        )
                        return None

        except aiohttp.ClientError as e:
            logger.error(f"Network error fetching {self.endpoint.name}: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error for {self.endpoint.name}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching {self.endpoint.name}: {e}")
            return None

    def _pre_process(self, data: list[dict[str, Any]]) -> None:
        # Override for JSON specific pre-processing
        pass

    @property
    def fields_to_remove(self) -> list[str]:
        # Override for JSON specific fields to remove
        return []

    @property
    def fields_to_rename(self) -> dict[str, str]:
        # Override for JSON specific fields to rename
        return {}

    def _post_process(self, data: list[dict[str, Any]]) -> None:
        # Override for JSON specific post-processing
        pass

    def clean_data(self, data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Cleanup of raw data"""
        self._pre_process(data)

        clean_data = []
        for record in data:
            clean_record = {}
            for key, value in record.items():
                # Convert JavaScript null to Python None
                clean_record[key] = None if value is None else value

            for field in self.fields_to_remove:
                clean_record.pop(field, None)

            for from_field, to_field in self.fields_to_rename.items():
                if from_field in clean_record:
                    clean_record[to_field] = clean_record.pop(from_field)
                else:
                    clean_record[to_field] = ""
            clean_data.append(clean_record)

        self._post_process(clean_data)

        return clean_data

    def save_data(self, cleaned_data: list[dict[str, Any]]) -> bool:
        """Save cleaned data to JSON file with metadata"""
        try:
            output_path = Path(self.endpoint.output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            # Preserve original structure with minimal metadata
            output = {
                "metadata": {
                    "source": "Gametora",
                    "scraped_at": datetime.now().isoformat(),
                    "endpoint": self.endpoint.url,
                    "record_count": len(cleaned_data),
                },
                "data": cleaned_data,
            }

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(output, f, indent=2, ensure_ascii=False)

            logger.info(
                f"Saved {len(cleaned_data)} records to {self.endpoint.output_file}"
            )
            return True

        except Exception as e:
            logger.error(f"Error saving {self.endpoint.name} data: {e}")
            return False

    async def run(self) -> bool:
        """Execute the complete scraping pipeline"""
        logger.debug(f"Starting {self.endpoint.name} scraper")

        # Fetch raw data
        raw_data = await self.fetch_data()
        if not raw_data:
            return False

        try:
            cleaned_data = self.clean_data(raw_data)
            logger.debug(
                f"Cleaned {len(raw_data)} -> {len(cleaned_data)} {self.endpoint.name} records"
            )
        except Exception as e:
            logger.error(
                f"{self.__class__.__name__} failed to clean {self.endpoint.name} data: {e}"
            )
            return False

        # Save to file
        return self.save_data(cleaned_data)


class CardsScraper(GametoraScraperBase):
    """Scraper for support cards - preserves raw effects arrays"""

    @property
    def fields_to_remove(self) -> list[str]:
        return [
            "release",
            "release_ko",
            "release_zh_tw",
            "obtained",
            "name_jp",
            "name_ko",
            "name_tw",
        ]

    @property
    def fields_to_rename(self) -> dict[str, str]:
        # Override for JSON specific fields to rename
        return {
            "release_en": "release",
            "release_en": "release",
            "release_en": "release",
            "support_id": "id",
            "char_id": "character_id",
            "char_name": "character_name",
        }


class SkillsScraper(GametoraScraperBase):
    """Scraper for skills - flattens gene_version"""

    @property
    def fields_to_remove(self) -> list[str]:
        return [
            "desc_ko",
            "desc_tw",
            "endesc",
            "enname",
            "jpdesc",
            "jpname",
            "name_ko",
            "name_tw",
            "loc",
            "evo_cond",
            "pre_evo",
            "sup_hint",
            "sup_e",
            "sce_e",
            "evo",
            "rarity",
        ]

    @property
    def fields_to_rename(self) -> dict[str, str]:
        # Override for JSON specific fields to rename
        return {
            "name_en": "name",
            "desc_en": "description",
            "char": "character_ids",
            "iconid": "icon_id",
        }

    def _pre_process(self, data: list[dict[str, Any]]) -> None:
        """
        Override to handle gene_version flattening.
        Extracts gene_version sub-skills and adds them as separate entries.
        """
        gene_skill_data = []
        for record in data:
            try:
                # Extract gene_version skills as separate entries
                if "gene_version" in record and record["gene_version"]:
                    gene_skill_record = record.pop("gene_version", None)
                    if gene_skill_record:
                        gene_skill_record["parent_skill"] = record.get("id")
                        gene_skill_data.append(gene_skill_record)
            except Exception as e:
                logger.warning(
                    f"Error cleaning record {record.get('id', 'unknown')}: {e}"
                )
                continue
        data.extend(gene_skill_data)


class CharactersScraper(GametoraScraperBase):
    """Scraper for characters - preserves structure with EN/Global cleanup"""

    @property
    def fields_to_remove(self) -> list[str]:
        return [
            "base_stats",
            "two_star_stats",
            "three_star_stats",
            "four_star_stats",
            "five_star_stats",
            "card_id",
            "release",
            "release_ko",
            "release_zh_tw",
            "obtained",
            "rarity",
            "name_jp",
            "name_ko",
            "name_tw",
            "skills_event",
            "talent_group",
            "title",
            "title_jp",
            "title_ko",
            "title_tw",
        ]

    @property
    def fields_to_rename(self) -> dict[str, str]:
        # Override for JSON specific fields to rename
        return {
            "name_en": "name",
            "release_en": "release",
            "skills_event_en": "skills_event",
            "title_en_gl": "title",
            "skills_awakening": "skills_potential",
            "skills_evo": "skills_evolution",
            "char_id": "id",
            "costume": "costume_id",
        }

    def _post_process(self, data: list[dict[str, Any]]) -> None:
        """Remove brackets from title field"""
        for record in data:
            if "title" in record and record["title"]:
                title = record["title"]
                # Remove leading [ and trailing ]
                if title.startswith("[") and title.endswith("]"):
                    record["title"] = title[1:-1]


class GametoraScrapeManager:
    """Main manager for running scrapers with raw data approach"""

    def __init__(self):
        # Endpoints will be set after fetching manifest
        self.scrapers = {}
        self.endpoints = None

    async def initialize(self) -> bool:
        """Fetch manifest and initialize scrapers"""
        # Fetch manifest
        manifest = await fetch_gametora_manifest()
        if not manifest:
            logger.error("Failed to fetch Gametora manifest")
            return False

        # Build endpoints from manifest
        self.endpoints = build_endpoints_from_manifest(manifest)

        # Initialize scrapers
        if "cards" in self.endpoints:
            self.scrapers["cards"] = CardsScraper(self.endpoints["cards"])
        if "skills" in self.endpoints:
            self.scrapers["skills"] = SkillsScraper(self.endpoints["skills"])
        if "characters" in self.endpoints:
            self.scrapers["characters"] = CharactersScraper(
                self.endpoints["characters"]
            )

        logger.debug(f"Initialized {len(self.scrapers)} scrapers")
        return True

    async def run_scrapers(
        self, selected_scrapers: list[str]
    ) -> dict[str, bool]:
        """Run selected scrapers and return results"""
        results = {}

        for scraper_name in selected_scrapers:
            if scraper_name not in self.scrapers:
                results[scraper_name] = False
                continue

            try:
                scraper = self.scrapers[scraper_name]
                success = await scraper.run()
                results[scraper_name] = success

                if success:
                    logger.info(
                        f"{scraper_name.title()} scraping completed successfully"
                    )
                else:
                    logger.error(f"{scraper_name.title()} scraping failed")

            except Exception as e:
                logger.error(
                    f"✗ {scraper_name} scraping failed with exception: {e}"
                )
                results[scraper_name] = False

        return results

    def log_summary(self, results: dict[str, bool]):
        """Print a summary of scraping results"""
        successful = [name for name, success in results.items() if success]
        failed = [name for name, success in results.items() if not success]
        if successful:
            logger.info(f"Successful scrapers: {', '.join(successful)} ({len(successful)}/{len(results)})")
        if failed:
            logger.error(f"Failed scrapers: {', '.join(failed)} ({len(failed)}/{len(results)})")

        if successful:
            for name in successful:
                logger.debug(f"Created: {self.endpoints[name].output_file}")


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Scrape Gametora data with minimal cleanup"
    )

    # Individual scraper options
    parser.add_argument(
        "--cards", action="store_true", help="Scrape support cards data"
    )
    parser.add_argument(
        "--skills", action="store_true", help="Scrape skills data"
    )
    parser.add_argument(
        "--characters", action="store_true", help="Scrape characters data"
    )

    # Convenience options
    parser.add_argument(
        "--all", action="store_true", help="Scrape all available data types"
    )

    # Utility options
    parser.add_argument(
        "--list-endpoints", action="store_true", help="List all known endpoints"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be scraped without doing it",
    )

    args = parser.parse_args()
    manager = GametoraScrapeManager()

    # List endpoints doesn't need manifest
    if not args.list_endpoints:
        if not await manager.initialize():
            logger.error("Failed to initialize scraper manager")
            return

    # Handle list endpoints
    if args.list_endpoints:
        # Fetch manifest just for listing
        manifest = await fetch_gametora_manifest()
        if manifest:
            endpoints = build_endpoints_from_manifest(manifest)
            print("Known Gametora endpoints:")
            for name, endpoint in endpoints.items():
                print(f"  ✓ {name}: {endpoint.url}")
                print(f"     → {endpoint.description}")
                print(f"     → Output: {endpoint.output_file}")
        return

    # Determine which scrapers to run
    selected_scrapers = []

    if args.all:
        selected_scrapers = ["cards", "skills", "characters"]
    else:
        if args.cards:
            selected_scrapers.append("cards")
        if args.skills:
            selected_scrapers.append("skills")
        if args.characters:
            selected_scrapers.append("characters")

    # Default to all if nothing specified
    if not selected_scrapers:
        selected_scrapers = ["cards", "skills", "characters"]

    # Handle dry run
    if args.dry_run:
        print("DRY RUN - Would scrape the following:")
        for name in selected_scrapers:
            if name == "cards" and "cards" in manager.endpoints:
                endpoint = manager.endpoints["cards"]
                print(f"  - {name}: {endpoint.url} → {endpoint.output_file}")
            elif name == "skills" and "skills" in manager.endpoints:
                endpoint = manager.endpoints["skills"]
                print(f"  - {name}: {endpoint.url} → {endpoint.output_file}")
            elif name == "characters" and "characters" in manager.endpoints:
                endpoint = manager.endpoints["characters"]
                print(f"  - {name}: {endpoint.url} → {endpoint.output_file}")
        return

    # Run the scrapers
    results = await manager.run_scrapers(selected_scrapers)
    manager.log_summary(results)

    # Exit with error code if any scrapers failed
    if not all(results.values()):
        exit(1)


if __name__ == "__main__":
    asyncio.run(main())
