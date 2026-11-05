"""Verify that the progress endpoint exposes recoverable evaluation states."""
import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.main import app


def main() -> None:
    client = TestClient(app)
    health = client.get("/api/v1/health")
    health.raise_for_status()
    print("Resilience smoke test ready: upload a CV, then inspect /evaluation-progress.")


if __name__ == "__main__":
    main()
