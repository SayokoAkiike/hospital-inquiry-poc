import subprocess
import sys


def run_migrations():
    try:
        subprocess.run(
            ["alembic", "upgrade", "head"],
            check=True,
            capture_output=True,
            text=True,
        )
        print("Migrations completed successfully")
    except subprocess.CalledProcessError as e:
        print(f"Migration failed: {e.stderr}")
        sys.exit(1)
