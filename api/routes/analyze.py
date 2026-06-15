import asyncio
import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from api.job_store import create_job, get_job, update_job
from api.schemas import AnalyzeRequest, AnalysisResult, JobStatus
from modules.browser_forensics import (
    extract_browser_artifacts,
    get_dns_cache,
    get_prefetch_evidence,
    recover_deleted_history,
)
from modules.hash_checker import compute_hashes, detect_tampering
from modules.metadata_extractor import extract_metadata
from modules.report_generator import generate_report
from modules.timeline_builder import build_timeline, export_timeline_json

router = APIRouter()

_OUTPUT_DIR = Path("output")


def _run_pipeline(job_id: str, request: AnalyzeRequest) -> None:
    try:
        evidence_path = Path(request.evidence_dir).resolve()
        _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        case_id = request.case_id
        analysis_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Step 1 — Metadata
        update_job(job_id, status="running", progress=5,
                   current_step="Extracting metadata...")
        metadata_results = extract_metadata(evidence_path)
        exif_files = [r for r in metadata_results if r.get("exif")]

        # Step 2 — Hashes & tamper detection
        update_job(job_id, progress=20, current_step="Computing hashes...")
        hash_results = compute_hashes(evidence_path)

        baseline_hashes = None
        if request.baseline_path:
            bp = Path(request.baseline_path)
            if bp.exists():
                baseline_hashes = json.loads(bp.read_text(encoding="utf-8"))

        flags = detect_tampering(metadata_results, baseline_hashes, hash_results)

        hash_file = _OUTPUT_DIR / f"{case_id}_hashes.json"
        hash_file.write_text(json.dumps(hash_results, indent=2), encoding="utf-8")

        # Step 3 — Browser forensics
        update_job(job_id, progress=40, current_step="Analyzing browser artifacts...")
        artifacts = {"history": [], "downloads": [], "cookies": []}
        recovered: list = []
        dns_entries: list = []
        pf_entries: list = []
        try:
            artifacts = extract_browser_artifacts(evidence_path)
            recovered = recover_deleted_history(evidence_path)
            dns_entries = get_dns_cache()
            pf_entries = get_prefetch_evidence()
        except Exception:
            pass

        all_history = artifacts["history"] + [
            r for r in recovered if r.get("type") == "history"
        ]
        all_downloads = artifacts["downloads"]
        all_cookies = artifacts["cookies"]

        # Step 4 — Timeline
        update_job(job_id, progress=60, current_step="Building timeline...")
        timeline: list = []
        try:
            timeline = build_timeline(
                metadata_results, artifacts, recovered, dns_entries, pf_entries
            )
            tl_file = _OUTPUT_DIR / f"{case_id}_timeline.json"
            export_timeline_json(timeline, tl_file)
        except Exception:
            pass

        # Step 5 — PDF report
        pdf_path: Optional[Path] = None
        if request.generate_pdf:
            update_job(job_id, progress=80, current_step="Generating PDF report...")
            try:
                report_data = {
                    "case_id": case_id,
                    "investigator": request.investigator,
                    "device_info": request.device_info,
                    "evidence_dir": str(evidence_path),
                    "analysis_time": analysis_time,
                    "metadata_results": metadata_results,
                    "hash_results": hash_results,
                    "tamper_flags": flags,
                    "browser_artifacts": artifacts,
                    "recovered_records": recovered,
                    "dns_cache": dns_entries,
                    "prefetch_evidence": pf_entries,
                    "timeline": timeline,
                }
                pdf_path = _OUTPUT_DIR / f"{case_id}_forensics_report.pdf"
                generate_report(report_data, str(pdf_path))
            except Exception:
                pdf_path = None

        # Step 6 — JSON export
        update_job(job_id, progress=95, current_step="Finalizing...")
        json_export_path: Optional[Path] = None
        if request.export_json:
            try:
                tl_conf = sum(1 for e in timeline if e["confidence"] == "CONFIRMED")
                tl_inf = sum(1 for e in timeline if e["confidence"] == "INFERRED")
                tl_recov = sum(1 for e in timeline if e["confidence"] == "RECOVERED")
                full_export = {
                    "case_id": case_id,
                    "investigator": request.investigator,
                    "analysis_time": analysis_time,
                    "device_info": request.device_info,
                    "evidence_dir": str(evidence_path),
                    "summary": {
                        "files_scanned": len(metadata_results),
                        "hidden_files": sum(
                            1 for r in metadata_results if r["name"].startswith(".")
                        ),
                        "files_with_exif": len(exif_files),
                        "timestamp_anomalies": sum(
                            1 for r in metadata_results if r.get("anomalies")
                        ),
                        "tamper_flags": len(flags),
                        "high_flags": sum(
                            1 for f in flags if f["severity"] == "HIGH"
                        ),
                        "medium_flags": sum(
                            1 for f in flags if f["severity"] == "MEDIUM"
                        ),
                        "low_flags": sum(
                            1 for f in flags if f["severity"] == "LOW"
                        ),
                        "browser_history_live": len(artifacts["history"]),
                        "browser_history_recovered": len(
                            [r for r in recovered if r.get("type") == "history"]
                        ),
                        "downloads": len(all_downloads),
                        "dns_cache_entries": len(dns_entries),
                        "timeline_events": len(timeline),
                        "confirmed_events": tl_conf,
                        "inferred_events": tl_inf,
                        "recovered_events": tl_recov,
                    },
                    "tamper_flags": flags,
                    "browser_history": all_history,
                    "downloads": all_downloads,
                    "timeline": [
                        {k: v for k, v in e.items() if k != "artifact"}
                        for e in timeline
                    ],
                }
                json_export_path = _OUTPUT_DIR / f"{case_id}_full_analysis.json"
                json_export_path.write_text(
                    json.dumps(full_export, indent=2), encoding="utf-8"
                )
            except Exception:
                json_export_path = None

        # Step 7 — Complete
        tl_file_path = _OUTPUT_DIR / f"{case_id}_timeline.json"
        result = {
            "job_id": job_id,
            "case_id": case_id,
            "analysis_time": analysis_time,
            "summary": {
                "files_scanned": len(metadata_results),
                "hidden_files": sum(
                    1 for r in metadata_results if r["name"].startswith(".")
                ),
                "files_with_exif": len(exif_files),
                "timestamp_anomalies": sum(
                    1 for r in metadata_results if r.get("anomalies")
                ),
                "tamper_flags": len(flags),
                "high_flags": sum(1 for f in flags if f["severity"] == "HIGH"),
                "medium_flags": sum(1 for f in flags if f["severity"] == "MEDIUM"),
                "low_flags": sum(1 for f in flags if f["severity"] == "LOW"),
                "browser_history_live": len(artifacts["history"]),
                "browser_history_recovered": len(
                    [r for r in recovered if r.get("type") == "history"]
                ),
                "downloads": len(all_downloads),
                "dns_cache_entries": len(dns_entries),
                "timeline_events": len(timeline),
                "confirmed_events": sum(
                    1 for e in timeline if e["confidence"] == "CONFIRMED"
                ),
                "inferred_events": sum(
                    1 for e in timeline if e["confidence"] == "INFERRED"
                ),
                "recovered_events": sum(
                    1 for e in timeline if e["confidence"] == "RECOVERED"
                ),
            },
            "tamper_flags": flags,
            "browser_history": all_history,
            "downloads": all_downloads,
            "cookies": all_cookies,
            "dns_cache": dns_entries,
            "timeline": [
                {k: v for k, v in e.items() if k != "artifact"} for e in timeline
            ],
            "output_files": {
                "hashes": str(hash_file),
                "timeline": str(tl_file_path) if tl_file_path.exists() else None,
                "pdf": str(pdf_path) if pdf_path and pdf_path.exists() else None,
                "json": (
                    str(json_export_path)
                    if json_export_path and json_export_path.exists()
                    else None
                ),
            },
        }
        update_job(
            job_id,
            status="complete",
            progress=100,
            current_step="Complete",
            result=result,
        )

    except Exception as exc:
        update_job(job_id, status="failed", error=str(exc))


