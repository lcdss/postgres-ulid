import re
from typing import Any


MAJOR_FAMILY_TAG = re.compile(r"^(?P<major>\d+)-(?P<family>[a-z0-9-]+)$")


def selected_tags(
    tag_names: list[str],
    minimum_major: int,
    families: tuple[str, ...],
) -> list[str]:
    family_names = set(families)
    selected = []
    for tag in tag_names:
        if tag in family_names:
            selected.append(tag)
            continue
        match = MAJOR_FAMILY_TAG.fullmatch(tag)
        if not match:
            continue
        if match.group("family") not in family_names:
            continue
        if int(match.group("major")) < minimum_major:
            continue
        selected.append(tag)
    return sorted(selected)


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
        for tag in selected_tags(upstream_names, policy.minimum_major, policy.families)
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
