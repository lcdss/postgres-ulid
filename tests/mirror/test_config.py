from pathlib import Path

import pytest

from scripts.mirror.config import load_policy


def test_load_policy_reads_alpine_only_mode(tmp_path: Path) -> None:
    policy_file = tmp_path / "mirror-policy.json"
    policy_file.write_text('{"mode": "alpine-only"}', encoding="utf-8")

    policy = load_policy(policy_file)

    assert policy.mode == "alpine-only"


def test_load_policy_rejects_unknown_mode(tmp_path: Path) -> None:
    policy_file = tmp_path / "mirror-policy.json"
    policy_file.write_text('{"mode": "unknown"}', encoding="utf-8")

    with pytest.raises(ValueError, match="Unsupported mirror mode"):
        load_policy(policy_file)
