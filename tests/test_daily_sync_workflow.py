from pathlib import Path


def test_publish_job_uses_matrix_job_name() -> None:
    workflow = Path(".github/workflows/daily-sync.yml").read_text(encoding="utf-8")

    assert "name: Publish ${{ matrix.job_name }}" in workflow
