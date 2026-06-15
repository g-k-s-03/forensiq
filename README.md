# ForensIQ — Digital Forensics Evidence Analyzer

A Python CLI tool for analyzing digital forensics evidence.

---

## Features

### Phase 1 — Metadata Extraction
- Recursively scans all files in an evidence directory
- Extracts file name, extension, size, and created/modified/accessed timestamps
- Detects timestamp anomalies: `mtime < ctime` (possible backdating), `atime < mtime`
- Identifies hidden files (dot-prefixed names)
- Extracts EXIF metadata from `.jpg`, `.jpeg`, `.tiff`, `.png` files:
  - Camera make/model, date taken, author/artist, GPS coordinates

### Phase 2 — Hash Checker & Tamper Detection
- SHA-256 hashes every file using 64 KB chunks (efficient for large evidence)
- Saves a hash manifest to `output/<case_id>_hashes.json` on every run
- Compares against a saved baseline to detect:
  - `HASH_MISMATCH` (HIGH) — file content changed since baseline
  - `NEW_FILE` (MEDIUM) — file not present in baseline
  - `DELETED_FILE` (HIGH) — file in baseline but now missing
- Flags from metadata regardless of baseline:
  - `TIMESTAMP_ANOMALY` (MEDIUM) — mtime or atime inconsistency
  - `HIDDEN_FILE` (LOW) — dot-prefixed filename
- Color-coded tamper flags table: HIGH=red, MEDIUM=yellow, LOW=cyan

### Phase 3 — Hash Integrity Engine (Deep Analysis)
- Every flag now cites a specific forensic rule ID (R-01 through R-10)
- **Entropy analysis** — Shannon entropy on plaintext file types (.txt, .log, .csv, etc.):
  - `HIGH_ENTROPY` (MEDIUM) — entropy > 7.2 suggests encrypted/compressed payload
- **Magic bytes detection** — reads first 16 bytes and compares against known signatures:
  - Detects: JPEG, PNG, PDF, ZIP/Office, OLE, RTF, PE Executable, ELF
  - `DISGUISED_FILE` (HIGH) — file extension does not match internal magic bytes
  - `SUSPICIOUS_EXECUTABLE` (HIGH) — .exe/.dll found in evidence collection
- **EXIF strip detection**:
  - `EXIF_STRIPPED` (MEDIUM) — JPEG with no EXIF tags, consistent with anti-forensic wiping
- **Anti-forensic detection**:
  - `ANTI_FORENSIC` (HIGH) — file hash changed but timestamps appear untouched (timestamp preservation attack)
- Summary now reports anti-forensic indicators, disguised files, and high-entropy files separately

> **Note:** All tamper determinations are rule-based and deterministic — no AI inference is used.
> Each flag cites the specific forensic rule under which it was raised.

### Phase 4 — Browser Forensics & Deleted History Recovery
- **Live extraction** from Chrome/Edge and Firefox SQLite databases:
  - Chrome/Edge: `History` (urls + downloads tables), `Cookies`
  - Firefox: `places.sqlite` (moz_places + download annotations), `cookies.sqlite`
  - Always works on a file copy to avoid locking the live browser database
- **WAL (Write-Ahead Log) recovery**: if a `-wal` companion file is present and non-empty,
  SQLite auto-merges it on connection — records appearing only in the WAL
  (not yet checkpointed to the main DB) are surfaced and marked `Recovered: Yes`
- **Freelist page scanning**: reads raw DB bytes and applies a regex
  (`https?://[\x21-\x7e]{4,255}`) to find URL strings in SQLite's
  freed/unallocated pages that are no longer reachable through the B-tree index.
  Results are deduplicated against live records.
- **DNS cache snapshot**: runs `ipconfig /displaydns` (Windows) and extracts
  all resolved hostnames — cross-referencing DNS entries with browser history
  can corroborate or contradict claimed browsing activity.
