#!/usr/bin/env python

"""
Gametora Data Scraper - Raw Data Approach

This tool fetches data from Gametora's JSON APIs and stores it with minimal 
transformation, preserving the original structure for maximum flexibility.

The philosophy is to keep scraped data as close to the original as possible,
then use "view classes" in the app to provide clean, typed interfaces to the data.

Usage:
    python tools/scrape_gametora.py --cards --skills
    python tools/scrape_gametora.py --cards-only
    python tools/scrape_gametora.py --all
"""

import logging
from utils import setup_logging, get_logger
setup_logging("DEBUG")
logger = get_logger(__name__)

import json
import asyncio
import aiohttp
import argparse

from pathlib import Path
from typing import Any
from dataclasses import dataclass
from datetime import datetime

from utils import ApplicationConstants

@dataclass
class GametoraEndpoint:
    """Configuration for a Gametora data endpoint"""
    name: str
    url: str
    output_file: str
    description: str

GAMETORA_ENDPOINTS = {
    'cards': GametoraEndpoint(
        name='support_cards',
        url='https://gametora.com/data/umamusume/support-cards.9da37405.json',
        output_file=ApplicationConstants.CARDS_JSON,
        description='Support cards with stats, effects, and skills'
    ),
    'skills': GametoraEndpoint(
        name='skills',
        url='https://gametora.com/data/umamusume/skills.742ab78e.json',
        output_file=ApplicationConstants.SKILLS_JSON,
        description='Skills that can be learned by characters and granted by cards'
    ),
    # Characters will be handled separately due to individual endpoint pattern
}

