"""Create sample browser SQLite databases for ForensIQ Phase 4 testing."""
import sqlite3
from datetime import datetime
from pathlib import Path

CHROME_DIR  = Path("sample_evidence/browser/Chrome")
FIREFOX_DIR = Path("sample_evidence/browser/Firefox")

_CHROME_EPOCH = datetime(1601, 1, 1)


def _chrome_ts(dt: datetime) -> int:
    """Datetime -> Chrome microseconds since 1601-01-01."""
    return int((dt - _CHROME_EPOCH).total_seconds() * 1_000_000)


def _firefox_ts(dt: datetime) -> int:
    """Datetime -> Firefox microseconds since Unix epoch."""
    return int(dt.timestamp() * 1_000_000)


def create_chrome_history():
    db = CHROME_DIR / "History"
    conn = sqlite3.connect(str(db))
    c = conn.cursor()

    c.execute("""
        CREATE TABLE urls (
            id           INTEGER PRIMARY KEY,
            url          TEXT NOT NULL,
            title        TEXT,
            visit_count  INTEGER DEFAULT 0,
            last_visit_time INTEGER NOT NULL
        )
    """)
    c.execute("""
        CREATE TABLE downloads (
            id           INTEGER PRIMARY KEY,
            target_path  TEXT,
            total_bytes  INTEGER,
            start_time   INTEGER,
            end_time     INTEGER,
            danger_type  INTEGER DEFAULT 0
        )
    """)

    history_rows = [
        (
            "https://www.google.com/search?q=forensics+tools",
            "forensics tools - Google Search",
            15,
            _chrome_ts(datetime(2024, 1, 15, 9, 30, 0)),
        ),
        (
            "https://github.com/open-forensics/autopsy",
            "open-forensics/autopsy - GitHub",
            7,
            _chrome_ts(datetime(2024, 1, 15, 10, 0, 0)),
        ),
        (
            "https://stackoverflow.com/questions/how-to-hide-files-windows",
            "How to hide files on Windows - Stack Overflow",
            3,
            _chrome_ts(datetime(2024, 1, 15, 11, 30, 0)),
        ),
        (
            "https://www.wikileaks.org/documents/index.html",
            "WikiLeaks - Document Archive",
            2,
            _chrome_ts(datetime(2024, 1, 15, 14, 0, 0)),
        ),
        (
            "https://www.torproject.org/download/",
            "Download - Tor Project",
            1,
            _chrome_ts(datetime(2024, 1, 15, 23, 45, 0)),
        ),
    ]
    c.executemany(
        "INSERT INTO urls (url, title, visit_count, last_visit_time) VALUES (?,?,?,?)",
        history_rows,
    )

    download_rows = [
        (
            r"C:\Users\suspect\Downloads\sensitive_data.zip",
            1048576,
            _chrome_ts(datetime(2024, 1, 15, 14, 5, 0)),
            _chrome_ts(datetime(2024, 1, 15, 14, 5, 30)),
            0,
        ),
        (
            r"C:\Users\suspect\Downloads\tor-browser-setup.exe",
            2097152,
            _chrome_ts(datetime(2024, 1, 15, 23, 46, 0)),
            _chrome_ts(datetime(2024, 1, 15, 23, 47, 0)),
            3,  # danger_type 3 = DANGEROUS_URL
        ),
    ]
    c.executemany(
        "INSERT INTO downloads (target_path, total_bytes, start_time, end_time, danger_type)"
        " VALUES (?,?,?,?,?)",
        download_rows,
    )

    conn.commit()
    conn.close()

    # ── Inject a deleted URL into the raw file (simulates freelist page) ─────
    with open(db, "ab") as f:
        f.write(
            b"\x00"
            b"https://deleted-evidence.example.com/secret-page"
            b"\x00"
        )

    print(f"  [+] Chrome/History  (5 history, 2 downloads, 1 injected deleted URL)")


