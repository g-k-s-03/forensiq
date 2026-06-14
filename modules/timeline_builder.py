import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List

_FMT = "%Y-%m-%d %H:%M:%S"
_UNKNOWN_TS = "0000-00-00 00:00:00"


# ── Timestamp helpers ─────────────────────────────────────────────────────────

def _parse_ts(ts_str: str) -> float:
    """Convert a timestamp string to a Unix float. Returns 0.0 if unparseable."""
    if not ts_str or ts_str in ("N/A", _UNKNOWN_TS):
        return 0.0
    try:
        return datetime.strptime(ts_str, _FMT).timestamp()
    except ValueError:
        pass
    # Numeric string — e.g. Firefox cookie expiry stored as Unix seconds
    try:
        val = float(ts_str)
        return val if val > 0 else 0.0
    except (ValueError, TypeError):
        return 0.0


def _ts_display(ts_float: float) -> str:
    """Unix float -> 'YYYY-MM-DD HH:MM:SS'. Returns _UNKNOWN_TS on failure."""
    if ts_float <= 0:
        return _UNKNOWN_TS
    try:
        return datetime.fromtimestamp(ts_float).strftime(_FMT)
    except (OSError, OverflowError, ValueError):
        return _UNKNOWN_TS


def _ev(
    timestamp: str,
    ts_sort: float,
    source: str,
    event_type: str,
    description: str,
    confidence: str,
    artifact: Dict,
) -> Dict:
    return {
        "timestamp": timestamp,
        "timestamp_sort": ts_sort,
        "source": source,
        "event_type": event_type,
        "description": description,
        "confidence": confidence,
        "artifact": artifact,
    }


# ── Main builder ──────────────────────────────────────────────────────────────

def build_timeline(
    metadata_results: List[Dict],
    browser_artifacts: Dict[str, List[Dict]],
    recovered_records: List[Dict],
    dns_cache: List[Dict],
    prefetch_evidence: List[Dict],
) -> List[Dict]:
    """Merge all artifact sources into a single chronological timeline."""
    events: List[Dict] = []

    # ── File System ───────────────────────────────────────────────────────────
    for r in metadata_results:
        name      = r.get("name", "")
        size      = r.get("size_human", "")
        anomalous = bool(r.get("anomalies"))
        confidence = "INFERRED" if anomalous else "CONFIRMED"
        anomaly_tag = " [TIMESTAMP ANOMALY]" if anomalous else ""

        created = r.get("created", "")
        ts_c    = _parse_ts(created)
        events.append(
            _ev(
                created or _UNKNOWN_TS,
                ts_c,
                "File System",
                "FILE_CREATED",
                f"File created: {name} ({size}){anomaly_tag}",
                confidence,
                r,
            )
        )

        modified = r.get("modified", "")
        if modified and modified != created:
            ts_m = _parse_ts(modified)
            events.append(
                _ev(
                    modified,
                    ts_m,
                    "File System",
                    "FILE_MODIFIED",
                    f"File modified: {name} ({size}){anomaly_tag}",
                    confidence,
                    r,
                )
            )

    # ── Browser History (live) ────────────────────────────────────────────────
    for r in browser_artifacts.get("history", []):
        ts_str = r.get("last_visit_time", "") or ""
        ts     = _parse_ts(ts_str)
        url    = (r.get("url") or "")[:80]
        visits = r.get("visit_count", 0)
        src    = r.get("source", "Browser")
        conf   = "RECOVERED" if r.get("recovered") else "CONFIRMED"
        events.append(
            _ev(
                ts_str or _UNKNOWN_TS,
                ts,
                src,
                "BROWSER_VISIT",
                f"Browser visit: {url} (visits: {visits})",
                conf,
                r,
            )
        )

    # ── Browser Downloads ─────────────────────────────────────────────────────
    for r in browser_artifacts.get("downloads", []):
        ts_str = r.get("start_time", "") or ""
        ts     = _parse_ts(ts_str)
        path   = (r.get("target_path") or r.get("url") or "")[:80]
        total  = r.get("total_bytes", 0) or 0
        src    = r.get("source", "Browser")
        events.append(
            _ev(
                ts_str or _UNKNOWN_TS,
                ts,
                src,
                "BROWSER_DOWNLOAD",
                f"Download: {path} ({total:,} bytes)",
                "CONFIRMED",
                r,
            )
        )

    # ── Browser Cookies ───────────────────────────────────────────────────────
    for r in browser_artifacts.get("cookies", []):
        expires_raw = r.get("expires_utc", "") or ""
        ts          = _parse_ts(expires_raw)
        ts_str      = _ts_display(ts) if ts > 0 else _UNKNOWN_TS
        host        = r.get("host_key", "")
        name        = r.get("name", "")
        src         = r.get("source", "Browser")
        events.append(
            _ev(
                ts_str,
                ts,
                src,
                "BROWSER_COOKIE",
                f"Cookie set: {host} -- {name}",
                "CONFIRMED",
                r,
            )
        )

    # ── Recovered Records (freelist / WAL) ────────────────────────────────────
    for r in recovered_records:
        url    = (r.get("url") or "")[:80]
        src    = r.get("source", "Freelist Recovery")
        ts_str = r.get("last_visit_time", "") or ""
        ts     = _parse_ts(ts_str)
        if ts <= 0:
            ts_str = _UNKNOWN_TS
        events.append(
            _ev(
                ts_str,
                ts,
                src,
                "BROWSER_VISIT",
                f"RECOVERED: Browser visit: {url}",
                "RECOVERED",
                r,
            )
        )

    # ── DNS Cache (snapshot — no individual timestamps) ───────────────────────
    now_str = datetime.now().strftime(_FMT)
    now_ts  = datetime.now().timestamp()
    for r in dns_cache:
        hostname = r.get("hostname", "")
        events.append(
            _ev(
                now_str,
                now_ts,
                "DNS Cache",
                "DNS_LOOKUP",
                f"DNS cache entry: {hostname}",
                "INFERRED",
                r,
            )
        )

    # ── Prefetch Evidence ─────────────────────────────────────────────────────
    for r in prefetch_evidence:
        ts_str  = r.get("last_executed", "") or ""
        ts      = _parse_ts(ts_str)
        browser = r.get("browser", "")
        fname   = r.get("filename", "")
        events.append(
            _ev(
                ts_str or _UNKNOWN_TS,
                ts,
                "Prefetch",
                "BROWSER_EXECUTED",
                f"Browser executed: {browser} ({fname})",
                "CONFIRMED",
                r,
            )
        )

    # ── Sort: chronological; unknowns (0.0) go to end ────────────────────────
    events.sort(key=lambda e: (e["timestamp_sort"] == 0.0, e["timestamp_sort"]))
    return events


def export_timeline_json(timeline: List[Dict], output_path: Path) -> None:
    """Write timeline to JSON, omitting the verbose 'artifact' field."""
    slim = [{k: v for k, v in ev.items() if k != "artifact"} for ev in timeline]
    output_path.write_text(json.dumps(slim, indent=2), encoding="utf-8")
