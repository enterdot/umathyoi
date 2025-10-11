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

from .skill import Skill
from common import auto_title_from_instance, stopwatch


class SkillDatabase:
    """Database for managing skills loaded from Gametora website with image caching."""

    SKILLS_JSON = "data/skills.json"
    SKILL_ICON_CACHE_NAME = "skill_icons"
    
    # Network constants for skill icons
    IMAGE_TIMEOUT_SECONDS = 10
    IMAGE_BASE_URL = "https://gametora.com/images/umamusume/skill_icons/utx_ico_skill_{icon_id}.png"
    MAX_CONCURRENT_CONNECTIONS = 10

    @stopwatch(show_args=False)
    def __init__(self, skills_file: str = SKILLS_JSON) -> None:
        """Initialize skill database."""
        self.skills: dict[int, Skill] = {}
        self.image_cache: dict[int, GdkPixbuf.Pixbuf] = {}
        
        # Thread-safe lock for cache access
        self._cache_lock = threading.Lock()
        
        # Shared requests session for connection pooling
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": "umathyoi/0.0"})
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=SkillDatabase.MAX_CONCURRENT_CONNECTIONS,
            pool_maxsize=SkillDatabase.MAX_CONCURRENT_CONNECTIONS,
            max_retries=3
        )
        self._session.mount("http://", adapter)
        self._session.mount("https://", adapter)
        
        # Setup disk cache directory
        cache_base = Path(user_cache_dir("umathyoi"))
        self._cache_dir = cache_base / SkillDatabase.SKILL_ICON_CACHE_NAME
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Skill icon cache directory: {self._cache_dir}")
        
        try:
            self._load_skills_from_file(skills_file)
        except Exception as e:
            logger.error(f"Could not load skills from {skills_file}: {e}")
            import sys
            sys.exit(1)

        logger.debug(f"{auto_title_from_instance(self)} initialized")

    def _load_skills_from_file(self, skills_file: str) -> None:
        """Load skills data from JSON file."""
        try:
            with open(skills_file, "r", encoding="utf-8") as f:
                file_data = json.load(f)
                logger.info(f"Loaded skill data from {f.name}")
        except FileNotFoundError:
            raise FileNotFoundError(f"Skills file {skills_file} not found.")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in skills file: {e}")
        
        skills_data = file_data["data"]
        metadata = file_data.get("metadata", {})
        
        logger.info(f"Loading data: {metadata.get('record_count', len(skills_data))} skills")
        if "scraped_at" in metadata:
            logger.info(f"Data scraped at: {metadata['scraped_at']}")
        
        self._load_skills(skills_data)
        logger.info(f"Loaded data for {self.count} skills")

    def _load_skills(self, skills_data: list) -> None:
        """Load skills from data array."""
        for skill_data in skills_data:
            try:
                skill_id = skill_data.get("id")
                if skill_id is None:
                    logger.warning(f"Skipping skill with no ID: {skill_data}")
                    continue
                
                # Create Skill object (using minimal data for now)
                self.skills[skill_id] = Skill(
                    id=skill_id,
                    name=skill_data.get("name", f"Skill {skill_id}"),
                    icon_id=skill_data.get("icon_id", 0)
                )
                logger.debug(f"Skill {skill_id} added to database")
            
            except (KeyError, ValueError) as e:
                logger.warning(f"Skipping invalid skill data: {e}")

    def get_skill_by_id(self, skill_id: int) -> Skill | None:
        """Get skill by ID."""
        return self.skills.get(skill_id)

    def search_skills(self, name_query: str) -> Iterator[Skill]:
        """Search skills by name."""
        name_lower = name_query.lower()
        for skill in self.skills.values():
            if name_lower in skill.name.lower():
                yield skill

    @property
    def count(self) -> int:
        """Number of skills in database."""
        return len(self.skills)

    def __iter__(self) -> Iterator[Skill]:
        """Iterate over all skills in database."""
        yield from self.skills.values()

    def load_skill_icon_async(self, skill_id: int, width: int, height: int, callback: callable) -> None:
        """Load and cache skill icon asynchronously."""
        def load_in_thread():
            """This runs in a background thread."""
            try:
                pixbuf = self._load_skill_icon_sync(skill_id, width, height)
                callback(pixbuf)
            except Exception as e:
                logger.error(f"Error loading icon for skill {skill_id}: {e}")
                callback(None)

        thread = threading.Thread(target=load_in_thread, daemon=True)
        thread.start()

    def _load_skill_icon_sync(self, skill_id: int, width: int, height: int) -> GdkPixbuf.Pixbuf | None:
        """Synchronous internal method to load skill icon."""
        # Check memory cache first
        with self._cache_lock:
            if skill_id in self.image_cache:
                cached_pixbuf = self.image_cache[skill_id]
                return cached_pixbuf.scale_simple(width, height, GdkPixbuf.InterpType.BILINEAR)

        # Check disk cache
        disk_pixbuf = self._load_from_disk_cache(skill_id)
        if disk_pixbuf:
            with self._cache_lock:
                self.image_cache[skill_id] = disk_pixbuf
            logger.debug(f"Loaded skill {skill_id} icon from disk cache")
            return disk_pixbuf.scale_simple(width, height, GdkPixbuf.InterpType.BILINEAR)

        # Download from internet as fallback
        downloaded_pixbuf = self._download_and_cache_icon(skill_id)
        if downloaded_pixbuf:
            with self._cache_lock:
                self.image_cache[skill_id] = downloaded_pixbuf
            return downloaded_pixbuf.scale_simple(width, height, GdkPixbuf.InterpType.BILINEAR)

        logger.error(f"Could not load icon data for skill {skill_id}")
        return None

    def _get_cache_file_path(self, skill_id: int) -> Path:
        """Get the disk cache file path for a skill icon."""
        return self._cache_dir / f"{skill_id}.png"

    def _load_from_disk_cache(self, skill_id: int) -> GdkPixbuf.Pixbuf | None:
        """Load skill icon from disk cache."""
        cache_file = self._get_cache_file_path(skill_id)

        if not cache_file.exists():
            return None

        try:
            image_data = cache_file.read_bytes()
            return self._create_pixbuf_from_data(image_data)
        except Exception as e:
            logger.warning(f"Failed to load cached icon for skill {skill_id}: {e}")
            cache_file.unlink(missing_ok=True)
            return None

    def _download_and_cache_icon(self, skill_id: int) -> GdkPixbuf.Pixbuf | None:
        """Download skill icon and save to disk cache."""
        skill = self.skills.get(skill_id)
        if not skill:
            logger.error(f"Skill {skill_id} not found in database")
            return None
        
        icon_id = skill.icon_id
        url = SkillDatabase.IMAGE_BASE_URL.format(icon_id=icon_id)
        logger.debug(f"Downloading icon for skill {skill_id} (icon_id={icon_id})")

        try:
            response = self._session.get(url, timeout=SkillDatabase.IMAGE_TIMEOUT_SECONDS)

            if response.status_code == 200:
                image_data = response.content
                logger.debug(f"Downloaded icon for skill {skill_id}: {len(image_data)} bytes")

                # Save to disk cache
                cache_file = self._get_cache_file_path(skill_id)
                try:
                    cache_file.write_bytes(image_data)
                    logger.debug(f"Cached icon for skill {skill_id} to {cache_file}")
                except Exception as e:
                    logger.warning(f"Failed to save icon cache for skill {skill_id}: {e}")

                return self._create_pixbuf_from_data(image_data)
            else:
                logger.warning(f"HTTP {response.status_code} when downloading icon for skill {skill_id}")

        except requests.RequestException as e:
            logger.warning(f"Network error downloading icon for skill {skill_id}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error downloading icon for skill {skill_id}: {e}")

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
                logger.info("Skill icon disk cache cleared")
                return True
        except Exception as e:
            logger.error(f"Error clearing skill icon cache: {e}")
            return False

    def get_cache_info(self) -> dict:
        """Get information about the disk cache."""
        try:
            cache_files = list(self._cache_dir.glob("*.png"))
            total_size = sum(f.stat().st_size for f in cache_files)

            return {
                "cache_dir": str(self._cache_dir),
                "cached_icons": len(cache_files),
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "total_skills": self.count
            }
        except Exception as e:
            logger.error(f"Error getting cache info: {e}")
            return {"error": str(e)}
