import json
from pathlib import Path

from scripts.mirror.config import MirrorPolicy
from scripts.mirror.planner import build_publish_plan


def load_fixture(name: str) -> dict:
    fixture = Path("tests/fixtures/dockerhub") / name
    return json.loads(fixture.read_text(encoding="utf-8"))


def test_build_publish_plan_filters_alpine_and_groups_by_digest() -> None:
    upstream = load_fixture("library-postgres-tags.json")
    destination = load_fixture("lcdss-postgres-ulid-tags.json")
    digest_by_tag = {
        "17-alpine": "sha256:aaa",
        "17.6-alpine3.22": "sha256:aaa",
        "16-alpine": "sha256:bbb",
        "latest": "sha256:ccc",
    }

    plan = build_publish_plan(
        policy=MirrorPolicy(mode="alpine-only"),
        upstream_tag_payload=upstream,
        destination_tag_payload=destination,
        digest_by_tag=digest_by_tag,
    )

    assert plan == [
        {
            "digest": "sha256:aaa",
            "base_image": "postgres@sha256:aaa",
            "source_tags": ["17-alpine", "17.6-alpine3.22"],
            "target_tags": ["17-alpine", "17.6-alpine3.22"],
        }
    ]