def create_chrome_cookies():
    db = CHROME_DIR / "Cookies"
    conn = sqlite3.connect(str(db))
    c = conn.cursor()

    c.execute("""
        CREATE TABLE cookies (
            id           INTEGER PRIMARY KEY,
            host_key     TEXT,
            name         TEXT,
            path         TEXT,
            expires_utc  INTEGER,
            is_secure    INTEGER DEFAULT 0,
            is_httponly  INTEGER DEFAULT 0
        )
    """)

    rows = [
        (".google.com",      "SID",          "/", _chrome_ts(datetime(2025, 6, 1)), 1, 1),
        (".github.com",      "user_session", "/", _chrome_ts(datetime(2025, 6, 1)), 1, 1),
        (".torproject.org",  "visit",        "/", _chrome_ts(datetime(2024, 3, 1)), 0, 0),
    ]
    c.executemany(
        "INSERT INTO cookies (host_key, name, path, expires_utc, is_secure, is_httponly)"
        " VALUES (?,?,?,?,?,?)",
        rows,
    )
    conn.commit()
    conn.close()
    print("  [+] Chrome/Cookies  (3 cookies)")


def create_firefox_places():
    db = FIREFOX_DIR / "places.sqlite"
    conn = sqlite3.connect(str(db))
    c = conn.cursor()

    c.execute("""
        CREATE TABLE moz_places (
            id             INTEGER PRIMARY KEY,
            url            TEXT NOT NULL,
            title          TEXT,
            visit_count    INTEGER DEFAULT 0,
            last_visit_date INTEGER
        )
    """)
    # Stub tables so Firefox download query doesn't hard-fail
    c.execute("CREATE TABLE moz_anno_attributes (id INTEGER PRIMARY KEY, name TEXT)")
    c.execute("""
        CREATE TABLE moz_annos (
            id                INTEGER PRIMARY KEY,
            place_id          INTEGER,
            anno_attribute_id INTEGER,
            content           TEXT
        )
    """)

    rows = [
        (
            "https://duckduckgo.com/?q=anonymous+browsing",
            "anonymous browsing - DuckDuckGo",
            5,
            _firefox_ts(datetime(2024, 1, 15, 9, 0, 0)),
        ),
        (
            "https://en.wikipedia.org/wiki/Digital_forensics",
            "Digital forensics - Wikipedia",
            3,
            _firefox_ts(datetime(2024, 1, 15, 10, 30, 0)),
        ),
        (
            "https://www.reddit.com/r/privacy",
            "r/privacy - Reddit",
            8,
            _firefox_ts(datetime(2024, 1, 15, 12, 0, 0)),
        ),
        (
            "https://protonmail.com/login",
            "ProtonMail - Secure Login",
            4,
            _firefox_ts(datetime(2024, 1, 15, 15, 30, 0)),
        ),
    ]
    c.executemany(
        "INSERT INTO moz_places (url, title, visit_count, last_visit_date) VALUES (?,?,?,?)",
        rows,
    )
    conn.commit()
    conn.close()
    print("  [+] Firefox/places.sqlite  (4 history records)")


def create_firefox_cookies():
    db = FIREFOX_DIR / "cookies.sqlite"
    conn = sqlite3.connect(str(db))
    c = conn.cursor()

    c.execute("""
        CREATE TABLE moz_cookies (
            id         INTEGER PRIMARY KEY,
            host       TEXT,
            name       TEXT,
            path       TEXT,
            expiry     INTEGER,
            isSecure   INTEGER DEFAULT 0,
            isHttpOnly INTEGER DEFAULT 0
        )
    """)
    rows = [
        ("duckduckgo.com", "ae",           "/", 1767225600, 0, 0),
        ("protonmail.com", "AUTH_SESSION", "/", 1767225600, 1, 1),
    ]
    c.executemany(
        "INSERT INTO moz_cookies (host, name, path, expiry, isSecure, isHttpOnly)"
        " VALUES (?,?,?,?,?,?)",
        rows,
    )
    conn.commit()
    conn.close()
    print("  [+] Firefox/cookies.sqlite (2 cookies)")


if __name__ == "__main__":
    CHROME_DIR.mkdir(parents=True, exist_ok=True)
    FIREFOX_DIR.mkdir(parents=True, exist_ok=True)

    print("Creating sample browser databases...")
    create_chrome_history()
    create_chrome_cookies()
    create_firefox_places()
    create_firefox_cookies()

    print("\nDone. Run:")
    print(
        "  python main.py analyze ./sample_evidence "
        '--case-id CASE-004 --investigator "Test User" --baseline baseline.json'
    )
