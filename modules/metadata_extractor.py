import logging
from pathlib import Path
from typing import Any, Dict, List
import datetime

# exifread emits noisy warnings for non-EXIF files (e.g. disguised PDFs with .jpg extension)
logging.getLogger("exifread").setLevel(logging.CRITICAL + 1)


def _format_size(size_bytes: int) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def _format_ts(ts: float) -> str:
    return datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")


def _dms_to_decimal(values) -> float:
    """Convert EXIF DMS (degrees/minutes/seconds) rational values to decimal degrees."""
    try:
        d = float(values[0].num) / float(values[0].den)
        m = float(values[1].num) / float(values[1].den)
        s = float(values[2].num) / float(values[2].den)
        return d + m / 60.0 + s / 3600.0
    except Exception:
        return 0.0


def _extract_exif(file_path: Path) -> Dict[str, Any]:
    try:
        import exifread

        with open(file_path, "rb") as f:
            tags = exifread.process_file(f, details=False)

        if not tags:
            return {}

        exif: Dict[str, Any] = {}

        simple_map = {
            "Image Make": "camera_make",
            "Image Model": "camera_model",
            "EXIF DateTimeOriginal": "date_taken",
            "Image Artist": "author",
            "Image Software": "software",
        }
        for tag_name, key in simple_map.items():
            if tag_name in tags:
                exif[key] = str(tags[tag_name]).strip()

        if "GPS GPSLatitude" in tags and "GPS GPSLongitude" in tags:
            lat = _dms_to_decimal(tags["GPS GPSLatitude"].values)
            lon = _dms_to_decimal(tags["GPS GPSLongitude"].values)
            lat_ref = str(tags.get("GPS GPSLatitudeRef", "N")).strip()
            lon_ref = str(tags.get("GPS GPSLongitudeRef", "E")).strip()
            if lat_ref == "S":
                lat = -lat
            if lon_ref == "W":
                lon = -lon
            exif["gps_coordinates"] = f"{lat:.6f}, {lon:.6f}"

        return exif
    except Exception:
        return {}


def extract_metadata(evidence_path: Path) -> List[Dict]:
    """Recursively extract metadata from all files in evidence_path."""
    results = []

    for file_path in sorted(evidence_path.rglob("*")):
        if not file_path.is_file():
            continue

        stat = file_path.stat()
        ctime = stat.st_ctime  # creation time on Windows, inode change time on Unix
        mtime = stat.st_mtime
        atime = stat.st_atime

        anomalies: List[str] = []
        if mtime < ctime:
            anomalies.append("mtime < ctime (possible backdating)")
        if atime < mtime:
            anomalies.append("atime < mtime (access before modification)")

        entry: Dict[str, Any] = {
            "name": file_path.name,
            "rel_path": str(file_path.relative_to(evidence_path)).replace("\\", "/"),
            "path": str(file_path.resolve()),
            "extension": file_path.suffix.lower(),
            "size_bytes": stat.st_size,
            "size_human": _format_size(stat.st_size),
            "created": _format_ts(ctime),
            "modified": _format_ts(mtime),
            "accessed": _format_ts(atime),
            "anomalies": anomalies,
            "exif": {},
        }

        if file_path.suffix.lower() in {".jpg", ".jpeg", ".tiff", ".tif", ".png"}:
            entry["exif"] = _extract_exif(file_path)

        results.append(entry)

    return results
