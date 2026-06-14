import re
import shutil
import sqlite3
import subprocess
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

_CHROME_EPOCH = datetime(1601, 1, 1)
_URL_PATTERN = re.compile(rb"https?://[\x21-\x7e]{4,255}")


# ── Timestamp helpers ─────────────────────────────────────────────────────────

def _chrome_ts(microseconds) -> str:
    """Chrome FILETIME: microseconds since 1601-01-01."""
    try:
        if not microseconds or microseconds <= 0:
            return "N/A"
        return (_CHROME_EPOCH + timedelta(microseconds=int(microseconds))).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    except (OverflowError, OSError, ValueError):
        return "N/A"


def _firefox_ts(microseconds) -> str:
    """Firefox timestamp: microseconds since Unix epoch."""
    try:
        if not microseconds or microseconds <= 0:
            return "N/A"
        return datetime.fromtimestamp(int(microseconds) / 1_000_000).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    except (OSError, ValueError, OverflowError):
        return "N/A"


# ── SQLite helpers ────────────────────────────────────────────────────────────

def _open_db_copy(db_path: Path) -> Tuple[Optional[sqlite3.Connection], Optional[str]]:
    """Copy a SQLite DB (and WAL/SHM companions) to a private temp dir.

    Returns (connection, tmpdir_path) or (None, None) on failure.
    The WAL is copied alongside so SQLite auto-merges it on open.
    Caller must close the connection and remove tmpdir when done.
    """
    tmp = None
    try:
        tmp = tempfile.mkdtemp(prefix="forensiq_db_")
        dest = Path(tmp) / db_path.name
        shutil.copy2(db_path, dest)
        for suffix in ("-wal", "-shm"):
            companion = db_path.parent / (db_path.name + suffix)
            if companion.exists():
                shutil.copy2(companion, Path(tmp) / companion.name)
        conn = sqlite3.connect(str(dest))
        conn.row_factory = sqlite3.Row
        return conn, tmp
    except Exception:
        if tmp:
            shutil.rmtree(tmp, ignore_errors=True)
        return None, None


def _query(conn: sqlite3.Connection, sql: str, params: tuple = ()) -> List[sqlite3.Row]:
    """Execute SQL, returning rows; silently returns [] on any error."""
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        return cur.fetchall()
    except Exception:
        return []


def _close(conn: Optional[sqlite3.Connection], tmp: Optional[str]) -> None:
    if conn:
        try:
            conn.close()
        except Exception:
            pass
    if tmp:
        shutil.rmtree(tmp, ignore_errors=True)


# ── Chrome / Edge extraction ──────────────────────────────────────────────────

def _extract_chrome_history(
    db_path: Path,
) -> Tuple[List[Dict], List[Dict]]:
    history: List[Dict] = []
    downloads: List[Dict] = []
    conn, tmp = _open_db_copy(db_path)
    if not conn:
        return history, downloads
    try:
        for row in _query(
            conn,
            "SELECT url, title, visit_count, last_visit_time FROM urls ORDER BY last_visit_time DESC",
        ):
            history.append(
                {
                    "source": "Chrome/Edge",
                    "type": "history",
                    "url": row["url"] or "",
                    "title": row["title"] or "",
                    "visit_count": row["visit_count"] or 0,
                    "last_visit_time": _chrome_ts(row["last_visit_time"]),
                    "recovered": False,
                }
            )
        for row in _query(
            conn,
            "SELECT target_path, total_bytes, start_time, end_time, danger_type FROM downloads",
        ):
            downloads.append(
                {
                    "source": "Chrome/Edge",
                    "type": "download",
                    "target_path": row["target_path"] or "",
                    "total_bytes": row["total_bytes"] or 0,
                    "start_time": _chrome_ts(row["start_time"]),
                    "end_time": _chrome_ts(row["end_time"]),
                    "danger_type": row["danger_type"],
                    "recovered": False,
                }
            )
    finally:
        _close(conn, tmp)
    return history, downloads


def _extract_chrome_cookies(db_path: Path) -> List[Dict]:
    cookies: List[Dict] = []
    conn, tmp = _open_db_copy(db_path)
    if not conn:
        return cookies
    try:
        for row in _query(
            conn,
            "SELECT host_key, name, path, expires_utc, is_secure, is_httponly FROM cookies",
        ):
            cookies.append(
                {
                    "source": "Chrome/Edge",
                    "type": "cookie",
                    "host_key": row["host_key"] or "",
                    "name": row["name"] or "",
                    "path": row["path"] or "",
                    "expires_utc": _chrome_ts(row["expires_utc"]),
                    "is_secure": bool(row["is_secure"]),
                    "is_httponly": bool(row["is_httponly"]),
                    "recovered": False,
                }
            )
    finally:
        _close(conn, tmp)
    return cookies