- **Prefetch evidence**: lists Chrome/Firefox/Edge `.pf` files in
  `C:\Windows\Prefetch` with their last-execution timestamps.
- Summary reports: live history count, recovered record count, download count,
  DNS entries, and prefetch traces.

> **Important:** Deleted record recovery is forensically significant but results
> should be treated as **INFERRED** evidence, not **CONFIRMED**, until corroborated
> by other artifacts. Raw byte scanning may surface fragments, partial URLs, or
> data from earlier sessions that were legitimately overwritten.

### Phase 5 — Forensic Timeline Builder
- **Unified chronological timeline**: merges all artifact sources into a single sorted event list:
  - `FILE_CREATED` / `FILE_MODIFIED` — from file system metadata
  - `BROWSER_VISIT` — from live browser history (Chrome/Edge/Firefox)
  - `BROWSER_DOWNLOAD` — from browser download records
  - `BROWSER_COOKIE` — from browser cookie stores (using expiry as event anchor)
  - `DNS_LOOKUP` — from DNS cache snapshot (timestamped at analysis time)
  - `BROWSER_EXECUTED` — from Windows Prefetch (last-run timestamp)
- **Confidence levels** assigned per event:
  - `CONFIRMED` (green) — directly retrieved from a live, indexed source
  - `INFERRED` (yellow) — derived artifact (e.g. DNS cache entry, timestamp anomaly)
  - `RECOVERED` (cyan) — retrieved from deleted/unallocated SQLite pages or WAL files
- **JSON export**: timeline written to `output/<case_id>_timeline.json` (artifact payloads excluded to keep file compact)
- **Forensic Narrative**: auto-generated template paragraph covering earliest/latest confirmed events, browser activity summary, recovered record count, and any anti-forensic or disguised-file alerts; closes with the mandatory Section 65B disclaimer
- Summary line: `Timeline events: N total (X CONFIRMED / Y INFERRED / Z RECOVERED)`

> **Confidence note:** `CONFIRMED` does not mean the event is legally admissible —
> it means the record was found in an active, indexed location. All findings
> require examiner review. The narrative disclaimer (`Section 65B of the Indian
> Evidence Act, 1872`) is printed automatically on every run.

---

## Installation

```bash
cd forensiq
pip install -r requirements.txt
python create_samples.py          # Phase 1 evidence (metadata, EXIF)
python create_phase3_samples.py   # Phase 3 evidence (disguised file, high-entropy, wiped JPEG)
python create_browser_samples.py  # Phase 4 evidence (Chrome/Firefox SQLite DBs)
```

---

## Usage

### `analyze` — scan and detect tampering

```bash
python main.py analyze <evidence_dir> --case-id <ID> --investigator "<Name>" [options]
```

| Argument / Option | Description                         | Default          |
|-------------------|-------------------------------------|------------------|
| `evidence_dir`    | Path to evidence directory          | *(required)*     |
| `--case-id`       | Case identifier                     | *(required)*     |
| `--investigator`  | Investigator name                   | *(required)*     |
| `--device`        | Device description                  | `Unknown Device` |
| `--output`        | Output directory for reports/hashes | `output/`        |
| `--baseline`      | Path to baseline hashes JSON        | *(none)*         |

**Example — first run (no baseline):**
```bash
python main.py analyze ./sample_evidence --case-id CASE-001 --investigator "Test User"
```

**Example — with tamper detection:**
```bash
python main.py analyze ./sample_evidence --case-id CASE-002 --investigator "Test User" --baseline baseline.json
```

---

### `save-baseline` — snapshot current hashes

```bash
python main.py save-baseline <evidence_dir> [--output <file>]
```

| Argument / Option | Description                  | Default                |
|-------------------|------------------------------|------------------------|
| `evidence_dir`    | Path to evidence directory   | *(required)*           |
| `--output`        | Output JSON file path        | `baseline_hashes.json` |

**Example:**
```bash
python main.py save-baseline ./sample_evidence --output baseline.json
```

