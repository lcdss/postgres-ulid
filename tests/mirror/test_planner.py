import json
from pathlib import Path

from scripts.mirror.config import MirrorPolicy
from scripts.mirror.planner import build_publish_plan


def load_fixture(name: str) -> dict:
    fixture = Path("tests/fixtures/dockerhub") / name
    return json.loads(fixture.read_text(encoding="utf-8"))


def test_build_publish_plan_filters_major_alpine_and_groups_by_digest() -> None:
    upstream = load_fixture("library-postgres-tags.json")
    destination = load_fixture("lcdss-postgres-ulid-tags.json")
    digest_by_tag = {
        "14-alpine": "sha256:aaa",
        "17-alpine": "sha256:aaa",
        "16-alpine": "sha256:bbb",
    }

    plan = build_publish_plan(
        policy=MirrorPolicy(mode="major-alpine", minimum_major=14),
        upstream_tag_payload=upstream,
        destination_tag_payload=destination,
        digest_by_tag=digest_by_tag,
        destination_digest_by_tag={"16-alpine": "sha256:bbb"},
    )

    assert plan == [
        {
            "digest": "sha256:aaa",
            "base_image": "postgres@sha256:aaa",
            "source_tags": ["14-alpine", "17-alpine"],
            "target_tags": ["14-alpine", "17-alpine"],
        }
    ]


def test_build_publish_plan_republishes_existing_tag_when_digest_changes() -> None:
    upstream = load_fixture("library-postgres-tags.json")
    destination = load_fixture("lcdss-postgres-ulid-tags.json")
    digest_by_tag = {
        "14-alpine": "sha256:aaa",
        "17-alpine": "sha256:aaa",
        "16-alpine": "sha256:bbb",
    }

    plan = build_publish_plan(
        policy=MirrorPolicy(mode="major-alpine", minimum_major=14),
        upstream_tag_payload=upstream,
        destination_tag_payload=destination,
        digest_by_tag=digest_by_tag,
        destination_digest_by_tag={"16-alpine": "sha256:stale"},
    )

    assert plan == [
        {
            "digest": "sha256:aaa",
            "base_image": "postgres@sha256:aaa",
            "source_tags": ["14-alpine", "17-alpine"],
            "target_tags": ["14-alpine", "17-alpine"],
        },
        {
            "digest": "sha256:bbb",
            "base_image": "postgres@sha256:bbb",
            "source_tags": ["16-alpine"],
            "target_tags": ["16-alpine"],
        },
    ]
