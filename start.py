"""One-command launcher: builds the React frontend then starts the API server."""
import subprocess
import sys
from pathlib import Path

ROOT     = Path(__file__).parent
FRONTEND = ROOT / "frontend"


def main():
    print("=" * 50)
    print(" ForensIQ — Production Launcher")
    print("=" * 50)

    # Step 1: build frontend
    print("\n[1/2] Building frontend (npm run build:prod)...")
    result = subprocess.run("npm run build:prod", cwd=str(FRONTEND), shell=True)
    if result.returncode != 0:
        print("\n[ERROR] Frontend build failed. Check the output above.")
        sys.exit(1)

    print("\n[2/2] Starting ForensIQ API server...")
    print("      Open http://localhost:8000 in your browser.\n")
    subprocess.run(
        [sys.executable, "run_api.py"],
        cwd=str(ROOT),
    )


if __name__ == "__main__":
    main()