# ── Firefox extraction ────────────────────────────────────────────────────────

def _extract_firefox_history(db_path: Path) -> Tuple[List[Dict], List[Dict]]:
    history: List[Dict] = []
    downloads: List[Dict] = []
    conn, tmp = _open_db_copy(db_path)
    if not conn:
        return history, downloads
    try:
        for row in _query(
            conn,
            "SELECT url, title, visit_count, last_visit_date FROM moz_places"
            " WHERE url IS NOT NULL ORDER BY last_visit_date DESC",
        ):
            history.append(
                {
                    "source": "Firefox",
                    "type": "history",
                    "url": row["url"] or "",
                    "title": row["title"] or "",
                    "visit_count": row["visit_count"] or 0,
                    "last_visit_time": _firefox_ts(row["last_visit_date"]),
                    "recovered": False,
                }
            )
        # Downloads via moz_annos annotation
        attr_rows = _query(
            conn,
            "SELECT id FROM moz_anno_attributes WHERE name = 'downloads/destinationFileName'",
        )
        if attr_rows:
            attr_id = attr_rows[0]["id"]
            for row in _query(
                conn,
                "SELECT p.url FROM moz_annos a"
                " JOIN moz_places p ON a.place_id = p.id"
                " WHERE a.anno_attribute_id = ?",
                (attr_id,),
            ):
                downloads.append(
                    {
                        "source": "Firefox",
                        "type": "download",
                        "url": row["url"] or "",
                        "target_path": "",
                        "total_bytes": 0,
                        "start_time": "N/A",
                        "end_time": "N/A",
                        "danger_type": None,
                        "recovered": False,
                    }
                )
    finally:
        _close(conn, tmp)
    return history, downloads


def _extract_firefox_cookies(db_path: Path) -> List[Dict]:
    cookies: List[Dict] = []
    conn, tmp = _open_db_copy(db_path)
    if not conn:
        return cookies
    try:
        for row in _query(
            conn,
            "SELECT host, name, path, expiry, isSecure, isHttpOnly FROM moz_cookies",
        ):
            cookies.append(
                {
                    "source": "Firefox",
                    "type": "cookie",
                    "host_key": row["host"] or "",
                    "name": row["name"] or "",
                    "path": row["path"] or "",
                    "expires_utc": str(row["expiry"]),
                    "is_secure": bool(row["isSecure"]),
                    "is_httponly": bool(row["isHttpOnly"]),
                    "recovered": False,
                }
            )
    finally:
        _close(conn, tmp)
    return cookies


# ── Public API ────────────────────────────────────────────────────────────────

def extract_browser_artifacts(evidence_path: Path) -> Dict[str, List[Dict]]:
    """Scan evidence_path recursively for Chrome/Edge and Firefox browser databases.

    Returns {"history": [...], "downloads": [...], "cookies": [...]}.
    Always works on DB copies to avoid locking issues.
    """
    artifacts: Dict[str, List[Dict]] = {"history": [], "downloads": [], "cookies": []}

    # Chrome / Edge
    for db in sorted(evidence_path.rglob("History")):
        if not db.is_file():
            continue
        h, d = _extract_chrome_history(db)
        artifacts["history"].extend(h)
        artifacts["downloads"].extend(d)

    for db in sorted(evidence_path.rglob("Cookies")):
        if not db.is_file():
            continue
        artifacts["cookies"].extend(_extract_chrome_cookies(db))

    # Firefox
    for db in sorted(evidence_path.rglob("places.sqlite")):
        if not db.is_file():
            continue
        h, d = _extract_firefox_history(db)
        artifacts["history"].extend(h)
        artifacts["downloads"].extend(d)

    for db in sorted(evidence_path.rglob("cookies.sqlite")):
        if not db.is_file():
            continue
        artifacts["cookies"].extend(_extract_firefox_cookies(db))

    return artifacts


