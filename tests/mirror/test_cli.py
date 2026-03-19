import json
from pathlib import Path

from scripts.mirror.cli import main, matrix_payload


def test_matrix_payload_wraps_publish_plan_for_github_actions() -> None:
    plan = [
        {
            "digest": "sha256:aaa",
            "base_image": "postgres@sha256:aaa",
            "build_signature": "sig-alpine",
            "dockerfile": "Dockerfile.alpine",
            "job_name": "Dockerfile.alpine -> 17-alpine, 17.6-alpine3.22",
            "target_tags": ["17-alpine", "17.6-alpine3.22"],
        }
    ]

    payload = json.loads(matrix_payload(plan))

    assert payload == {
        "include": [
            {
                "digest": "sha256:aaa",
                "base_image": "postgres@sha256:aaa",
                "build_signature": "sig-alpine",
                "dockerfile": "Dockerfile.alpine",
                "job_name": "Dockerfile.alpine -> 17-alpine, 17.6-alpine3.22",
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
        '{"minimum_major": 13, "families": ["alpine", "trixie"]}',
        encoding="utf-8",
    )

    def fake_fetch_tags(namespace: str, repository: str) -> dict:
        if (namespace, repository) == ("library", "postgres"):
            return {
                "results": [
                    {"name": "12-alpine"},
                    {"name": "13-alpine"},
                    {"name": "13-trixie"},
                    {"name": "14-alpine"},
                    {"name": "14-trixie"},
                    {"name": "14.19-alpine3.21"},
                    {"name": "17.6-trixie"},
                    {"name": "alpine"},
                    {"name": "trixie"},
                    {"name": "latest"},
                ]
            }

        return {"results": [{"name": "13-trixie"}]}

    def fake_resolve_manifest_digest(image: str, tag: str) -> str:
        return {
            ("library/postgres", "13-alpine"): "sha256:aaa",
            ("library/postgres", "13-trixie"): "sha256:bbb",
            ("library/postgres", "14-alpine"): "sha256:aaa",
            ("library/postgres", "14-trixie"): "sha256:bbb",
            ("library/postgres", "alpine"): "sha256:ccc",
            ("library/postgres", "trixie"): "sha256:ddd",
        }[(image, tag)]

    def fake_resolve_source_digest(image: str, tag: str) -> str | None:
        return {
            ("lcdss/postgres-ulid", "13-trixie"): "sha256:bbb",
        }.get((image, tag))

    def fake_resolve_config_label(image: str, tag: str, label: str) -> str | None:
        return {
            ("lcdss/postgres-ulid", "13-trixie", "io.github.lcdss.postgres-ulid.build-signature"): "sig-debian",
        }.get((image, tag, label))

    def fake_build_signature_for_dockerfile(dockerfile: str) -> str:
        return {
            "Dockerfile.alpine": "sig-alpine",
            "Dockerfile.debian": "sig-debian",
        }[dockerfile]

    monkeypatch.setattr("scripts.mirror.cli.fetch_tags", fake_fetch_tags)
    monkeypatch.setattr(
        "scripts.mirror.cli.resolve_manifest_digest", fake_resolve_manifest_digest
    )
    monkeypatch.setattr(
        "scripts.mirror.cli.resolve_source_digest", fake_resolve_source_digest
    )
    monkeypatch.setattr(
        "scripts.mirror.cli.resolve_config_label",
        fake_resolve_config_label,
    )
    monkeypatch.setattr(
        "scripts.mirror.cli.build_signature_for_dockerfile",
        fake_build_signature_for_dockerfile,
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
                "build_signature": "sig-alpine",
                "dockerfile": "Dockerfile.alpine",
                "job_name": "Dockerfile.alpine -> 13-alpine, 14-alpine",
                "target_tags": ["13-alpine", "14-alpine"],
            },
            {
                "digest": "sha256:bbb",
                "base_image": "docker.io/library/postgres@sha256:bbb",
                "build_signature": "sig-debian",
                "dockerfile": "Dockerfile.debian",
                "job_name": "Dockerfile.debian -> 14-trixie",
                "target_tags": ["14-trixie"],
            },
            {
                "digest": "sha256:ccc",
                "base_image": "docker.io/library/postgres@sha256:ccc",
                "build_signature": "sig-alpine",
                "dockerfile": "Dockerfile.alpine",
                "job_name": "Dockerfile.alpine -> alpine",
                "target_tags": ["alpine"],
            },
            {
                "digest": "sha256:ddd",
                "base_image": "docker.io/library/postgres@sha256:ddd",
                "build_signature": "sig-debian",
                "dockerfile": "Dockerfile.debian",
                "job_name": "Dockerfile.debian -> trixie",
                "target_tags": ["trixie"],
            }
        ]
    }


