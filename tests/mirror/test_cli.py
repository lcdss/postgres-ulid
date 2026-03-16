import json
from pathlib import Path

from scripts.mirror.cli import main, matrix_payload


def test_matrix_payload_wraps_publish_plan_for_github_actions() -> None:
    plan = [
        {
            "digest": "sha256:aaa",
            "base_image": "postgres@sha256:aaa",
            "target_tags": ["17-alpine", "17.6-alpine3.22"],
        }
    ]

    payload = json.loads(matrix_payload(plan))

    assert payload == {
        "include": [
            {
                "digest": "sha256:aaa",
                "base_image": "postgres@sha256:aaa",
                "target_tags": ["17-alpine", "17.6-alpine3.22"],
            }
        ]
    }


def test_matrix_payload_returns_empty_include_when_nothing_is_missing() -> None:
    payload = json.loads(matrix_payload([]))
    assert payload == {"include": []}


def test_main_writes_matrix_json_from_discovered_tags(
    monkeypatch, tmp_path: Path
) -> None:
    policy_file = tmp_path / "mirror-policy.json"
    output_file = tmp_path / "matrix.json"
    policy_file.write_text(
        '{"mode": "major-alpine", "minimum_major": 14}',
        encoding="utf-8",
    )

    def fake_fetch_tags(namespace: str, repository: str) -> dict:
        if (namespace, repository) == ("library", "postgres"):
            return {
                "results": [
                    {"name": "13-alpine"},
                    {"name": "14-alpine"},
                    {"name": "14.19-alpine3.21"},
                    {"name": "17-alpine"},
                    {"name": "16-alpine"},
                    {"name": "latest"},
                ]
            }

        return {"results": [{"name": "16-alpine"}]}

    def fake_resolve_manifest_digest(image: str, tag: str) -> str:
        return {
            "14-alpine": "sha256:aaa",
            "17-alpine": "sha256:aaa",
            "16-alpine": "sha256:bbb",
        }[tag]

    monkeypatch.setattr("scripts.mirror.cli.fetch_tags", fake_fetch_tags)
    monkeypatch.setattr(
        "scripts.mirror.cli.resolve_manifest_digest", fake_resolve_manifest_digest
    )

    exit_code = main(
        [
            "--policy",
            str(policy_file),
            "--output",
            str(output_file),
        ]
    )

    assert exit_code == 0
    assert json.loads(output_file.read_text(encoding="utf-8")) == {
        "include": [
            {
                "digest": "sha256:aaa",
                "base_image": "docker.io/library/postgres@sha256:aaa",
                "target_tags": ["14-alpine", "17-alpine"],
            }
        ]
    }


def test_main_republishes_existing_tag_when_target_digest_drifted(
    monkeypatch, tmp_path: Path
) -> None:
    policy_file = tmp_path / "mirror-policy.json"
    output_file = tmp_path / "matrix.json"
    policy_file.write_text(
        '{"mode": "major-alpine", "minimum_major": 14}',
        encoding="utf-8",
    )

    def fake_fetch_tags(namespace: str, repository: str) -> dict:
        if (namespace, repository) == ("library", "postgres"):
            return {
                "results": [
                    {"name": "14-alpine"},
                    {"name": "16-alpine"},
                    {"name": "17-alpine"},
                ]
            }

        return {"results": [{"name": "16-alpine"}]}

    def fake_resolve_manifest_digest(image: str, tag: str) -> str:
        return {
            ("library/postgres", "14-alpine"): "sha256:aaa",
            ("library/postgres", "16-alpine"): "sha256:bbb",
            ("library/postgres", "17-alpine"): "sha256:aaa",
            ("lcdss/postgres-ulid", "16-alpine"): "sha256:stale",
        }[(image, tag)]

    monkeypatch.setattr("scripts.mirror.cli.fetch_tags", fake_fetch_tags)
    monkeypatch.setattr(
        "scripts.mirror.cli.resolve_manifest_digest", fake_resolve_manifest_digest
    )

    exit_code = main(
        [
            "--policy",
            str(policy_file),
            "--output",
            str(output_file),
        ]
    )

    assert exit_code == 0
    assert json.loads(output_file.read_text(encoding="utf-8")) == {
        "include": [
            {
                "digest": "sha256:aaa",
                "base_image": "docker.io/library/postgres@sha256:aaa",
                "target_tags": ["14-alpine", "17-alpine"],
            },
            {
                "digest": "sha256:bbb",
                "base_image": "docker.io/library/postgres@sha256:bbb",
                "target_tags": ["16-alpine"],
            },
        ]
    }
