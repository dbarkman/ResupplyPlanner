"""
In-memory autocomplete service for system names.
Loads all system names from a text file and provides fast prefix matching.
"""

import time
from pathlib import Path
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


class SystemAutocomplete:
    """
    Fast in-memory autocomplete service for system names.
    Loads all system names from a text file and provides O(log n) prefix matching.
    """
    
    def __init__(self, names_file: str = "data/system_names.txt"):
        """
        Initialize the autocomplete service.
        
        Args:
            names_file: Path to the text file containing system names (one per line)
        """
        self.names_file = Path(names_file)
        self.system_names: List[str] = []
        self.loaded = False
        self.load_time: Optional[float] = None
        
    def load_names(self) -> None:
        """
        Load all system names from the text file into memory.
        This should be called once at application startup.
        """
        if self.loaded:
            logger.info("System names already loaded")
            return
            
        start_time = time.time()
        logger.info(f"Loading system names from {self.names_file}...")
        
        if not self.names_file.exists():
            raise FileNotFoundError(f"System names file not found: {self.names_file}")
        
        # Load all names from file
        with open(self.names_file, 'r', encoding='utf-8') as f:
            self.system_names = [line.strip() for line in f if line.strip()]
        
        # Verify the list is sorted (should be from export script)
        if not self._is_sorted():
            logger.warning("System names not sorted, sorting now...")
            self.system_names.sort()
        
        self.load_time = time.time() - start_time
        self.loaded = True
        
        logger.info(f"Loaded {len(self.system_names):,} system names in {self.load_time:.3f} seconds")
        logger.info(f"Memory usage: ~{len(self.system_names) * 15 / 1024 / 1024:.1f} MB")
    
    def _is_sorted(self) -> bool:
        """Check if the system names list is sorted."""
        return all(self.system_names[i] <= self.system_names[i + 1] 
                  for i in range(len(self.system_names) - 1))
    
    def search(self, query: str, limit: int = 10) -> List[str]:
        """
        Search for system names that start with the given query (case-insensitive).
        
        Args:
            query: The search query (prefix to match)
            limit: Maximum number of results to return
            
        Returns:
            List of matching system names (up to limit)
        """
        if not self.loaded:
            raise RuntimeError("System names not loaded. Call load_names() first.")
        
        if not query:
            return []
        
        query_lower = query.lower()
        results = []
        
        # Binary search to find the first matching name
        left, right = 0, len(self.system_names)
        
        while left < right:
            mid = (left + right) // 2
            if self.system_names[mid].lower() < query_lower:
                left = mid + 1
            else:
                right = mid
        
        # Collect all matching names starting from the found position
        start_idx = left
        for i in range(start_idx, len(self.system_names)):
            name = self.system_names[i]
            if not name.lower().startswith(query_lower):
                break
            results.append(name)
            if len(results) >= limit:
                break
        
        return results
    
    def get_stats(self) -> dict:
        """
        Get statistics about the autocomplete service.
        
        Returns:
            Dictionary with stats
        """
        return {
            "loaded": self.loaded,
            "total_systems": len(self.system_names) if self.loaded else 0,
            "load_time_seconds": self.load_time,
            "estimated_memory_mb": len(self.system_names) * 15 / 1024 / 1024 if self.loaded else 0,
            "names_file": str(self.names_file),
            "file_exists": self.names_file.exists()
        }


# Global instance for the application
autocomplete_service = SystemAutocomplete() 