def test_main_republishes_existing_tag_when_target_source_digest_drifted(
    monkeypatch, tmp_path: Path
) -> None:
    policy_file = tmp_path / "mirror-policy.json"
    output_file = tmp_path / "matrix.json"
    policy_file.write_text(
        '{"minimum_major": 13, "families": ["alpine", "trixie"]}',
        encoding="utf-8",
    )

    def fake_fetch_tags(namespace: str, repository: str) -> dict:
        if (namespace, repository) == ("library", "postgres"):
            return {
                "results": [
                    {"name": "13-alpine"},
                    {"name": "16-alpine"},
                    {"name": "13-trixie"},
                    {"name": "alpine"},
                    {"name": "trixie"},
                ]
            }

        return {"results": [{"name": "16-alpine"}, {"name": "alpine"}]}

    def fake_resolve_manifest_digest(image: str, tag: str) -> str:
        return {
            ("library/postgres", "13-alpine"): "sha256:aaa",
            ("library/postgres", "16-alpine"): "sha256:bbb",
            ("library/postgres", "13-trixie"): "sha256:ccc",
            ("library/postgres", "alpine"): "sha256:ddd",
            ("library/postgres", "trixie"): "sha256:eee",
        }[(image, tag)]

    def fake_resolve_source_digest(image: str, tag: str) -> str | None:
        return {
            ("lcdss/postgres-ulid", "16-alpine"): "sha256:stale",
            ("lcdss/postgres-ulid", "alpine"): "sha256:stale-alpine",
        }.get((image, tag))

    def fake_resolve_config_label(image: str, tag: str, label: str) -> str | None:
        return {
            ("lcdss/postgres-ulid", "16-alpine", "io.github.lcdss.postgres-ulid.build-signature"): "sig-alpine",
            ("lcdss/postgres-ulid", "alpine", "io.github.lcdss.postgres-ulid.build-signature"): "sig-alpine",
        }.get((image, tag, label))

    def fake_build_signature_for_dockerfile(dockerfile: str) -> str:
        return {
            "Dockerfile.alpine": "sig-alpine",
            "Dockerfile.debian": "sig-debian",
        }[dockerfile]

    monkeypatch.setattr("scripts.mirror.cli.fetch_tags", fake_fetch_tags)
    monkeypatch.setattr(
        "scripts.mirror.cli.resolve_manifest_digest", fake_resolve_manifest_digest
    )
    monkeypatch.setattr(
        "scripts.mirror.cli.resolve_source_digest", fake_resolve_source_digest
    )
    monkeypatch.setattr(
        "scripts.mirror.cli.resolve_config_label",
        fake_resolve_config_label,
    )
    monkeypatch.setattr(
        "scripts.mirror.cli.build_signature_for_dockerfile",
        fake_build_signature_for_dockerfile,
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
                "build_signature": "sig-alpine",
                "dockerfile": "Dockerfile.alpine",
                "job_name": "Dockerfile.alpine -> 13-alpine",
                "target_tags": ["13-alpine"],
            },
            {
                "digest": "sha256:bbb",
                "base_image": "docker.io/library/postgres@sha256:bbb",
                "build_signature": "sig-alpine",
                "dockerfile": "Dockerfile.alpine",
                "job_name": "Dockerfile.alpine -> 16-alpine",
                "target_tags": ["16-alpine"],
            },
            {
                "digest": "sha256:ccc",
                "base_image": "docker.io/library/postgres@sha256:ccc",
                "build_signature": "sig-debian",
                "dockerfile": "Dockerfile.debian",
                "job_name": "Dockerfile.debian -> 13-trixie",
                "target_tags": ["13-trixie"],
            },
            {
                "digest": "sha256:ddd",
                "base_image": "docker.io/library/postgres@sha256:ddd",
                "build_signature": "sig-alpine",
                "dockerfile": "Dockerfile.alpine",
                "job_name": "Dockerfile.alpine -> alpine",
                "target_tags": ["alpine"],
            },
            {
                "digest": "sha256:eee",
                "base_image": "docker.io/library/postgres@sha256:eee",
                "build_signature": "sig-debian",
                "dockerfile": "Dockerfile.debian",
                "job_name": "Dockerfile.debian -> trixie",
                "target_tags": ["trixie"],
            },
        ]
    }


