import os
import json
import logging
from pathlib import Path
from typing import Optional

class CacheManager:
    def __init__(self, cache_dir: str):
        self.cache_dir = Path(cache_dir)
        self.logger = logging.getLogger(__name__)
    
    def get_cached_result(self, analysis_mode: str, path: str, is_file: bool) -> Optional[dict]:
        cache_path = self._get_cache_path(analysis_mode, path, is_file)
        if cache_path.exists():
            self.logger.info(f"Cache hit for {cache_path}")
            with cache_path.open('r') as f:
                return json.load(f)
        self.logger.info(f"Cache miss for {cache_path}")
        return None
    
    def cache_result(self, analysis_mode: str, path: str, result: dict, is_file: bool):
        cache_path = self._get_cache_path(analysis_mode, path, is_file)
        print(str(cache_path)+"\n\n\n\n\n\n\n")
        # Ensure the directory exists
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with cache_path.open('w') as f:
                json.dump(result, f)
            self.logger.info(f"Cached result for {cache_path}")
        except Exception as e:
            self.logger.error(f"Failed to cache result for {cache_path}: {str(e)}")
    
    def _get_cache_path(self, analysis_mode: str, path: str, is_file: bool) -> Path:
        path = path.replace('/', '#').replace('\\', '##')
        path_str = f"{path}_file" if is_file else f"{path}_dir"
        return self.cache_dir / analysis_mode / f"{path_str}.json"