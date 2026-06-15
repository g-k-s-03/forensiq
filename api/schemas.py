from typing import Dict, List, Optional
from pydantic import BaseModel


class AnalyzeRequest(BaseModel):
    evidence_dir: str
    case_id: str
    investigator: str
    device_info: str = "Unknown Device"
    baseline_path: Optional[str] = None
    generate_pdf: bool = True
    export_json: bool = False


class BaselineRequest(BaseModel):
    evidence_dir: str
    output_path: str = "baseline_hashes.json"


class JobStatus(BaseModel):
    job_id: str
    status: str          # "pending", "running", "complete", "failed"
    progress: int        # 0-100
    current_step: str
    error: Optional[str] = None


class AnalysisResult(BaseModel):
    job_id: str
    case_id: str
    analysis_time: str
    summary: Dict
    tamper_flags: List[Dict]
    browser_history: List[Dict]
    downloads: List[Dict]
    cookies: List[Dict]
    dns_cache: List[Dict]
    timeline: List[Dict]
    output_files: Dict   # {"pdf": path|None, "json": path|None, "hashes": path, "timeline": path}
