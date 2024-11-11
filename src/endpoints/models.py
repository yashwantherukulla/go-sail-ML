from pydantic import BaseModel
from typing import Dict, List, Optional, Union, Any

class AnalysisRequest(BaseModel):
    path: str
    force_recompute: bool = False

class AnalysisResponse(BaseModel):
    path: str
    analysis_type: str
    scores: Optional[Dict[str, Union[int, float]]] = None
    descriptions: Optional[List[str]] = None
    details: Optional[Dict[str, Any]] = None
    cached: bool = False