---

## Tamper Detection Workflow

```bash
# 1. Snapshot clean state
python main.py save-baseline ./sample_evidence --output baseline.json

# 2. (time passes — suspect may have modified files)

# 3. Re-analyze against baseline
python main.py analyze ./sample_evidence --case-id CASE-002 --investigator "J. Smith" --baseline baseline.json
```

---

## Project Structure

```
forensiq/
├── main.py                     # CLI entry point (Typer)
├── modules/
│   ├── __init__.py
│   ├── metadata_extractor.py   # File metadata + EXIF extraction
│   └── hash_checker.py         # SHA-256 hashing + tamper detection
├── sample_evidence/
│   ├── images/                 # JPEG/TIFF evidence images
│   ├── docs/                   # Text-based evidence files
│   └── .case_metadata          # Hidden file (demonstrates detection)
├── output/                     # Hash manifests and future reports
├── create_samples.py           # Generates sample evidence files
├── requirements.txt
└── README.md
```

---

## Tamper Rule Reference

| Rule  | Flag Type              | Severity | Trigger                                                   |
|-------|------------------------|----------|-----------------------------------------------------------|
| R-01  | `HASH_MISMATCH`        | HIGH     | SHA-256 digest differs from verified baseline             |
| R-02  | `NEW_FILE`             | MEDIUM   | File absent from baseline snapshot                        |
| R-03  | `DELETED_FILE`         | HIGH     | File present in baseline but missing from evidence        |
| R-04  | `TIMESTAMP_ANOMALY`    | MEDIUM   | mtime < ctime or atime < mtime                            |
| R-05  | `HIDDEN_FILE`          | LOW      | Dot-prefixed filename used for concealment                |
| R-06  | `HIGH_ENTROPY`         | MEDIUM   | Shannon entropy > 7.2 in a plaintext file type            |
| R-07  | `DISGUISED_FILE`       | HIGH     | File extension does not match internal magic bytes        |
| R-08  | `SUSPICIOUS_EXECUTABLE`| HIGH     | .exe / .dll found in evidence collection                  |
| R-09  | `EXIF_STRIPPED`        | MEDIUM   | JPEG image lacks EXIF metadata                            |
| R-10  | `ANTI_FORENSIC`        | HIGH     | Content changed (hash mismatch) but timestamps unmodified |

---

### Phase 6 — Court-Admissible PDF Report Generator
- **ReportLab-powered PDF** with A4 pages, 2.5cm margins, page headers and footers
- **9-section structure**:
  1. Cover page — case details, Section 65B subtitle, RESTRICTED classification
  2. Section 65B Certificate — investigator name filled in, with signature block
  3. Chain of Custody — 3-step acquisition/examination/report table
  4. Case Summary — examination details + findings overview with counts
  5. File Inventory & Hash Manifest — all files with SHA-256 (first 24 chars), flagged files marked
  6. Tamper Detection Findings — all flags with rule ID, color-coded severity
  7. Browser Forensic Findings — history, downloads, cookies, DNS cache subsections
  8. Forensic Timeline — chronological events; unknown-timestamp events listed separately
  9. Examiner Declaration — declaration text, signature block, IMPORTANT note box
- **"Page X of Y"** footer via two-pass numbered canvas (no third-party dependency)
- **Color-coded severity**: HIGH=red, MEDIUM=orange, LOW=blue in PDF tables
- **Zero AI conclusions**: every section uses only factual, tabular, observable data
- **Output**: `output/<case_id>_forensics_report.pdf`

> **LEGAL DISCLAIMER:** ForensIQ generates forensic worksheets for examiner review.
> Reports require physical signature and Section 65B certification by a qualified
> forensic examiner before submission to any court. This tool does not provide
> legal conclusions.

## Roadmap

- **Phase 7** — Chain of custody log, investigator sign-off
- **Phase 8** — File carving, deleted file recovery
