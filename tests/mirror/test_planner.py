import json
from pathlib import Path

from scripts.mirror.config import MirrorPolicy
from scripts.mirror.planner import build_publish_plan, selected_tags


def load_fixture(name: str) -> dict:
    fixture = Path("tests/fixtures/dockerhub") / name
    return json.loads(fixture.read_text(encoding="utf-8"))


def test_selected_tags_filters_major_families_and_floating_aliases() -> None:
    tags = [
        "13-alpine",
        "13-trixie",
        "14-alpine",
        "14-trixie",
        "14.19-alpine3.21",
        "17.6-trixie",
        "alpine",
        "trixie",
        "latest",
    ]

    selected = selected_tags(
        tag_names=tags,
        minimum_major=14,
        families=("alpine", "trixie"),
    )

    assert selected == [
        "14-alpine",
        "14-trixie",
        "alpine",
        "trixie",
    ]


def test_build_publish_plan_filters_major_families_and_groups_by_digest() -> None:
    upstream = {
        "results": [
            {"name": "14-alpine"},
            {"name": "14-trixie"},
            {"name": "15-alpine"},
            {"name": "15-trixie"},
            {"name": "14.19-alpine3.21"},
            {"name": "alpine"},
            {"name": "trixie"},
        ]
    }
    destination = load_fixture("lcdss-postgres-ulid-tags.json")
    digest_by_tag = {
        "14-alpine": "sha256:aaa",
        "14-trixie": "sha256:ccc",
        "15-alpine": "sha256:aaa",
        "15-trixie": "sha256:ccc",
        "16-alpine": "sha256:bbb",
        "alpine": "sha256:ddd",
        "trixie": "sha256:eee",
    }

    plan = build_publish_plan(
        policy=MirrorPolicy(
            minimum_major=14,
            families=("alpine", "trixie"),
        ),
        upstream_tag_payload=upstream,
        destination_tag_payload=destination,
        digest_by_tag=digest_by_tag,
        destination_source_digest_by_tag={"16-alpine": "sha256:bbb"},
        build_signature_by_tag={
            "14-alpine": "sig-alpine",
            "14-trixie": "sig-debian",
            "15-alpine": "sig-alpine",
            "15-trixie": "sig-debian",
            "alpine": "sig-alpine",
            "trixie": "sig-debian",
        },
        destination_build_signature_by_tag={
            "16-alpine": "sig-alpine",
        },
    )

    assert plan == [
        {
            "digest": "sha256:aaa",
            "base_image": "postgres@sha256:aaa",
            "build_signature": "sig-alpine",
            "dockerfile": "Dockerfile.alpine",
            "source_tags": ["14-alpine", "15-alpine"],
            "target_tags": ["14-alpine", "15-alpine"],
        },
        {
            "digest": "sha256:ccc",
            "base_image": "postgres@sha256:ccc",
            "build_signature": "sig-debian",
            "dockerfile": "Dockerfile.debian",
            "source_tags": ["14-trixie", "15-trixie"],
            "target_tags": ["14-trixie", "15-trixie"],
        },
        {
            "digest": "sha256:ddd",
            "base_image": "postgres@sha256:ddd",
            "build_signature": "sig-alpine",
            "dockerfile": "Dockerfile.alpine",
            "source_tags": ["alpine"],
            "target_tags": ["alpine"],
        },
        {
            "digest": "sha256:eee",
            "base_image": "postgres@sha256:eee",
            "build_signature": "sig-debian",
            "dockerfile": "Dockerfile.debian",
            "source_tags": ["trixie"],
            "target_tags": ["trixie"],
        }
    ]


