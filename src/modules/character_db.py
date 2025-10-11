import logging

logger = logging.getLogger(__name__)

import gi

gi.require_version("Gdk", "4.0")
from gi.repository import GdkPixbuf, GLib

import json
import requests
import threading
from typing import Iterator
from pathlib import Path
from platformdirs import user_cache_dir

from .character import Character, Aptitude
from common import auto_title_from_instance, stopwatch


class CharacterDatabase:
    """Database for managing characters loaded from Gametora website with image caching."""

    CHARACTERS_JSON = "data/characters.json"
    CHARACTER_PORTRAIT_CACHE_NAME = "character_portraits"
    
    # Network constants for character portraits
    IMAGE_TIMEOUT_SECONDS = 10
    # Character portraits use id and character_id fields: https://gametora.com/images/umamusume/characters/chara_stand_{character_id}_{id}.png
    IMAGE_BASE_URL = "https://gametora.com/images/umamusume/characters/chara_stand_{character_id}_{id}.png"
    MAX_CONCURRENT_CONNECTIONS = 10

    @stopwatch(show_args=False)
    def __init__(self, characters_file: str = CHARACTERS_JSON) -> None:
        """Initialize character database."""
        self.characters: dict[int, Character] = {}
        self.image_cache: dict[int, GdkPixbuf.Pixbuf] = {}
        
        # Thread-safe lock for cache access
        self._cache_lock = threading.Lock()
        
        # Shared requests session for connection pooling
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": "umathyoi/0.0"})
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=CharacterDatabase.MAX_CONCURRENT_CONNECTIONS,
            pool_maxsize=CharacterDatabase.MAX_CONCURRENT_CONNECTIONS,
            max_retries=3
        )
        self._session.mount("http://", adapter)
        self._session.mount("https://", adapter)
        
        # Setup disk cache directory
        cache_base = Path(user_cache_dir("umathyoi"))
        self._cache_dir = cache_base / CharacterDatabase.CHARACTER_PORTRAIT_CACHE_NAME
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Character portrait cache directory: {self._cache_dir}")
        
        try:
            self._load_characters_from_file(characters_file)
        except Exception as e:
            logger.error(f"Could not load characters from {characters_file}: {e}")
            import sys
            sys.exit(1)

        logger.debug(f"{auto_title_from_instance(self)} initialized")

    def _load_characters_from_file(self, characters_file: str) -> None:
        """Load characters data from JSON file."""
        try:
            with open(characters_file, "r", encoding="utf-8") as f:
                file_data = json.load(f)
                logger.info(f"Loaded character data from {f.name}")
        except FileNotFoundError:
            raise FileNotFoundError(f"Characters file {characters_file} not found.")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in characters file: {e}")
        
        characters_data = file_data["data"]
        metadata = file_data.get("metadata", {})
        
        logger.info(f"Loading data: {metadata.get('record_count', len(characters_data))} characters")
        if "scraped_at" in metadata:
            logger.info(f"Data scraped at: {metadata['scraped_at']}")
        
        self._load_characters(characters_data)
        logger.info(f"Loaded data for {self.count} characters")

    def _load_characters(self, characters_data: list) -> None:
        """Load characters from data array."""
        for char_data in characters_data:
            try:
                id = char_data.get("id")
   
                # Create Character object
                self.characters[id] = Character(
                    id=id,
                    character_id=char_data.get("character_id"),
                    name=char_data.get("url_name"),
                    view_name=char_data.get("name", f"Character {id}"),
                    stat_bonus=[20, 10, 0, 0, 0],
                    aptitudes=[Aptitude.A, Aptitude.A, Aptitude.A, Aptitude.A, Aptitude.A, Aptitude.A, Aptitude.A, Aptitude.A, Aptitude.A, Aptitude.A]
                )
                logger.debug(f"Character {id} ({self.characters[id].name}) added to database")
            
            except (KeyError, ValueError) as e:
                logger.warning(f"Skipping invalid character data: {e}")

    def get_character_by_id(self, id: int) -> Character | None:
        """Get character by ID."""
        return self.characters.get(id)

    def get_costumes_by_character_id(self, character_id: int) -> Iterator[Character]:
        """Get all character costumes for a given character ID."""
        for character in self.characters.values():
            if character.character_id == character_id:
                yield character

    def search_characters(self, name_query: str) -> Iterator[Character]:
        """Search characters by name."""
        name_lower = name_query.lower()
        for character in self.characters.values():
            if name_lower in character.name.lower():
                yield character

    @property
    def count(self) -> int:
        """Number of character costumes in database."""
        return len(self.characters)

    def __iter__(self) -> Iterator[Character]:
        """Iterate over all character cards in database."""
        yield from self.characters.values()

    def load_character_portrait_async(self, id: int, width: int, height: int, callback: callable) -> None:
        """Load and cache character portrait asynchronously."""
        def load_in_thread():
            """This runs in a background thread."""
            try:
                pixbuf = self._load_character_portrait_sync(id, width, height)
                callback(pixbuf)
            except Exception as e:
                logger.error(f"Error loading portrait for character costume {id}: {e}")
                callback(None)

        thread = threading.Thread(target=load_in_thread, daemon=True)
        thread.start()

    def _load_character_portrait_sync(self, id: int, width: int, height: int) -> GdkPixbuf.Pixbuf | None:
        """Synchronous internal method to load character portrait."""
        # Check memory cache first
        with self._cache_lock:
            if id in self.image_cache:
                cached_pixbuf = self.image_cache[id]
                return cached_pixbuf.scale_simple(width, height, GdkPixbuf.InterpType.BILINEAR)

        # Check disk cache
        disk_pixbuf = self._load_from_disk_cache(id)
        if disk_pixbuf:
            with self._cache_lock:
                self.image_cache[id] = disk_pixbuf
            logger.debug(f"Loaded character card {id} portrait from disk cache")
            return disk_pixbuf.scale_simple(width, height, GdkPixbuf.InterpType.BILINEAR)

        # Download from internet as fallback
        downloaded_pixbuf = self._download_and_cache_portrait(id)
        if downloaded_pixbuf:
            with self._cache_lock:
                self.image_cache[id] = downloaded_pixbuf
            return downloaded_pixbuf.scale_simple(width, height, GdkPixbuf.InterpType.BILINEAR)

        logger.error(f"Could not load portrait data for character costume {id}")
        return None

    def _get_cache_file_path(self, id: int) -> Path:
        """Get the disk cache file path for a character portrait."""
        return self._cache_dir / f"{id}.png"

    def _load_from_disk_cache(self, id: int) -> GdkPixbuf.Pixbuf | None:
        """Load character portrait from disk cache."""
        cache_file = self._get_cache_file_path(id)

        if not cache_file.exists():
            return None

        try:
            image_data = cache_file.read_bytes()
            return self._create_pixbuf_from_data(image_data)
        except Exception as e:
            logger.warning(f"Failed to load cached portrait for character costume {id}: {e}")
            cache_file.unlink(missing_ok=True)
            return None

    def _download_and_cache_portrait(self, id: int) -> GdkPixbuf.Pixbuf | None:
        """Download character portrait and save to disk cache."""
        character = self.characters.get(id)
        if not character:
            logger.error(f"Character costume {id} not found in database")
            return None
        
        url = CharacterDatabase.IMAGE_BASE_URL.format(id=id)
        logger.debug(f"Downloading portrait for character costume {character.id}")

        try:
            response = self._session.get(url, timeout=CharacterDatabase.IMAGE_TIMEOUT_SECONDS)

            if response.status_code == 200:
                image_data = response.content
                logger.debug(f"Downloaded portrait for character card {character.id}: {len(image_data)} bytes")

                # Save to disk cache
                cache_file = self._get_cache_file_path(character.id)
                try:
                    cache_file.write_bytes(image_data)
                    logger.debug(f"Cached portrait for character costume {character.id} to {cache_file}")
                except Exception as e:
                    logger.warning(f"Failed to save portrait cache for character costume {character.id}: {e}")

                return self._create_pixbuf_from_data(image_data)
            else:
                logger.warning(f"HTTP {response.status_code} when downloading portrait for character costume {character.id}")

        except requests.RequestException as e:
            logger.warning(f"Network error downloading portrait for character costume {character.id}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error downloading portrait for character costume {character.id}: {e}")

        return None

    def _create_pixbuf_from_data(self, image_data: bytes) -> GdkPixbuf.Pixbuf | None:
        """Create GdkPixbuf from image data bytes."""
        try:
            loader = GdkPixbuf.PixbufLoader()
            loader.write(image_data)
            loader.close()
            return loader.get_pixbuf()
        except Exception as e:
            logger.error(f"Could not create pixbuf from image data: {e}")
            return None

    def clear_cache(self) -> bool:
        """Clear the disk cache."""
        try:
            import shutil

            if self._cache_dir.exists():
                shutil.rmtree(self._cache_dir)
                self._cache_dir.mkdir(parents=True, exist_ok=True)
                with self._cache_lock:
                    self.image_cache.clear()
                logger.info("Character portrait disk cache cleared")
                return True
        except Exception as e:
            logger.error(f"Error clearing character portrait cache: {e}")
            return False

    def get_cache_info(self) -> dict:
        """Get information about the disk cache."""
        try:
            cache_files = list(self._cache_dir.glob("*.png"))
            total_size = sum(f.stat().st_size for f in cache_files)

            return {
                "cache_dir": str(self._cache_dir),
                "cached_portraits": len(cache_files),
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "total_characters": self.count
            }
        except Exception as e:
            logger.error(f"Error getting cache info: {e}")
            return {"error": str(e)}