def recover_deleted_history(evidence_path: Path) -> List[Dict]:
    """Attempt to recover deleted browser history via WAL replay and freelist scanning.

    Returns list of record dicts with recovered=True.
    """
    recovered: List[Dict] = []
    seen_urls: set = set()

    db_files = sorted(
        list(evidence_path.rglob("History")) + list(evidence_path.rglob("places.sqlite"))
    )

    for db_file in db_files:
        if not db_file.is_file():
            continue

        # ── WAL recovery ─────────────────────────────────────────────────────
        wal = db_file.parent / (db_file.name + "-wal")
        if wal.exists() and wal.stat().st_size > 0:
            conn, tmp = _open_db_copy(db_file)  # _open_db_copy already copies the WAL
            if conn:
                try:
                    for row in _query(
                        conn,
                        "SELECT url, title, visit_count, last_visit_time FROM urls"
                        " ORDER BY last_visit_time DESC",
                    ):
                        recovered.append(
                            {
                                "source": "Chrome/Edge",
                                "type": "history",
                                "url": row["url"] or "",
                                "title": row["title"] or "",
                                "visit_count": row["visit_count"] or 0,
                                "last_visit_time": _chrome_ts(row["last_visit_time"]),
                                "recovered": True,
                                "detail": "Recovered from WAL (Write-Ahead Log)",
                            }
                        )
                    for row in _query(
                        conn,
                        "SELECT url, title, visit_count, last_visit_date FROM moz_places"
                        " WHERE url IS NOT NULL ORDER BY last_visit_date DESC",
                    ):
                        recovered.append(
                            {
                                "source": "Firefox",
                                "type": "history",
                                "url": row["url"] or "",
                                "title": row["title"] or "",
                                "visit_count": row["visit_count"] or 0,
                                "last_visit_time": _firefox_ts(row["last_visit_date"]),
                                "recovered": True,
                                "detail": "Recovered from WAL (Write-Ahead Log)",
                            }
                        )
                finally:
                    _close(conn, tmp)

        # ── Freelist / raw page scan ─────────────────────────────────────────
        # Populate live-URL set for deduplication
        conn, tmp = _open_db_copy(db_file)
        if conn:
            try:
                for (url,) in _query(conn, "SELECT url FROM urls WHERE url IS NOT NULL"):
                    if url:
                        seen_urls.add(url)
                for (url,) in _query(
                    conn, "SELECT url FROM moz_places WHERE url IS NOT NULL"
                ):
                    if url:
                        seen_urls.add(url)
            finally:
                _close(conn, tmp)

        try:
            raw = db_file.read_bytes()
        except (OSError, IOError):
            continue

        for match in _URL_PATTERN.findall(raw):
            try:
                url = match.decode("utf-8", errors="ignore").strip()
                if not url or url in seen_urls:
                    continue
                # Skip if this is just a live URL with trailing page garbage appended
                if any(
                    url.startswith(live) and len(url) - len(live) < 60
                    for live in seen_urls
                ):
                    continue
                seen_urls.add(url)
                recovered.append(
                    {
                        "source": "Freelist Recovery",
                        "type": "history",
                        "url": url,
                        "recovered": True,
                        "detail": "Recovered from SQLite freelist/unallocated pages",
                    }
                )
            except Exception:
                pass

    return recovered


def get_dns_cache() -> List[Dict]:
    """Run ipconfig /displaydns (Windows only) and parse Record Name entries."""
    import platform

    if platform.system() != "Windows":
        return []
    try:
        result = subprocess.run(
            ["ipconfig", "/displaydns"],
            capture_output=True,
            text=True,
            timeout=15,
            encoding="utf-8",
            errors="replace",
        )
        entries: List[Dict] = []
        seen: set = set()
        for line in result.stdout.splitlines():
            stripped = line.strip()
            if stripped.lower().startswith("record name") and "." in stripped:
                hostname = stripped.split(":", 1)[-1].strip().rstrip(".")
                if hostname and hostname not in seen:
                    seen.add(hostname)
                    entries.append(
                        {
                            "type": "dns_cache",
                            "hostname": hostname,
                            "detail": "From ipconfig /displaydns",
                        }
                    )
        return entries
    except Exception:
        return []


def get_prefetch_evidence() -> List[Dict]:
    """List Chrome/Firefox/Edge prefetch files in C:\\Windows\\Prefetch (Windows only)."""
    import platform

    if platform.system() != "Windows":
        return []
    prefetch_dir = Path(r"C:\Windows\Prefetch")
    if not prefetch_dir.exists():
        return []

    _browser_map = {
        "CHROME": "Chrome",
        "FIREFOX": "Firefox",
        "MSEDGE": "Microsoft Edge",
    }
    results: List[Dict] = []
    for pat in ("CHROME*.pf", "FIREFOX*.pf", "MSEDGE*.pf"):
        for pf in sorted(prefetch_dir.glob(pat)):
            try:
                mtime = datetime.fromtimestamp(pf.stat().st_mtime).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
                browser = next(
                    (name for key, name in _browser_map.items() if pf.name.startswith(key)),
                    "Unknown",
                )
                results.append(
                    {
                        "type": "prefetch",
                        "browser": browser,
                        "filename": pf.name,
                        "last_executed": mtime,
                    }
                )
            except Exception:
                pass
    return results
