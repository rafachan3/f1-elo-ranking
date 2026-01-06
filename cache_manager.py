"""
Cache manager for expensive data processing operations.
This module provides a singleton pattern for the F1DataProcessor to avoid
reloading and reprocessing data on every request.
"""
import os
import threading
from functools import lru_cache


class DataProcessorCache:
    """Thread-safe singleton cache for F1DataProcessor."""
    
    _instance = None
    _lock = threading.Lock()
    _processor = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def get_processor(self):
        """Get or create the cached F1DataProcessor instance."""
        if not self._initialized:
            with self._lock:
                if not self._initialized:
                    from data_processor import F1DataProcessor
                    self._processor = F1DataProcessor()
                    self._processor.load_data()
                    self._processor.process_races()
                    self._initialized = True
        return self._processor
    
    def reset(self):
        """Reset the cache (useful for testing or manual refresh)."""
        with self._lock:
            self._processor = None
            self._initialized = False
    
    @property
    def is_initialized(self):
        """Check if processor is already initialized."""
        return self._initialized


# Global cache instance
_cache = DataProcessorCache()


def get_cached_processor():
    """Get the cached F1DataProcessor instance."""
    return _cache.get_processor()


def reset_cache():
    """Reset the processor cache."""
    _cache.reset()


def is_cache_initialized():
    """Check if the cache is initialized."""
    return _cache.is_initialized


@lru_cache(maxsize=1)
def get_race_count():
    """Get cached count of races (called frequently on home page)."""
    processor = get_cached_processor()
    return len(processor.races)

