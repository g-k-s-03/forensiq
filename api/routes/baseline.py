import json
from pathlib import Path

from fastapi import APIRouter, HTTPException

from api.schemas import BaselineRequest
from modules.hash_checker import compute_hashes

router = APIRouter()


@router.post("/baseline")
def save_baseline(request: BaselineRequest):
    evidence_path = Path(request.evidence_dir)
    if not evidence_path.exists():
        raise HTTPException(
            status_code=400,
            detail=f"Evidence directory '{request.evidence_dir}' does not exist.",
        )

    hashes = compute_hashes(evidence_path)

    out_path = Path(request.output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(hashes, indent=2), encoding="utf-8")

    return {
        "status": "saved",
        "file_count": len(hashes),
        "output_path": str(out_path.resolve()),
    }
