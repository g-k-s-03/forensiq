"""Generate Phase 3 sample evidence files for testing deep-analysis rules."""
import os
from pathlib import Path

DISGUISED = Path("sample_evidence/disguised")
DOCS      = Path("sample_evidence/docs")
IMAGES    = Path("sample_evidence/images")


def create_disguised_file():
    """A PDF file renamed to .jpg — triggers R-07 DISGUISED_FILE."""
    DISGUISED.mkdir(parents=True, exist_ok=True)
    out = DISGUISED / "legit_photo.jpg"
    # Write a minimal PDF header so magic bytes = "%PDF"
    out.write_bytes(
        b"%PDF-1.4\n"
        b"% ForensIQ Phase 3 test - PDF content disguised as JPEG\n"
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Kids [] /Count 0 >>\nendobj\n"
        b"xref\n0 3\n0000000000 65535 f\n"
        b"trailer\n<< /Size 3 /Root 1 0 R >>\nstartxref\n9\n%%EOF\n"
    )
    print("  [+] disguised/legit_photo.jpg  (PDF magic bytes under .jpg extension -> R-07)")


def create_high_entropy_file():
    """Random binary data written to a .txt file — triggers R-06 HIGH_ENTROPY."""
    random_payload = os.urandom(4096)   # 4 KB of cryptographically random bytes
    out = DOCS / "encrypted_looking.txt"
    out.write_bytes(random_payload)
    print("  [+] docs/encrypted_looking.txt (random bytes, entropy ~8.0 -> R-06)")


def create_exif_stripped_jpeg():
    """A valid JPEG saved without any EXIF tags — triggers R-09 EXIF_STRIPPED."""
    from PIL import Image
    img = Image.new("RGB", (200, 150), color=(180, 60, 90))
    out = IMAGES / "wiped_photo.jpg"
    img.save(out, "JPEG", quality=85)   # no exif= kwarg -> zero EXIF data
    print("  [+] images/wiped_photo.jpg     (JPEG with no EXIF -> R-09)")


if __name__ == "__main__":
    print("Creating Phase 3 sample evidence files...")
    create_disguised_file()
    create_high_entropy_file()
    create_exif_stripped_jpeg()
    print("\nDone. Run:")
    print(
        "  python main.py analyze ./sample_evidence "
        '--case-id CASE-003 --investigator "Test User" --baseline baseline.json'
    )
