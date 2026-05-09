from __future__ import annotations

import sys
from types import SimpleNamespace

from job_intel.core.resume import load_resume_text


def test_load_resume_text_reads_utf8_txt(tmp_path) -> None:
    resume_path = tmp_path / "resume.txt"
    resume_path.write_text("Python backend engineer\nAirflow Docker SQL", encoding="utf-8")

    assert load_resume_text(resume_path) == "Python backend engineer\nAirflow Docker SQL"


def test_load_resume_text_extracts_pdf_pages(monkeypatch, tmp_path) -> None:
    resume_path = tmp_path / "resume.pdf"
    resume_path.write_bytes(b"%PDF fake")

    class FakeReader:
        def __init__(self, path: str) -> None:
            self.path = path
            self.pages = [
                SimpleNamespace(extract_text=lambda: "Python backend engineer"),
                SimpleNamespace(extract_text=lambda: None),
                SimpleNamespace(extract_text=lambda: "Airflow Docker SQL"),
            ]

    monkeypatch.setitem(sys.modules, "pypdf", SimpleNamespace(PdfReader=FakeReader))

    assert load_resume_text(resume_path) == "Python backend engineer\n\nAirflow Docker SQL"


def test_load_resume_text_requires_pypdf_for_pdf(monkeypatch, tmp_path) -> None:
    resume_path = tmp_path / "resume.pdf"
    resume_path.write_bytes(b"%PDF fake")
    monkeypatch.setitem(sys.modules, "pypdf", None)

    try:
        load_resume_text(resume_path)
    except RuntimeError as exc:
        assert "Reading PDF resumes requires pypdf" in str(exc)
    else:
        raise AssertionError("Expected RuntimeError when pypdf is unavailable.")
