#code_eval.py
from fastapi import FastAPI, HTTPException
from typing import Dict
from src.eval.cache_manager import CacheManager
from src.eval.code_analyserv2 import CodeAnalyser
from src.endpoints.models import AnalysisRequest, AnalysisResponse
from src.eval.git_handler import GitHandler
import os

app = FastAPI()
cache_manager = CacheManager("analysis_cache")
git_handler = GitHandler("./clones_repos")

def get_analyser(analysis_type: str) -> CodeAnalyser:
    return CodeAnalyser(analysis_type, cache_manager)

@app.post("/file_description")
async def file_description(request: AnalysisRequest) -> AnalysisResponse:
    analyser = get_analyser("code_descriptor")
    repo = git_handler.clone_repository(request.url)
    result = await analyser.analyze_file(os.path.join("./cloned_repos", request.path), request.force_recompute)
    return AnalysisResponse(
        path=request.path,
        analysis_type="description",
        descriptions=result.get("descriptions"),
        cached=result.get("cached", False)
    )

@app.post("/file_sec_analysis")
async def file_sec_analysis(request: AnalysisRequest) -> AnalysisResponse:
    analyser = get_analyser("code_security")
    result = await analyser.analyze_file(request.path, request.force_recompute)
    return AnalysisResponse(
        path=request.path,
        analysis_type="security",
        scores=result.get("scores"),
        details=result.get("details"),
        cached=result.get("cached", False)
    )

@app.post("/file_cqual_analysis")
async def file_cqual_analysis(request: AnalysisRequest) -> AnalysisResponse:
    analyser = get_analyser("code_quality")
    result = await analyser.analyze_file(request.path, request.force_recompute)
    return AnalysisResponse(
        path=request.path,
        analysis_type="quality",
        scores=result.get("scores"),
        details=result.get("details"),
        cached=result.get("cached", False)
    )

@app.post("/folder_description")
async def folder_description(request: AnalysisRequest) -> AnalysisResponse:
    analyser = get_analyser("code_descriptor")
    result = await analyser.analyze_directory(request.path, request.force_recompute)
    return AnalysisResponse(
        path=request.path,
        analysis_type="description",
        descriptions=result.get("descriptions"),
        cached=result.get("cached", False)
    )

@app.post("/folder_sec_analysis")
async def folder_sec_analysis(request: AnalysisRequest) -> AnalysisResponse:
    analyser = get_analyser("code_security")
    result = await analyser.analyze_directory(request.path, request.force_recompute)
    return AnalysisResponse(
        path=request.path,
        analysis_type="security",
        scores=result.get("scores"),
        details=result.get("details"),
        cached=result.get("cached", False)
    )

@app.post("/folder_cqual_analysis")
async def folder_cqual_analysis(request: AnalysisRequest) -> AnalysisResponse:
    analyser = get_analyser("code_quality")
    result = await analyser.analyze_directory(request.path, request.force_recompute)
    return AnalysisResponse(
        path=request.path,
        analysis_type="quality",
        scores=result.get("scores"),
        details=result.get("details"),
        cached=result.get("cached", False)
    )

@app.post("/repo_description")
async def repo_description(request: AnalysisRequest) -> AnalysisResponse:
    analyser = get_analyser("code_descriptor")
    result = await analyser.analyze_repo(request.path, request.force_recompute)
    return AnalysisResponse(
        path=request.path,
        analysis_type="description",
        descriptions=result.get("descriptions"),
        cached=result.get("cached", False)
    )

@app.post("/repo_sec_analysis")
async def repo_sec_analysis(request: AnalysisRequest) -> AnalysisResponse:
    analyser = get_analyser("code_security")
    result = await analyser.analyze_repo(request.path, request.force_recompute)
    return AnalysisResponse(
        path=request.path,
        analysis_type="security",
        scores=result.get("scores"),
        details=result.get("details"),
        cached=result.get("cached", False)
    )

@app.post("/repo_cqual_analysis")
async def repo_cqual_analysis(request: AnalysisRequest) -> AnalysisResponse:
    analyser = get_analyser("code_quality")
    result = await analyser.analyze_repo(request.path, request.force_recompute)
    return AnalysisResponse(
        path=request.path,
        analysis_type="quality",
        scores=result.get("scores"),
        details=result.get("details"),
        cached=result.get("cached", False)
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)