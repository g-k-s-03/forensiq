# Contributing to ForensIQ

## Running the Project

```bash
# Install dependencies
pip install -r requirements.txt

# Generate sample evidence for all phases
python create_samples.py
python create_phase3_samples.py
python create_browser_samples.py

# Snapshot a baseline
python main.py save-baseline ./sample_evidence --output baseline.json

# Full analysis run
python main.py analyze ./sample_evidence \
    --case-id DEV-001 \
    --investigator "Your Name" \
    --baseline baseline.json \
    --json
```

All output files go to `output/` (git-ignored). Delete them freely between runs.

---

## Adding a New Forensic Rule

1. **Define the rule in `modules/hash_checker.py`**

   Add an entry to the `TAMPER_RULES` dict at the top of the file:
   ```python
   TAMPER_RULES: Dict[str, str] = {
       ...
       "MY_NEW_FLAG": "Rule R-11: Description of what this rule detects",
   }
   ```

2. **Write a detector function**

   Add a function that returns a list of flag dicts:
   ```python
   def detect_my_condition(metadata_results: List[Dict]) -> List[Dict]:
       flags = []
       for r in metadata_results:
           if <condition>:
               flags.append({
                   "type":     "MY_NEW_FLAG",
                   "severity": "HIGH",   # HIGH | MEDIUM | LOW
                   "file":     r.get("rel_path", r.get("name", "")),
                   "detail":   "Human-readable observation about what was found.",
                   "rule":     TAMPER_RULES["MY_NEW_FLAG"],
               })
       return flags
   ```

3. **Call it from `detect_tampering()`**

   Append your function's output inside `detect_tampering()`:
   ```python
   def detect_tampering(metadata_results, baseline_hashes, current_hashes):
       flags = []
       ...
       flags.extend(detect_my_condition(metadata_results))
       ...
   ```

4. **Update the README**

   Add the new rule to the Forensic Rule Set table in `README.md`.

5. **Add a sample evidence file** (optional but recommended)

   Add a file to `create_phase3_samples.py` (or a new `create_phaseN_samples.py`)
   that triggers the new rule, so it is always tested during development.

---

## Adding a New Browser Parser

Browser parsers live in `modules/browser_forensics.py`. Each parser follows this pattern:

1. **Write a private extraction function**

   ```python
   def _extract_mybrowser_history(db_path: Path) -> Tuple[List[Dict], List[Dict]]:
       history, downloads = [], []
       conn, tmp = _open_db_copy(db_path)
       if not conn:
           return history, downloads
       try:
           for row in _query(conn, "SELECT url, title, visit_count, last_visit FROM visits"):
               history.append({
                   "source":          "MyBrowser",
                   "type":            "history",
                   "url":             row["url"] or "",
                   "title":           row["title"] or "",
                   "visit_count":     row["visit_count"] or 0,
                   "last_visit_time": _some_ts_converter(row["last_visit"]),
                   "recovered":       False,
               })
       finally:
           _close(conn, tmp)
       return history, downloads
   ```

   Key rules:
   - Always use `_open_db_copy()` -- never open the original DB directly.
   - Always use `try/finally: _close(conn, tmp)` to clean up the temp dir.
   - Use `_query()` for all SQL -- it silently returns `[]` on schema mismatch.
   - Use `_CHROME_EPOCH` or `_firefox_ts()` helpers for timestamp conversion,
     or write your own converter that returns `"YYYY-MM-DD HH:MM:SS"` strings.

2. **Register it in `extract_browser_artifacts()`**

   Add a glob pattern and call your extractor:
   ```python
   for db in sorted(evidence_path.rglob("mybrowser_history.db")):
       if not db.is_file():
           continue
       h, d = _extract_mybrowser_history(db)
       artifacts["history"].extend(h)
       artifacts["downloads"].extend(d)
   ```

3. **Add freelist scanning** (optional)

   The existing `recover_deleted_history()` automatically scans any file matched
   by `rglob("History")` or `rglob("places.sqlite")`. To include your DB:
   ```python
   db_files = sorted(
       list(evidence_path.rglob("History"))
       + list(evidence_path.rglob("places.sqlite"))
       + list(evidence_path.rglob("mybrowser_history.db"))  # add here
   )
   ```

---

## Code Style

- **Python 3.9+** compatible (uses `list[str]` type hints only in type annotations,
  not in runtime code; use `List` from `typing` for function signatures).
- **No comments** unless the WHY is non-obvious. Well-named identifiers carry the WHAT.
- **No docstrings** on private helpers (prefixed `_`). Public functions get a one-line docstring.
- **No unnecessary abstractions**: three similar lines is better than a premature helper.
- **No AI/ML inference**: every flag must be deterministic and cite a specific rule ID.
- **Error handling**: only at system boundaries (file I/O, subprocess, SQLite). Do not
  wrap internal logic in try/except.
- **Truncation**: use `_trunc(s, n)` in `main.py` for display strings; raw data in
  dicts/JSON is always full-length.
- **Relative paths**: all hash/tamper keys use forward-slash relative paths:
  `str(path.relative_to(base)).replace("\\", "/")`.