class GametoraScraperBase:
    """Base class for Gametora data scrapers with minimal cleanup"""
    
    def __init__(self, endpoint: GametoraEndpoint):
        self.endpoint = endpoint
        self.session: aiohttp.ClientSession | None = None
    
    async def fetch_data(self) -> list[dict[str, Any]] | None:
        """Fetch raw data from Gametora endpoint"""
        try:
            logger.info(f"Fetching {self.endpoint.description} from {self.endpoint.url}")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(self.endpoint.url) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"Successfully fetched {len(data)} {self.endpoint.name} records")
                        return data
                    else:
                        logger.error(f"HTTP {response.status} when fetching {self.endpoint.name}")
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
    
    def clean_data(self, raw_data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Minimal cleanup of raw data - override in subclasses for specific needs.
        
        This should only do essential cleanup like:
        - Null handling
        - Removing clearly invalid records
        - Basic data validation
        
        NOT semantic transformation of the data structure.
        """
        cleaned_data = []
        
        for record in raw_data:
            try:
                # Basic validation - ensure record has required fields
                if self._is_valid_record(record):
                    # Minimal cleanup
                    cleaned_record = self._clean_record(record)
                    cleaned_data.append(cleaned_record)
                else:
                    logger.debug(f"Skipping invalid record: {record.get('id', 'unknown')}")
            except Exception as e:
                logger.warning(f"Error cleaning record {record.get('id', 'unknown')}: {e}")
                continue
        
        return cleaned_data
    
    def _is_valid_record(self, record: dict[str, Any]) -> bool:
        """Check if record has minimum required fields - override in subclasses"""
        return True  # Base implementation accepts all records
    
    def _clean_record(self, record: dict[str, Any]) -> dict[str, Any]:
        """Minimal cleanup of individual record - override in subclasses"""
        # Base implementation: just ensure consistent null handling
        cleaned = {}
        for key, value in record.items():
            # Convert JavaScript null to Python None, keep everything else as-is
            cleaned[key] = None if value is None else value
        return cleaned
    
    def save_data(self, cleaned_data: list[dict[str, Any]]) -> bool:
        """Save cleaned data to JSON file with metadata"""
        try:
            output_path = Path(self.endpoint.output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Preserve original structure with minimal metadata
            output = {
                'metadata': {
                    'source': 'Gametora',
                    'scraped_at': datetime.now().isoformat(),
                    'endpoint': self.endpoint.url,
                    'record_count': len(cleaned_data)
                },
                'data': cleaned_data
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(output, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved {len(cleaned_data)} records to {self.endpoint.output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving {self.endpoint.name} data: {e}")
            return False
    
    async def run(self) -> bool:
        """Execute the complete scraping pipeline"""
        logger.info(f"Starting {self.endpoint.name} scraper (raw data approach)")
        
        # Fetch raw data
        raw_data = await self.fetch_data()
        if not raw_data:
            return False
        
        # Minimal cleanup
        try:
            cleaned_data = self.clean_data(raw_data)
            logger.info(f"Cleaned {len(raw_data)} -> {len(cleaned_data)} {self.endpoint.name} records")
        except Exception as e:
            logger.error(f"Error cleaning {self.endpoint.name} data: {e}")
            return False
        
        # Save to file
        return self.save_data(cleaned_data)


class CardsScraper(GametoraScraperBase):
    """Scraper for support cards - preserves raw effects arrays with EN/Global cleanup"""
    
    # Fields to remove from card records
    FIELDS_TO_REMOVE = {
        'release', 'release_ko', 'release_zh_tw', 'obtained',
        'name_jp', 'name_ko', 'name_tw'
    }
    
    def _is_valid_record(self, record: dict[str, Any]) -> bool:
        """Validate card record has essential fields"""
        required_fields = ['support_id', 'char_name', 'rarity', 'type']
        return all(field in record for field in required_fields)
    
    def _clean_record(self, record: dict[str, Any]) -> dict[str, Any]:
        """Clean card record for EN/Global version"""
        cleaned = super()._clean_record(record)
        
        # Remove unwanted fields
        for field in self.FIELDS_TO_REMOVE:
            cleaned.pop(field, None)
        
        # Rename release_en to release
        if 'release_en' in cleaned:
            cleaned['release'] = cleaned.pop('release_en')
        else:
            # Add empty release if no release_en exists
            cleaned['release'] = ""
        
        # Ensure effects is a list (not null)
        if 'effects' not in cleaned or cleaned['effects'] is None:
            cleaned['effects'] = []
        
        # Ensure hints structure exists
        if 'hints' not in cleaned or cleaned['hints'] is None:
            cleaned['hints'] = {'hint_others': [], 'hint_skills': []}
        
        # Ensure event_skills is a list
        if 'event_skills' not in cleaned or cleaned['event_skills'] is None:
            cleaned['event_skills'] = []
        
        return cleaned


class SkillsScraper(GametoraScraperBase):
    """Scraper for skills - preserves structure with EN/Global cleanup and flattens gene_version"""
    
    # Fields to remove from skill records
    FIELDS_TO_REMOVE = {
        'desc_ko', 'desc_tw', 'endesc', 'enname', 'jpdesc', 'jpname',
        'name_ko', 'name_tw', 'loc'
    }
    
    def _is_valid_record(self, record: dict[str, Any]) -> bool:
        """Validate skill record has essential fields"""
        return 'id' in record or 'skill_id' in record
    
    def clean_data(self, raw_data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Override clean_data to handle gene_version flattening.
        
        This extracts gene_version sub-skills and adds them as separate entries
        at the same hierarchical level as their parent skills.
        """
        cleaned_data = []
        
        for record in raw_data:
            try:
                if self._is_valid_record(record):
                    # Clean the main skill
                    cleaned_record = self._clean_record(record)
                    cleaned_data.append(cleaned_record)
                    
                    # Extract and clean gene_version skills as separate entries
                    if 'gene_version' in record and record['gene_version']:
                        gene_skill = self._clean_gene_version_skill(record['gene_version'], record.get('id'))
                        if gene_skill:
                            cleaned_data.append(gene_skill)
                            
                else:
                    logger.debug(f"Skipping invalid record: {record.get('id', 'unknown')}")
            except Exception as e:
                logger.warning(f"Error cleaning record {record.get('id', 'unknown')}: {e}")
                continue
        
        return cleaned_data
    
    def _clean_record(self, record: dict[str, Any]) -> dict[str, Any]:
        """Clean skill record for EN/Global version"""
        cleaned = super()._clean_record(record)
        
        # Remove unwanted fields
        for field in self.FIELDS_TO_REMOVE:
            cleaned.pop(field, None)
        
        # Rename name_en to name
        if 'name_en' in cleaned:
            cleaned['name'] = cleaned.pop('name_en')
        
        # Rename desc_en to description
        if 'desc_en' in cleaned:
            cleaned['description'] = cleaned.pop('desc_en')
        
        # Remove gene_version since we're flattening it
        cleaned.pop('gene_version', None)
        
        return cleaned
    
    def _clean_gene_version_skill(self, gene_skill: dict[str, Any], parent_id: Any) -> dict[str, Any] | None:
        """
        Clean gene_version skill and prepare it as a separate entry.
        
        Args:
            gene_skill: The gene_version skill data
            parent_id: ID of the parent skill
            
        Returns:
            Cleaned gene skill with parent_skills field, or None if invalid
        """
        
        # TODO: Review this method
        
        if not isinstance(gene_skill, dict):
            return None
        
        try:
            cleaned = dict(gene_skill)  # Copy to avoid modifying original
            
            # Remove unwanted fields
            for field in self.FIELDS_TO_REMOVE:
                cleaned.pop(field, None)
            
            # Rename name_en to name
            if 'name_en' in cleaned:
                cleaned['name'] = cleaned.pop('name_en')
            
            # Rename desc_en to description
            if 'desc_en' in cleaned:
                cleaned['description'] = cleaned.pop('desc_en')
            
            # Add parent_skills field to identify this as a gene skill
            if parent_id is not None:
                cleaned['parent_skills'] = [parent_id]
            
            # Remove nested gene_version if it exists (shouldn't normally)
            cleaned.pop('gene_version', None)
            
            return cleaned
            
        except Exception as e:
            logger.warning(f"Error cleaning gene_version skill: {e}")
            return None


class CharactersScraper:
    """
    Special scraper for characters that handles individual character endpoints
    with EN/Global cleanup.
    """
    
    # Fields to remove from itemData
    ITEM_DATA_FIELDS_TO_REMOVE = {
        'name_jp', 'name_ko', 'name_tw', 'title', 'title_jp', 'title_ko', 'title_tw',
        'release', 'release_ko', 'release_zh_tw', 'obtained', 'skills_event'
    }
    
    def __init__(self, character_ids: list[str], base_url_template: str):
        """
        Initialize characters scraper.
        
        Args:
            character_ids: list of character ID strings (e.g., ["101102-grass-wonder"])
            base_url_template: URL template with {character_id} placeholder
        """
        self.character_ids = character_ids
        self.base_url_template = base_url_template
        self.output_file = ApplicationConstants.CHARACTERS_JSON
    
    async def fetch_character(self, character_id: str) -> dict[str, Any] | None:
        """Fetch data for a single character"""
        url = self.base_url_template.format(character_id=character_id)
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.debug(f"Fetched character {character_id}")
                        return data
                    else:
                        logger.warning(f"HTTP {response.status} for character {character_id}")
                        return None
        except Exception as e:
            logger.warning(f"Error fetching character {character_id}: {e}")
            return None
    
    def _clean_character_record(self, record: dict[str, Any]) -> dict[str, Any] | None:
        """Clean character record for EN/Global version"""
        try:
            # Extract only itemData, discard everything else
            if 'pageProps' not in record or 'itemData' not in record['pageProps']:
                logger.debug("Character record missing pageProps.itemData")
                return None
            
            item_data = record['pageProps']['itemData']
            if not isinstance(item_data, dict):
                logger.debug("itemData is not a dictionary")
                return None
            
            cleaned = dict(item_data)  # Copy to avoid modifying original
            
            # Remove unwanted fields
            for field in self.ITEM_DATA_FIELDS_TO_REMOVE:
                cleaned.pop(field, None)
            
            # Rename name_en to name
            if 'name_en' in cleaned:
                cleaned['name'] = cleaned.pop('name_en')
            
            # Rename title_en_gl to title
            if 'title_en_gl' in cleaned:
                cleaned['title'] = cleaned.pop('title_en_gl')
            
            # Rename release_en to release, or add empty release
            if 'release_en' in cleaned:
                cleaned['release'] = cleaned.pop('release_en')
            else:
                cleaned['release'] = ""
            
            # Rename skills_event_en to skills_event
            if 'skills_event_en' in cleaned:
                cleaned['skills_event'] = cleaned.pop('skills_event_en')
            
            return cleaned
            
        except Exception as e:
            logger.warning(f"Error cleaning character record: {e}")
            return None
    
    async def fetch_all_characters(self) -> list[dict[str, Any]]:
        """Fetch all characters concurrently"""
        logger.info(f"Fetching {len(self.character_ids)} individual character files")
        
        # Fetch all characters concurrently
        tasks = [self.fetch_character(char_id) for char_id in self.character_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out failed fetches and clean the data
        characters = []
        for char_id, result in zip(self.character_ids, results):
            if isinstance(result, dict):
                cleaned = self._clean_character_record(result)
                if cleaned:
                    characters.append(cleaned)
                else:
                    logger.warning(f"Failed to clean character data for {char_id}")
            else:
                logger.warning(f"Failed to fetch character {char_id}")
        
        logger.info(f"Successfully processed {len(characters)}/{len(self.character_ids)} characters")
        return characters
    
    def save_characters(self, characters: list[dict[str, Any]]) -> bool:
        """Save character data to JSON file"""
        try:
            output_path = Path(self.output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            output = {
                'metadata': {
                    'source': 'Gametora',
                    'scraped_at': datetime.now().isoformat(),
                    'endpoint_pattern': self.base_url_template,
                    'record_count': len(characters),
                    'data_format': 'raw_gametora',
                    'character_ids_requested': self.character_ids,
                    'success_rate': f"{len(characters)}/{len(self.character_ids)}"
                },
                'data': characters
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(output, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved {len(characters)} character records to {self.output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving character data: {e}")
            return False
    
    async def run(self) -> bool:
        """Execute character scraping"""
        if not self.character_ids:
            logger.warning("No character IDs provided, skipping character scraping")
            return False
        
        characters = await self.fetch_all_characters()
        if not characters:
            return False
        
        return self.save_characters(characters)


class GametoraScrapeManager:
    """Main manager for running scrapers with raw data approach"""
    
    def __init__(self):
        self.scrapers = {
            'cards': CardsScraper(GAMETORA_ENDPOINTS['cards']),
            'skills': SkillsScraper(GAMETORA_ENDPOINTS['skills']),
        }
        
        self.character_scraper = None
    
    def set_character_ids(self, character_ids: list[str], url_template: str):
        """Set up character scraper with provided IDs"""
        self.character_scraper = CharactersScraper(character_ids, url_template)
        self.scrapers['characters'] = self.character_scraper
    
    async def run_scrapers(self, selected_scrapers: list[str]) -> dict[str, bool]:
        """Run selected scrapers and return results"""
        results = {}
        
        for scraper_name in selected_scrapers:
            if scraper_name not in self.scrapers:
                if scraper_name == 'characters':
                    logger.error("Characters scraper not configured. Use --characters-file or --characters-ids")
                else:
                    logger.error(f"Unknown scraper: {scraper_name}")
                results[scraper_name] = False
                continue
            
            try:
                scraper = self.scrapers[scraper_name]
                success = await scraper.run()
                results[scraper_name] = success
                
                if success:
                    logger.info(f"✓ {scraper_name} scraping completed successfully")
                else:
                    logger.error(f"✗ {scraper_name} scraping failed")
                    
            except Exception as e:
                logger.error(f"✗ {scraper_name} scraping failed with exception: {e}")
                results[scraper_name] = False
        
        return results
    
    def print_summary(self, results: dict[str, bool]):
        """Print a summary of scraping results"""
        print("\n" + "="*60)
        print("SCRAPING SUMMARY (Raw Data Approach)")
        print("="*60)
        
        successful = [name for name, success in results.items() if success]
        failed = [name for name, success in results.items() if not success]
        
        if successful:
            print(f"✓ Successful: {', '.join(successful)}")
        
        if failed:
            print(f"✗ Failed: {', '.join(failed)}")
        
        print(f"\nTotal: {len(successful)}/{len(results)} scrapers succeeded")
        
        if successful:
            print("\nOutput files generated:")
            for name in successful:
                if name in GAMETORA_ENDPOINTS:
                    endpoint = GAMETORA_ENDPOINTS[name]
                    print(f"  - {endpoint.output_file}")
                elif name == 'characters':
                    print(f"  - {ApplicationConstants.CHARACTERS_JSON}")
        
        print("\nNote: Data stored with minimal transformation.")
        print("Use view classes in the app to access typed, clean interfaces.")


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Scrape Gametora data with minimal cleanup'
    )
    
    # Individual scraper options
    parser.add_argument('--cards', action='store_true', help='Scrape support cards data')
    parser.add_argument('--skills', action='store_true', help='Scrape skills data')
    parser.add_argument('--characters', action='store_true', help='Scrape characters data (requires --characters-file or --characters-ids)')
    
    # Character-specific options
    parser.add_argument('--characters-file', help='File containing character IDs (one per line)')
    parser.add_argument('--characters-ids', help='Comma-separated character IDs (e.g. "30025-special-week,10007-vodka")')
    parser.add_argument('--characters-url-template', 
                       default='https://gametora.com/_next/data/pgqKwGpVRDewvjE3UX6O2/umamusume/characters/{character_id}.json?id={character_id}',
                       help='URL template for character endpoints')
    
    # Convenience options
    parser.add_argument('--cards-only', action='store_true', help='Scrape only cards (same as --cards)')
    parser.add_argument('--all', action='store_true', help='Scrape all available data types')
    
    # Utility options
    parser.add_argument('--list-endpoints', action='store_true', help='List all known endpoints')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be scraped without doing it')
    
    args = parser.parse_args()
    
    # Handle list endpoints
    if args.list_endpoints:
        print("Known Gametora endpoints:")
        for name, endpoint in GAMETORA_ENDPOINTS.items():
            print(f"  ✓ {name}: {endpoint.url}")
            print(f"     → {endpoint.description}")
            print(f"     → Output: {endpoint.output_file}")
        print("  ✓ characters: Individual endpoints (pattern-based)")
        print(f"     → Pattern: {args.characters_url_template}")
        print(f"     → Output: {ApplicationConstants.CHARACTERS_JSON}")
        return
    
    manager = GametoraScrapeManager()
    
    # Handle character IDs setup
    character_ids = []
    if args.characters_file:
        try:
            with open(args.characters_file, 'r') as f:
                character_ids = [line.strip() for line in f if line.strip()]
            logger.info(f"Loaded {len(character_ids)} character IDs from {args.characters_file}")
        except Exception as e:
            logger.error(f"Error reading character IDs file: {e}")
            return
    elif args.characters_ids:
        character_ids = [id.strip() for id in args.characters_ids.split(',') if id.strip()]
        logger.info(f"Using {len(character_ids)} character IDs from command line")
    
    if character_ids:
        manager.set_character_ids(character_ids, args.characters_url_template)
    
    # Determine which scrapers to run
    selected_scrapers = []
    
    if args.all:
        selected_scrapers = ['cards', 'skills']
        if character_ids:
            selected_scrapers.append('characters')
    else:
        if args.cards or args.cards_only:
            selected_scrapers.append('cards')
        if args.skills:
            selected_scrapers.append('skills')
        if args.characters:
            selected_scrapers.append('characters')
    
    # Default to cards if nothing specified
    if not selected_scrapers:
        selected_scrapers = ['cards']
        print("No scrapers specified, defaulting to --cards")
    
    # Handle dry run
    if args.dry_run:
        print("DRY RUN - Would scrape the following:")
        for name in selected_scrapers:
            if name in GAMETORA_ENDPOINTS:
                endpoint = GAMETORA_ENDPOINTS[name]
                print(f"  - {name}: {endpoint.url} → {endpoint.output_file}")
            elif name == 'characters':
                print(f"  - characters: {len(character_ids)} individual endpoints → {ApplicationConstants.CHARACTERS_JSON}")
        return
    
    # Run the scrapers
    results = await manager.run_scrapers(selected_scrapers)
    manager.print_summary(results)
    
    # Exit with error code if any scrapers failed
    if not all(results.values()):
        exit(1)


if __name__ == "__main__":
    asyncio.run(main())
