# ForensIQ — Digital Forensics Evidence Analyzer

A Python CLI tool for analyzing digital forensics evidence. Phase 1 covers recursive file metadata extraction, timestamp anomaly detection, and EXIF parsing from images.

---

## Features (Phase 1)

- Recursively scans all files in an evidence directory
- Extracts file name, extension, size, and created/modified/accessed timestamps
- Detects timestamp anomalies: `mtime < ctime` (possible backdating), `atime < mtime`
- Identifies hidden files (dot-prefixed)
- Extracts EXIF metadata from `.jpg`, `.jpeg`, `.tiff`, `.png` files:
  - Camera make/model, date taken, author/artist
  - GPS coordinates (if present)
- Prints a clean terminal report with a summary

---

## Installation

```bash
cd forensiq
pip install -r requirements.txt
python create_samples.py   # generate sample evidence files
```

---

## Usage

```bash
python main.py analyze <evidence_dir> --case-id <ID> --investigator "<Name>" [options]
```

### Example

```bash
python main.py analyze ./sample_evidence --case-id CASE-001 --investigator "Test User"
```

### Options

| Argument / Option  | Description                        | Default          |
|--------------------|------------------------------------|------------------|
| `evidence_dir`     | Path to evidence directory         | *(required)*     |
| `--case-id`        | Case identifier                    | *(required)*     |
| `--investigator`   | Investigator name                  | *(required)*     |
| `--device`         | Device description                 | `Unknown Device` |
| `--output`         | Output directory for future reports| `output/`        |

---

## Project Structure

```
forensiq/
├── main.py                     # CLI entry point (Typer)
├── modules/
│   ├── __init__.py
│   └── metadata_extractor.py   # Core metadata + EXIF extraction
├── sample_evidence/
│   ├── images/                 # JPEG/TIFF evidence images
│   ├── docs/                   # Text-based evidence files
│   └── .case_metadata          # Hidden file (demonstrates detection)
├── output/                     # Reports go here (Phase 2+)
├── create_samples.py           # Generates sample evidence
├── requirements.txt
└── README.md
```

---

## Roadmap

- **Phase 2** — PDF report generation with ReportLab + Jinja2 templates
- **Phase 3** — Hash verification (MD5/SHA-256), chain of custody log
- **Phase 4** — File carving, deleted file detection
