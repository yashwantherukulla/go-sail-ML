import os
import json
import time
import logging
from collections import defaultdict
from groq import Groq
import instructor
from dotenv import load_dotenv
from pathlib import Path
from typing import Dict, List, Optional, Union

from ..models.code_descriptor_model import CodeDescriptorModel, sys_prompt as code_descriptor_sys_prompt
from ..models.code_quality_eval_model import CodeQualityModel, sys_prompt as code_quality_sys_prompt
from ..models.code_sec_eval_model import CodeSecurityModel, sys_prompt as code_sec_sys_prompt
from ..eval.cache_manager import CacheManager
from ..eval.chunker import ChunkExtractor

GROQ_MODEL = "llama-3.1-70b-versatile"#"gemma2-9b-it"

class CodeAnalyser:
    def __init__(self, analysis_mode: str, cache_manager: CacheManager):
        self.logger = logging.getLogger(__name__)
        self.cache_manager = cache_manager
        self.analysis_mode = analysis_mode
        self._setup_analysis_mode(analysis_mode)
        
    def _setup_analysis_mode(self, analysis_mode: str):
        if analysis_mode == "code_descriptor":
            self.sys_prompt = code_descriptor_sys_prompt
            self.response_model = CodeDescriptorModel
        elif analysis_mode == "code_quality":
            self.sys_prompt = code_quality_sys_prompt
            self.response_model = CodeQualityModel
        elif analysis_mode == "code_security":
            self.sys_prompt = code_sec_sys_prompt
            self.response_model = CodeSecurityModel
        else:
            raise ValueError("Invalid analysis mode")
    
    def analyze_file(self, file_path: str, force_recompute: bool = False) -> Dict:
        """Analyze a single file"""
        if not force_recompute:
            cached_result = self.cache_manager.get_cached_result(
                self.analysis_mode, file_path, is_file=True
            )
            if cached_result:
                return {**cached_result, "cached": True}
        
        chunks = self._get_file_chunks(file_path)
        results = []
        for chunk in chunks:
            code = chunk["text"]
            result = self._analyze_chunk(code)
            results.append(result)
        
        aggregated_result = self._aggregate_results(results)
        self.cache_manager.cache_result(
            self.analysis_mode, file_path, aggregated_result, is_file=True
        )
        return {**aggregated_result, "cached": False}
    
    def analyze_directory(self, dir_path: str, force_recompute: bool = False) -> Dict:
        """Analyze a directory"""
        if not force_recompute:
            cached_result = self.cache_manager.get_cached_result(
                self.analysis_mode, dir_path, is_file=False
            )
            if cached_result:
                return {**cached_result, "cached": True}
        
        results = []
        for file_path in Path(dir_path).rglob("*"):
            if file_path.is_file():
                result = self.analyze_file(str(file_path), force_recompute)
                results.append(result)
        
        aggregated_result = self._aggregate_results(results)
        self.cache_manager.cache_result(
            self.analysis_mode, dir_path, aggregated_result, is_file=False
        )
        return {**aggregated_result, "cached": False}
    
    def analyze_repo(self, repo_path: str, force_recompute: bool = False) -> Dict:
        """Analyze entire repository"""
        return self.analyze_directory(repo_path, force_recompute)
    
    def _get_file_chunks(self, file_path: str) -> List[str]:
        """Get chunks for a file using the existing chunker"""
        chunk_extractor = ChunkExtractor()
        chunks = []
        chunk_folder = Path("temp_chunks")
        chunk_folder.mkdir(exist_ok=True)
        chunk_extractor.processFile(Path(file_path), chunk_folder)
        
        for chunk_file in chunk_folder.glob("*.json"):
            with chunk_file.open() as f:
                chunks.append(json.load(f))
            chunk_file.unlink()
        
        chunk_folder.rmdir()
        return chunks
    
    def _analyze_chunk(self, code: str) -> Dict:
        """Analyze a single code chunk using Groq API"""
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        client = instructor.from_groq(client, mode=instructor.Mode.TOOLS)
        
        result = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": self.sys_prompt},
                {"role": "user", "content": code},
            ],
            response_model=self.response_model,
        )
        return result.model_dump()
    
    def _aggregate_results(self, results: List[Dict]) -> Dict:
        """Aggregate results from multiple chunks or files"""
        if not results:
            return {"scores": {}, "descriptions": [], "details": {}}
        
        if self.analysis_mode == "code_descriptor":
            return {
                "descriptions": [r["description"] for r in results if "description" in r]
            }
        
        # For security and quality analysis
        aggregated_scores = defaultdict(list)
        aggregated_details = defaultdict(list)
        
        for result in results:
            for category, data in result.items():
                if isinstance(data, dict) and "score" in data:
                    aggregated_scores[category].append(data["score"])
                    if "details" in data:
                        aggregated_details[category].extend(data["details"])
        
        return {
            "scores": {
                category: round(sum(scores) / len(scores), 2)
                for category, scores in aggregated_scores.items()
            },
            "details": dict(aggregated_details)
        }