import hashlib
from pathlib import Path
from typing import Dict, List, Optional

_SKIP_DIRS = {"__pycache__", ".git", "venv", ".venv", "node_modules"}
_CHUNK_SIZE = 65536  # 64 KB


def compute_hashes(evidence_path: Path) -> Dict[str, str]:
    """SHA-256 hash every file under evidence_path. Returns {rel_path: hex_digest}."""
    hashes: Dict[str, str] = {}
    for file_path in sorted(evidence_path.rglob("*")):
        if not file_path.is_file():
            continue
        if any(part in _SKIP_DIRS for part in file_path.parts):
            continue
        rel = str(file_path.relative_to(evidence_path)).replace("\\", "/")
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            while True:
                chunk = f.read(_CHUNK_SIZE)
                if not chunk:
                    break
                sha256.update(chunk)
        hashes[rel] = sha256.hexdigest()
    return hashes


def detect_tampering(
    metadata_results: List[Dict],
    baseline_hashes: Optional[Dict[str, str]],
    current_hashes: Dict[str, str],
) -> List[Dict]:
    """Cross-reference hashes and metadata to produce a list of tamper flags."""
    flags = []

    if baseline_hashes is not None:
        for rel_path, cur_hash in current_hashes.items():
            if rel_path in baseline_hashes:
                if cur_hash != baseline_hashes[rel_path]:
                    flags.append({
                        "type": "HASH_MISMATCH",
                        "severity": "HIGH",
                        "file": rel_path,
                        "detail": (
                            f"baseline={baseline_hashes[rel_path][:16]}...  "
                            f"current={cur_hash[:16]}..."
                        ),
                    })
            else:
                flags.append({
                    "type": "NEW_FILE",
                    "severity": "MEDIUM",
                    "file": rel_path,
                    "detail": "File not present in baseline",
                })

        for rel_path in baseline_hashes:
            if rel_path not in current_hashes:
                flags.append({
                    "type": "DELETED_FILE",
                    "severity": "HIGH",
                    "file": rel_path,
                    "detail": "File was in baseline but is now missing",
                })

    for r in metadata_results:
        file_id = r.get("rel_path", r["name"])
        if r.get("anomalies"):
            flags.append({
                "type": "TIMESTAMP_ANOMALY",
                "severity": "MEDIUM",
                "file": file_id,
                "detail": "; ".join(r["anomalies"]),
            })
        if r["name"].startswith("."):
            flags.append({
                "type": "HIDDEN_FILE",
                "severity": "LOW",
                "file": file_id,
                "detail": "Dot-prefixed filename (concealed on Unix/Linux)",
            })

    return flags
