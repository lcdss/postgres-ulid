from pathlib import Path

import pytest

from scripts.mirror.config import load_policy


def test_load_policy_reads_major_alpine_mode(tmp_path: Path) -> None:
    policy_file = tmp_path / "mirror-policy.json"
    policy_file.write_text(
        '{"mode": "major-alpine", "minimum_major": 14}',
        encoding="utf-8",
    )

    policy = load_policy(policy_file)

    assert policy.mode == "major-alpine"
    assert policy.minimum_major == 14


def test_load_policy_rejects_unknown_mode(tmp_path: Path) -> None:
    policy_file = tmp_path / "mirror-policy.json"
    policy_file.write_text('{"mode": "unknown"}', encoding="utf-8")

    with pytest.raises(ValueError, match="Unsupported mirror mode"):
        load_policy(policy_file)
