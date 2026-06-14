"""Generate sample evidence files for ForensIQ testing. Run after pip install -r requirements.txt."""
import os
import time
from pathlib import Path

DOCS = Path("sample_evidence/docs")
IMAGES = Path("sample_evidence/images")
EVIDENCE = Path("sample_evidence")


def create_text_files():
    (DOCS / "incident_report.txt").write_text(
        "INCIDENT REPORT\n"
        "Date: 2024-01-15\n"
        "Location: Server Room B\n"
        "Severity: HIGH\n\n"
        "Unauthorized access detected on primary database server.\n"
        "Login attempts from 192.168.1.105 at 03:47 AM.\n"
        "Data exfiltration suspected. Immediate forensic investigation required.\n",
        encoding="utf-8",
    )
    print("  [+] incident_report.txt")

    # Backdate modification time to simulate a timestamp anomaly
    notes_path = DOCS / "case_notes.txt"
    notes_path.write_text(
        "CASE NOTES — Investigator: J. Smith\n"
        "Collected USB drive from suspect workstation (Desk 7, Floor 3).\n"
        "Device serial: USB-2024-XYZ-789\n"
        "Chain of custody maintained throughout collection.\n",
        encoding="utf-8",
    )
    past = time.time() - 60 * 60 * 24 * 30  # 30 days ago
    os.utime(notes_path, (past, past))
    print("  [+] case_notes.txt (mtime backdated 30 days — triggers anomaly)")

    (DOCS / "system_log.txt").write_text(
        "2024-01-14 23:58:01  USER_LOGIN    root\n"
        "2024-01-14 23:58:45  FILE_ACCESS   /etc/passwd\n"
        "2024-01-14 23:59:12  FILE_ACCESS   /etc/shadow\n"
        "2024-01-15 00:01:33  NETWORK_CONN  10.0.0.42:4444\n"
        "2024-01-15 00:03:22  USER_LOGOUT   root\n",
        encoding="utf-8",
    )
    print("  [+] system_log.txt")


def create_image_file():
    from PIL import Image

    img = Image.new("RGB", (640, 480), color=(70, 130, 180))
    out = IMAGES / "crime_scene_photo.jpg"

    try:
        import piexif

        exif_dict = {
            "0th": {
                piexif.ImageIFD.Make: b"ForensIQ",
                piexif.ImageIFD.Model: b"EvidenceCam 3000",
                piexif.ImageIFD.Artist: b"Digital Forensics Lab",
                piexif.ImageIFD.DateTime: b"2024:01:15 14:30:00",
                piexif.ImageIFD.Software: b"ForensIQ Capture v1.0",
            },
            "Exif": {
                piexif.ExifIFD.DateTimeOriginal: b"2024:01:15 14:30:00",
                piexif.ExifIFD.DateTimeDigitized: b"2024:01:15 14:30:01",
            },
            "GPS": {
                piexif.GPSIFD.GPSLatitudeRef: b"N",
                piexif.GPSIFD.GPSLatitude: ((40, 1), (26, 1), (2760, 100)),
                piexif.GPSIFD.GPSLongitudeRef: b"W",
                piexif.GPSIFD.GPSLongitude: ((79, 1), (58, 1), (3000, 100)),
                piexif.GPSIFD.GPSAltitudeRef: 0,
                piexif.GPSIFD.GPSAltitude: (280, 1),
            },
            "1st": {},
            "thumbnail": None,
        }
        img.save(out, "JPEG", exif=piexif.dump(exif_dict), quality=85)
        print("  [+] crime_scene_photo.jpg (EXIF: camera info + GPS coordinates)")
    except ImportError:
        # piexif not available — use Pillow's built-in EXIF for basic tags
        exif = img.getexif()
        exif[271] = "ForensIQ"         # Make
        exif[272] = "EvidenceCam 3000"  # Model
        exif[315] = "Digital Forensics Lab"  # Artist
        exif[306] = "2024:01:15 14:30:00"   # DateTime
        img.save(out, "JPEG", exif=exif.tobytes(), quality=85)
        print("  [+] crime_scene_photo.jpg (basic EXIF, no GPS — install piexif for full support)")


def create_hidden_file():
    hidden = EVIDENCE / ".case_metadata"
    hidden.write_text(
        "# Hidden Case Metadata\n"
        "case_id: CASE-001\n"
        "classification: CONFIDENTIAL\n"
        "created_by: automated_collection_agent\n"
        "note: This file was intentionally concealed\n",
        encoding="utf-8",
    )
    print("  [+] .case_metadata (hidden file — dot-prefixed)")


if __name__ == "__main__":
    DOCS.mkdir(parents=True, exist_ok=True)
    IMAGES.mkdir(parents=True, exist_ok=True)

    print("Creating sample evidence files...")
    create_text_files()
    create_image_file()
    create_hidden_file()

    print("\nDone. Run:")
    print('  python main.py analyze ./sample_evidence --case-id CASE-001 --investigator "Test User"')