def test_build_publish_plan_republishes_existing_tag_when_digest_changes() -> None:
    upstream = {
        "results": [
            {"name": "14-alpine"},
            {"name": "15-alpine"},
            {"name": "16-alpine"},
            {"name": "alpine"},
            {"name": "14.19-alpine3.21"},
        ]
    }
    destination = load_fixture("lcdss-postgres-ulid-tags.json")
    digest_by_tag = {
        "14-alpine": "sha256:aaa",
        "15-alpine": "sha256:aaa",
        "16-alpine": "sha256:bbb",
        "alpine": "sha256:ccc",
    }

    plan = build_publish_plan(
        policy=MirrorPolicy(
            minimum_major=14,
            families=("alpine",),
        ),
        upstream_tag_payload=upstream,
        destination_tag_payload=destination,
        digest_by_tag=digest_by_tag,
        destination_source_digest_by_tag={"16-alpine": "sha256:stale"},
        build_signature_by_tag={
            "14-alpine": "sig-alpine",
            "15-alpine": "sig-alpine",
            "16-alpine": "sig-alpine",
            "alpine": "sig-alpine",
        },
        destination_build_signature_by_tag={
            "16-alpine": "sig-alpine",
        },
    )

    assert plan == [
        {
            "digest": "sha256:aaa",
            "base_image": "postgres@sha256:aaa",
            "build_signature": "sig-alpine",
            "dockerfile": "Dockerfile.alpine",
            "source_tags": ["14-alpine", "15-alpine"],
            "target_tags": ["14-alpine", "15-alpine"],
        },
        {
            "digest": "sha256:bbb",
            "base_image": "postgres@sha256:bbb",
            "build_signature": "sig-alpine",
            "dockerfile": "Dockerfile.alpine",
            "source_tags": ["16-alpine"],
            "target_tags": ["16-alpine"],
        },
        {
            "digest": "sha256:ccc",
            "base_image": "postgres@sha256:ccc",
            "build_signature": "sig-alpine",
            "dockerfile": "Dockerfile.alpine",
            "source_tags": ["alpine"],
            "target_tags": ["alpine"],
        },
    ]


def test_build_publish_plan_skips_unsupported_tag_when_major_is_below_policy_floor() -> None:
    upstream = {
        "results": [
            {"name": "13-alpine"},
            {"name": "16-alpine"},
            {"name": "alpine"},
        ]
    }
    destination = {
        "results": [
            {"name": "16-alpine"},
            {"name": "alpine"},
        ]
    }
    digest_by_tag = {
        "13-alpine": "sha256:aaa",
        "16-alpine": "sha256:bbb",
        "alpine": "sha256:ccc",
    }

    plan = build_publish_plan(
        policy=MirrorPolicy(
            minimum_major=14,
            families=("alpine",),
        ),
        upstream_tag_payload=upstream,
        destination_tag_payload=destination,
        digest_by_tag=digest_by_tag,
        destination_source_digest_by_tag={
            "16-alpine": "sha256:bbb",
            "alpine": "sha256:ccc",
        },
        build_signature_by_tag={
            "13-alpine": "sig-alpine",
            "16-alpine": "sig-alpine",
            "alpine": "sig-alpine",
        },
        destination_build_signature_by_tag={
            "16-alpine": "sig-alpine",
            "alpine": "sig-alpine",
        },
    )

    assert plan == []


def test_build_publish_plan_republishes_existing_tag_when_build_signature_changes() -> None:
    upstream = {
        "results": [
            {"name": "16-alpine"},
        ]
    }
    destination = {
        "results": [
            {"name": "16-alpine"},
        ]
    }
    digest_by_tag = {
        "16-alpine": "sha256:bbb",
    }

    plan = build_publish_plan(
        policy=MirrorPolicy(
            minimum_major=14,
            families=("alpine",),
        ),
        upstream_tag_payload=upstream,
        destination_tag_payload=destination,
        digest_by_tag=digest_by_tag,
        destination_source_digest_by_tag={
            "16-alpine": "sha256:bbb",
        },
        build_signature_by_tag={
            "16-alpine": "sig-current",
        },
        destination_build_signature_by_tag={
            "16-alpine": "sig-stale",
        },
    )

    assert plan == [
        {
            "digest": "sha256:bbb",
            "base_image": "postgres@sha256:bbb",
            "build_signature": "sig-current",
            "dockerfile": "Dockerfile.alpine",
            "source_tags": ["16-alpine"],
            "target_tags": ["16-alpine"],
        }
    ]
