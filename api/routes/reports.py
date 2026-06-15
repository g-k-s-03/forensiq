from pathlib import Path
from typing import Dict, List

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

router = APIRouter()

_OUTPUT_DIR = Path("output")

_SUFFIXES = [
    "_hashes.json",
    "_timeline.json",
    "_forensics_report.pdf",
    "_full_analysis.json",
]


@router.get("/reports/list")
def list_reports():
    if not _OUTPUT_DIR.exists():
        return {"cases": []}

    case_files: Dict[str, List[str]] = {}
    for f in _OUTPUT_DIR.iterdir():
        if not f.is_file():
            continue
        for suf in _SUFFIXES:
            if f.name.endswith(suf):
                case_id = f.name[: -len(suf)]
                case_files.setdefault(case_id, []).append(f.name)
                break

    return {
        "cases": [
            {"case_id": cid, "files": sorted(files)}
            for cid, files in sorted(case_files.items())
        ]
    }


@router.get("/reports/{case_id}/pdf")
def get_pdf(case_id: str):
    path = _OUTPUT_DIR / f"{case_id}_forensics_report.pdf"
    if not path.exists():
        raise HTTPException(status_code=404, detail="PDF report not found.")
    return FileResponse(
        path=str(path),
        media_type="application/pdf",
        filename=f"{case_id}_forensics_report.pdf",
    )


@router.get("/reports/{case_id}/json")
def get_json(case_id: str):
    path = _OUTPUT_DIR / f"{case_id}_full_analysis.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="JSON export not found.")
    return FileResponse(
        path=str(path),
        media_type="application/json",
        filename=f"{case_id}_full_analysis.json",
    )


@router.get("/reports/{case_id}/timeline")
def get_timeline(case_id: str):
    path = _OUTPUT_DIR / f"{case_id}_timeline.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Timeline file not found.")
    return FileResponse(
        path=str(path),
        media_type="application/json",
        filename=f"{case_id}_timeline.json",
    )


@router.get("/reports/{case_id}/hashes")
def get_hashes(case_id: str):
    path = _OUTPUT_DIR / f"{case_id}_hashes.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Hash manifest not found.")
    return FileResponse(
        path=str(path),
        media_type="application/json",
        filename=f"{case_id}_hashes.json",
    )
