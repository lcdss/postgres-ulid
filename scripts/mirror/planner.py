import re
from typing import Any


MAJOR_ALPINE_TAG = re.compile(r"^(?P<major>\d+)-alpine$")


def selected_tags(
    mode: str, tag_names: list[str], minimum_major: int | None = None
) -> list[str]:
    if mode == "all-tags":
        return sorted(tag_names)
    if mode == "major-alpine":
        if minimum_major is None:
            raise ValueError("major-alpine selection requires minimum_major")
        return sorted(
            tag
            for tag in tag_names
            if (match := MAJOR_ALPINE_TAG.fullmatch(tag))
            and int(match.group("major")) >= minimum_major
        )
    raise ValueError(f"Unsupported mirror mode: {mode}")


def build_publish_plan(
    policy: Any,
    upstream_tag_payload: dict,
    destination_tag_payload: dict,
    digest_by_tag: dict[str, str],
    destination_digest_by_tag: dict[str, str],
) -> list[dict[str, Any]]:
    upstream_names = [item["name"] for item in upstream_tag_payload["results"]]
    destination_names = {item["name"] for item in destination_tag_payload["results"]}
    wanted = [
        tag
        for tag in selected_tags(policy.mode, upstream_names, policy.minimum_major)
        if tag not in destination_names
        or destination_digest_by_tag[tag] != digest_by_tag[tag]
    ]

    grouped: dict[str, list[str]] = {}
    for tag in wanted:
        digest = digest_by_tag[tag]
        grouped.setdefault(digest, []).append(tag)

    plan = []
    for digest, tags in sorted(grouped.items()):
        plan.append(
            {
                "digest": digest,
                "base_image": f"postgres@{digest}",
                "source_tags": tags,
                "target_tags": tags,
            }
        )
    return plan