@router.post("/analyze")
def start_analysis(request: AnalyzeRequest):
    evidence_path = Path(request.evidence_dir)
    if not evidence_path.exists():
        raise HTTPException(
            status_code=400,
            detail=f"Evidence directory '{request.evidence_dir}' does not exist.",
        )

    job_id = f"job_{request.case_id}_{uuid4().hex[:8]}"
    create_job(job_id)
    threading.Thread(target=_run_pipeline, args=(job_id, request), daemon=True).start()
    return {"job_id": job_id, "status": "pending"}


@router.get("/analyze/{job_id}", response_model=JobStatus)
def get_job_status(job_id: str):
    job = get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found.")
    return JobStatus(
        job_id=job_id,
        status=job["status"],
        progress=job["progress"],
        current_step=job["current_step"],
        error=job.get("error"),
    )


@router.get("/analyze/{job_id}/stream")
async def stream_job(job_id: str):
    if get_job(job_id) is None:
        raise HTTPException(status_code=404, detail="Job not found.")

    async def _generator():
        while True:
            job = get_job(job_id)
            if job is None:
                break
            data = json.dumps(
                {
                    "progress": job["progress"],
                    "step": job["current_step"],
                    "status": job["status"],
                }
            )
            yield f"data: {data}\n\n"
            if job["status"] in ("complete", "failed"):
                if job["status"] == "complete":
                    final = json.dumps(
                        {"progress": 100, "status": "complete", "job_id": job_id}
                    )
                    yield f"data: {final}\n\n"
                break
            await asyncio.sleep(0.5)

    return StreamingResponse(_generator(), media_type="text/event-stream")


@router.get("/analyze/{job_id}/results", response_model=AnalysisResult)
def get_results(job_id: str):
    job = get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found.")
    if job["status"] in ("pending", "running"):
        raise HTTPException(status_code=425, detail="Analysis still in progress.")
    if job["status"] == "failed":
        raise HTTPException(status_code=500, detail=job.get("error", "Pipeline failed."))
    return job["result"]
