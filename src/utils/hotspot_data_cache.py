import pandas as pd
from sqlalchemy import text
from db.db import get_async_db
from sqlalchemy.ext.asyncio import AsyncSession
import logging
from datetime import datetime, timedelta
import asyncio
from typing import Optional
import os
import json

logger = logging.getLogger(__name__)

class HotspotDataCache:
    _instance = None
    _cache_file = "static/hotspot_data_cache.json"
    _last_update_file = "static/hotspot_data_last_update.txt"
    _cache_duration = timedelta(hours=24)
    _df: Optional[pd.DataFrame] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(HotspotDataCache, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.initialized = True
            self._load_cache()

    def _load_cache(self):
        """Load data from cache file if it exists and is not expired"""
        try:
            if os.path.exists(self._last_update_file):
                with open(self._last_update_file, 'r') as f:
                    last_update = datetime.fromisoformat(f.read().strip())
                
                if datetime.now() - last_update < self._cache_duration:
                    if os.path.exists(self._cache_file):
                        with open(self._cache_file, 'r') as f:
                            data = json.load(f)
                            self._df = pd.DataFrame(data)
                            logger.info("Loaded hotspot data from cache")
                            return
        except Exception as e:
            logger.error(f"Error loading cache: {str(e)}")

        # If cache doesn't exist or is expired, fetch from database
        asyncio.create_task(self.refresh_cache())

    async def refresh_cache(self):
        """Fetch data from database and update cache"""
        try:
            async for session in get_async_db():
                # Fetch data from database
                result = await session.execute(text("SELECT * FROM public.hotspot_data"))
                rows = result.fetchall()
                
                # Convert to DataFrame
                self._df = pd.DataFrame(rows)
                
                # Save to cache file
                os.makedirs(os.path.dirname(self._cache_file), exist_ok=True)
                with open(self._cache_file, 'w') as f:
                    json.dump(self._df.to_dict(orient='records'), f)
                
                # Update last update timestamp
                with open(self._last_update_file, 'w') as f:
                    f.write(datetime.now().isoformat())
                
                logger.info("Hotspot data cache refreshed successfully")
                break
        except Exception as e:
            logger.error(f"Error refreshing cache: {str(e)}")
            raise e

    def get_data(self) -> pd.DataFrame:
        """Get the cached DataFrame, refreshing if necessary"""
        if self._df is None:
            # If DataFrame is not loaded, trigger a refresh
            asyncio.create_task(self.refresh_cache())
            # Wait for the refresh to complete
            while self._df is None:
                asyncio.sleep(0.1)
        return self._df

# Create a singleton instance
hotspot_cache = HotspotDataCache() 