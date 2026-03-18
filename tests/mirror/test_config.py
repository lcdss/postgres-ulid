from pathlib import Path

import pytest

from scripts.mirror.config import load_policy


def test_load_policy_reads_major_families_mode(tmp_path: Path) -> None:
    policy_file = tmp_path / "mirror-policy.json"
    policy_file.write_text(
        '{"minimum_major": 13, "families": ["alpine", "trixie"]}',
        encoding="utf-8",
    )

    policy = load_policy(policy_file)

    assert policy.minimum_major == 13
    assert policy.families == ("alpine", "trixie")


def test_load_policy_rejects_missing_families(tmp_path: Path) -> None:
    policy_file = tmp_path / "mirror-policy.json"
    policy_file.write_text('{"minimum_major": 13}', encoding="utf-8")

    with pytest.raises(ValueError, match="families"):
        load_policy(policy_file)


def test_repository_policy_skips_unsupported_postgres_13() -> None:
    policy = load_policy(Path("mirror-policy.json"))

    assert policy.minimum_major == 14
