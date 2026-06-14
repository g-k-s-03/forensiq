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

---

## Installation

```bash
cd forensiq
pip install -r requirements.txt
python create_samples.py   # generate sample evidence files
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

## Roadmap

- **Phase 4** — PDF report generation with ReportLab + Jinja2 templates
- **Phase 5** — Chain of custody log, investigator sign-off
- **Phase 6** — File carving, deleted file recovery
