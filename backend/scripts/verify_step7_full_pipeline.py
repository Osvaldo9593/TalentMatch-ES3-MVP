#!/usr/bin/env python3
"""Smoke test for the DOCX upload and asynchronous batch endpoint."""
import io
import sys
from pathlib import Path

from docx import Document
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.main import app


def build_docx() -> bytes:
    document = Document()
    document.add_paragraph("Candidato de verificación")
    document.add_paragraph("Ingeniero Python con experiencia en FastAPI")
    output = io.BytesIO()
    document.save(output)
    return output.getvalue()


def main() -> None:
    client = TestClient(app)
    health = client.get("/api/v1/health")
    health.raise_for_status()
    offer = client.post(
        "/api/v1/job-offers/",
        json={
            "title": "Oferta de verificación DOCX",
            "description": "Smoke test del pipeline.",
            "required_skills": ["Python"],
            "status": "active",
        },
    )
    offer.raise_for_status()
    offer_id = offer.json()["id"]
    upload = client.post(
        f"/api/v1/job-offers/{offer_id}/cvs/",
        files={
            "file": (
                "verification.docx",
                build_docx(),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
    )
    upload.raise_for_status()
    assert upload.json()["processing_status"] == "processed"
    batch = client.post(f"/api/v1/job-offers/{offer_id}/evaluate")
    assert batch.status_code == 202, batch.text
    print("DOCX upload, extraction and asynchronous batch scheduling verified.")


if __name__ == "__main__":
    main()
