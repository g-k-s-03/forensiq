import hashlib
import math
from pathlib import Path
from typing import Dict, List, Optional

_SKIP_DIRS = {"__pycache__", ".git", "venv", ".venv", "node_modules"}
_CHUNK_SIZE = 65536  # 64 KB

_MAGIC_SIGNATURES = [
    (b"\x4d\x5a",          "Windows PE Executable (EXE/DLL)"),  # MZ / PE
    (b"\x7fELF",           "Linux ELF Executable"),
    (b"\x89PNG",           "PNG Image"),
    (b"\xff\xd8\xff",      "JPEG Image"),
    (b"%PDF",              "PDF Document"),
    (b"PK\x03\x04",        "ZIP/Office Archive"),
    (b"\xd0\xcf\x11\xe0",  "MS Office OLE Document"),
    (b"{\x5c\x72\x74\x66", "RTF Document"),             # {\rtf
]

_EXT_TO_EXPECTED_MAGIC: Dict[str, str] = {
    ".jpg":  "JPEG Image",
    ".jpeg": "JPEG Image",
    ".png":  "PNG Image",
    ".pdf":  "PDF Document",
    ".doc":  "MS Office OLE Document",
    ".docx": "ZIP/Office Archive",
    ".xlsx": "ZIP/Office Archive",
    ".pptx": "ZIP/Office Archive",
    ".rtf":  "RTF Document",
}

_EXECUTABLE_EXTS = {".exe", ".dll"}
_PLAINTEXT_EXTS  = {".txt", ".doc", ".docx", ".log", ".csv", ".xml", ".json"}

TAMPER_RULES: Dict[str, str] = {
    "HASH_MISMATCH":         "Rule R-01: File hash differs from verified baseline",
    "NEW_FILE":              "Rule R-02: File absent from baseline snapshot",
    "DELETED_FILE":          "Rule R-03: File present in baseline but missing from evidence",
    "TIMESTAMP_ANOMALY":     "Rule R-04: File timestamps indicate possible backdating",
    "HIDDEN_FILE":           "Rule R-05: Dot-prefixed filename used for concealment",
    "HIGH_ENTROPY":          "Rule R-06: Shannon entropy exceeds threshold for plaintext file type",
    "DISGUISED_FILE":        "Rule R-07: File extension does not match internal magic bytes",
    "SUSPICIOUS_EXECUTABLE": "Rule R-08: Executable file found in non-executable evidence context",
    "EXIF_STRIPPED":         "Rule R-09: JPEG image lacks EXIF metadata — possible anti-forensic wiping",
    "ANTI_FORENSIC":         "Rule R-10: Content modified with timestamp preservation — anti-forensic indicator",
}


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


def analyze_entropy(file_path: Path) -> float:
    """Compute Shannon entropy of file contents on a 0.0 – 8.0 scale."""
    byte_counts = [0] * 256
    total = 0
    with open(file_path, "rb") as f:
        while True:
            chunk = f.read(_CHUNK_SIZE)
            if not chunk:
                break
            for byte in chunk:
                byte_counts[byte] += 1
            total += len(chunk)
    if total == 0:
        return 0.0
    entropy = 0.0
    for count in byte_counts:
        if count > 0:
            p = count / total
            entropy -= p * math.log2(p)
    return round(entropy, 4)


def check_magic_bytes(file_path: Path) -> Optional[str]:
    """Read the first 16 bytes and return a type label if a known signature matches."""
    try:
        with open(file_path, "rb") as f:
            header = f.read(16)
        for sig, label in _MAGIC_SIGNATURES:
            if header[: len(sig)] == sig:
                return label
        return None
    except (OSError, IOError):
        return None


def detect_extension_mismatch(file_path: Path) -> Optional[Dict]:
    """Compare declared file extension against magic bytes. Returns a flag dict or None."""
    ext = file_path.suffix.lower()

    if ext in _EXECUTABLE_EXTS:
        return {
            "type": "SUSPICIOUS_EXECUTABLE",
            "severity": "HIGH",
            "file": file_path.name,
            "detail": f"Executable file ({ext}) found in evidence collection",
            "rule": TAMPER_RULES["SUSPICIOUS_EXECUTABLE"],
        }

    if ext in _EXT_TO_EXPECTED_MAGIC:
        expected = _EXT_TO_EXPECTED_MAGIC[ext]
        actual = check_magic_bytes(file_path)
        if actual != expected:
            actual_desc = actual if actual else "unknown / unrecognized format"
            return {
                "type": "DISGUISED_FILE",
                "severity": "HIGH",
                "file": file_path.name,
                "detail": f"Extension claims {ext} but magic bytes indicate {actual_desc}",
                "rule": TAMPER_RULES["DISGUISED_FILE"],
            }

    return None


