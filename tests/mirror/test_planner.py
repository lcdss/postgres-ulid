import json
from pathlib import Path

from scripts.mirror.config import MirrorPolicy
from scripts.mirror.planner import build_publish_plan, selected_tags


def load_fixture(name: str) -> dict:
    fixture = Path("tests/fixtures/dockerhub") / name
    return json.loads(fixture.read_text(encoding="utf-8"))


def test_selected_tags_filters_major_families_and_floating_aliases() -> None:
    tags = [
        "12-alpine",
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
        minimum_major=13,
        families=("alpine", "trixie"),
    )

    assert selected == [
        "13-alpine",
        "13-trixie",
        "14-alpine",
        "14-trixie",
        "alpine",
        "trixie",
    ]


def test_build_publish_plan_filters_major_families_and_groups_by_digest() -> None:
    upstream = {
        "results": [
            {"name": "13-alpine"},
            {"name": "13-trixie"},
            {"name": "14-alpine"},
            {"name": "14-trixie"},
            {"name": "14.19-alpine3.21"},
            {"name": "alpine"},
            {"name": "trixie"},
        ]
    }
    destination = load_fixture("lcdss-postgres-ulid-tags.json")
    digest_by_tag = {
        "13-alpine": "sha256:aaa",
        "13-trixie": "sha256:ccc",
        "14-alpine": "sha256:aaa",
        "14-trixie": "sha256:ccc",
        "16-alpine": "sha256:bbb",
        "alpine": "sha256:ddd",
        "trixie": "sha256:eee",
    }

    plan = build_publish_plan(
        policy=MirrorPolicy(
            minimum_major=13,
            families=("alpine", "trixie"),
        ),
        upstream_tag_payload=upstream,
        destination_tag_payload=destination,
        digest_by_tag=digest_by_tag,
        destination_digest_by_tag={"16-alpine": "sha256:bbb"},
    )

    assert plan == [
        {
            "digest": "sha256:aaa",
            "base_image": "postgres@sha256:aaa",
            "source_tags": ["13-alpine", "14-alpine"],
            "target_tags": ["13-alpine", "14-alpine"],
        },
        {
            "digest": "sha256:ccc",
            "base_image": "postgres@sha256:ccc",
            "source_tags": ["13-trixie", "14-trixie"],
            "target_tags": ["13-trixie", "14-trixie"],
        },
        {
            "digest": "sha256:ddd",
            "base_image": "postgres@sha256:ddd",
            "source_tags": ["alpine"],
            "target_tags": ["alpine"],
        },
        {
            "digest": "sha256:eee",
            "base_image": "postgres@sha256:eee",
            "source_tags": ["trixie"],
            "target_tags": ["trixie"],
        }
    ]


def test_build_publish_plan_republishes_existing_tag_when_digest_changes() -> None:
    upstream = {
        "results": [
            {"name": "13-alpine"},
            {"name": "14-alpine"},
            {"name": "16-alpine"},
            {"name": "alpine"},
            {"name": "14.19-alpine3.21"},
        ]
    }
    destination = load_fixture("lcdss-postgres-ulid-tags.json")
    digest_by_tag = {
        "13-alpine": "sha256:aaa",
        "14-alpine": "sha256:aaa",
        "16-alpine": "sha256:bbb",
        "alpine": "sha256:ccc",
    }

    plan = build_publish_plan(
        policy=MirrorPolicy(
            minimum_major=13,
            families=("alpine",),
        ),
        upstream_tag_payload=upstream,
        destination_tag_payload=destination,
        digest_by_tag=digest_by_tag,
        destination_digest_by_tag={"16-alpine": "sha256:stale"},
    )

    assert plan == [
        {
            "digest": "sha256:aaa",
            "base_image": "postgres@sha256:aaa",
            "source_tags": ["13-alpine", "14-alpine"],
            "target_tags": ["13-alpine", "14-alpine"],
        },
        {
            "digest": "sha256:bbb",
            "base_image": "postgres@sha256:bbb",
            "source_tags": ["16-alpine"],
            "target_tags": ["16-alpine"],
        },
        {
            "digest": "sha256:ccc",
            "base_image": "postgres@sha256:ccc",
            "source_tags": ["alpine"],
            "target_tags": ["alpine"],
        },
    ]