def test_main_skips_existing_tag_when_target_source_digest_matches(
    monkeypatch, tmp_path: Path
) -> None:
    policy_file = tmp_path / "mirror-policy.json"
    output_file = tmp_path / "matrix.json"
    policy_file.write_text(
        '{"minimum_major": 13, "families": ["alpine"]}',
        encoding="utf-8",
    )

    def fake_fetch_tags(namespace: str, repository: str) -> dict:
        if (namespace, repository) == ("library", "postgres"):
            return {
                "results": [
                    {"name": "13-alpine"},
                    {"name": "16-alpine"},
                    {"name": "alpine"},
                ]
            }

        return {"results": [{"name": "16-alpine"}, {"name": "alpine"}]}

    def fake_resolve_manifest_digest(image: str, tag: str) -> str:
        return {
            ("library/postgres", "13-alpine"): "sha256:aaa",
            ("library/postgres", "16-alpine"): "sha256:bbb",
            ("library/postgres", "alpine"): "sha256:ccc",
        }[(image, tag)]

    def fake_resolve_source_digest(image: str, tag: str) -> str | None:
        return {
            ("lcdss/postgres-ulid", "16-alpine"): "sha256:bbb",
            ("lcdss/postgres-ulid", "alpine"): "sha256:ccc",
        }.get((image, tag))

    def fake_resolve_config_label(image: str, tag: str, label: str) -> str | None:
        return {
            ("lcdss/postgres-ulid", "16-alpine", "io.github.lcdss.postgres-ulid.build-signature"): "sig-alpine",
            ("lcdss/postgres-ulid", "alpine", "io.github.lcdss.postgres-ulid.build-signature"): "sig-alpine",
        }.get((image, tag, label))

    def fake_build_signature_for_dockerfile(dockerfile: str) -> str:
        assert dockerfile == "Dockerfile.alpine"
        return "sig-alpine"

    monkeypatch.setattr("scripts.mirror.cli.fetch_tags", fake_fetch_tags)
    monkeypatch.setattr(
        "scripts.mirror.cli.resolve_manifest_digest", fake_resolve_manifest_digest
    )
    monkeypatch.setattr(
        "scripts.mirror.cli.resolve_source_digest", fake_resolve_source_digest
    )
    monkeypatch.setattr(
        "scripts.mirror.cli.resolve_config_label",
        fake_resolve_config_label,
    )
    monkeypatch.setattr(
        "scripts.mirror.cli.build_signature_for_dockerfile",
        fake_build_signature_for_dockerfile,
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
                "build_signature": "sig-alpine",
                "dockerfile": "Dockerfile.alpine",
                "job_name": "Dockerfile.alpine -> 13-alpine",
                "target_tags": ["13-alpine"],
            }
        ]
    }


def test_main_republishes_existing_tag_when_target_build_signature_drifted(
    monkeypatch, tmp_path: Path
) -> None:
    policy_file = tmp_path / "mirror-policy.json"
    output_file = tmp_path / "matrix.json"
    policy_file.write_text(
        '{"minimum_major": 13, "families": ["alpine"]}',
        encoding="utf-8",
    )

    def fake_fetch_tags(namespace: str, repository: str) -> dict:
        if (namespace, repository) == ("library", "postgres"):
            return {
                "results": [
                    {"name": "16-alpine"},
                ]
            }

        return {"results": [{"name": "16-alpine"}]}

    def fake_resolve_manifest_digest(image: str, tag: str) -> str:
        return {
            ("library/postgres", "16-alpine"): "sha256:bbb",
        }[(image, tag)]

    def fake_resolve_source_digest(image: str, tag: str) -> str | None:
        return {
            ("lcdss/postgres-ulid", "16-alpine"): "sha256:bbb",
        }.get((image, tag))

    def fake_resolve_config_label(image: str, tag: str, label: str) -> str | None:
        return {
            ("lcdss/postgres-ulid", "16-alpine", "io.github.lcdss.postgres-ulid.build-signature"): "sig-stale",
        }.get((image, tag, label))

    def fake_build_signature_for_dockerfile(dockerfile: str) -> str:
        assert dockerfile == "Dockerfile.alpine"
        return "sig-current"

    monkeypatch.setattr("scripts.mirror.cli.fetch_tags", fake_fetch_tags)
    monkeypatch.setattr(
        "scripts.mirror.cli.resolve_manifest_digest", fake_resolve_manifest_digest
    )
    monkeypatch.setattr(
        "scripts.mirror.cli.resolve_source_digest", fake_resolve_source_digest
    )
    monkeypatch.setattr(
        "scripts.mirror.cli.resolve_config_label",
        fake_resolve_config_label,
        raising=False,
    )
    monkeypatch.setattr(
        "scripts.mirror.cli.build_signature_for_dockerfile",
        fake_build_signature_for_dockerfile,
        raising=False,
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
                "digest": "sha256:bbb",
                "base_image": "docker.io/library/postgres@sha256:bbb",
                "build_signature": "sig-current",
                "dockerfile": "Dockerfile.alpine",
                "job_name": "Dockerfile.alpine -> 16-alpine",
                "target_tags": ["16-alpine"],
            }
        ]
    }