def detect_exif_strip(metadata_results: List[Dict]) -> List[Dict]:
    """Flag JPEG files that carry no EXIF metadata."""
    flags = []
    for r in metadata_results:
        if r["extension"] in {".jpg", ".jpeg"} and not r.get("exif"):
            flags.append({
                "type": "EXIF_STRIPPED",
                "severity": "MEDIUM",
                "file": r.get("rel_path", r["name"]),
                "detail": (
                    "JPEG file contains no EXIF metadata — "
                    "possible evidence of anti-forensic wiping"
                ),
                "rule": TAMPER_RULES["EXIF_STRIPPED"],
            })
    return flags


def detect_antiforensic(
    metadata_results: List[Dict],
    baseline_hashes: Optional[Dict[str, str]],
    current_hashes: Dict[str, str],
) -> List[Dict]:
    """Flag files whose content changed since baseline but whose timestamps appear untouched."""
    if baseline_hashes is None:
        return []

    mismatch_files = {
        rel
        for rel, cur_hash in current_hashes.items()
        if rel in baseline_hashes and cur_hash != baseline_hashes[rel]
    }

    meta_by_rel = {r.get("rel_path", r["name"]): r for r in metadata_results}
    flags = []
    for rel in sorted(mismatch_files):
        r = meta_by_rel.get(rel)
        if r is not None and not r.get("anomalies"):
            flags.append({
                "type": "ANTI_FORENSIC",
                "severity": "HIGH",
                "file": rel,
                "detail": (
                    "File content changed (hash mismatch) but timestamps appear "
                    "unmodified — consistent with anti-forensic timestamp preservation"
                ),
                "rule": TAMPER_RULES["ANTI_FORENSIC"],
            })
    return flags


def detect_tampering(
    metadata_results: List[Dict],
    baseline_hashes: Optional[Dict[str, str]],
    current_hashes: Dict[str, str],
) -> List[Dict]:
    """Run all tamper rules and return a sorted list of flag dicts."""
    flags: List[Dict] = []

    # ── R-01 / R-02 / R-03: Hash comparison against baseline ─────────────────
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
                        "rule": TAMPER_RULES["HASH_MISMATCH"],
                    })
            else:
                flags.append({
                    "type": "NEW_FILE",
                    "severity": "MEDIUM",
                    "file": rel_path,
                    "detail": "File not present in baseline",
                    "rule": TAMPER_RULES["NEW_FILE"],
                })

        for rel_path in baseline_hashes:
            if rel_path not in current_hashes:
                flags.append({
                    "type": "DELETED_FILE",
                    "severity": "HIGH",
                    "file": rel_path,
                    "detail": "File was in baseline but is now missing",
                    "rule": TAMPER_RULES["DELETED_FILE"],
                })

    # ── R-04 / R-05: Timestamp anomalies and hidden files ────────────────────
    for r in metadata_results:
        file_id = r.get("rel_path", r["name"])
        if r.get("anomalies"):
            flags.append({
                "type": "TIMESTAMP_ANOMALY",
                "severity": "MEDIUM",
                "file": file_id,
                "detail": "; ".join(r["anomalies"]),
                "rule": TAMPER_RULES["TIMESTAMP_ANOMALY"],
            })
        if r["name"].startswith("."):
            flags.append({
                "type": "HIDDEN_FILE",
                "severity": "LOW",
                "file": file_id,
                "detail": "Dot-prefixed filename (concealed on Unix/Linux)",
                "rule": TAMPER_RULES["HIDDEN_FILE"],
            })

    # ── R-06: Shannon entropy analysis on plaintext file types ───────────────
    for r in metadata_results:
        if r["extension"] in _PLAINTEXT_EXTS:
            entropy = analyze_entropy(Path(r["path"]))
            if entropy > 7.2:
                flags.append({
                    "type": "HIGH_ENTROPY",
                    "severity": "MEDIUM",
                    "file": r.get("rel_path", r["name"]),
                    "detail": (
                        f"Shannon entropy: {entropy:.2f} — high entropy in plaintext "
                        "file suggests encrypted/compressed payload"
                    ),
                    "rule": TAMPER_RULES["HIGH_ENTROPY"],
                })

    # ── R-07 / R-08: Extension vs magic bytes mismatch ───────────────────────
    for r in metadata_results:
        flag = detect_extension_mismatch(Path(r["path"]))
        if flag:
            flag["file"] = r.get("rel_path", r["name"])
            flags.append(flag)

    # ── R-09: EXIF strip detection ────────────────────────────────────────────
    flags.extend(detect_exif_strip(metadata_results))

    # ── R-10: Anti-forensic timestamp preservation ───────────────────────────
    flags.extend(detect_antiforensic(metadata_results, baseline_hashes, current_hashes))

    _order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    flags.sort(key=lambda f: _order.get(f["severity"], 99))
    return flags
