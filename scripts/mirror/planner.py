from typing import Any


def selected_tags(mode: str, tag_names: list[str]) -> list[str]:
    if mode == "all-tags":
        return sorted(tag_names)
    return sorted(tag for tag in tag_names if "alpine" in tag)


def build_publish_plan(
    policy: Any,
    upstream_tag_payload: dict,
    destination_tag_payload: dict,
    digest_by_tag: dict[str, str],
) -> list[dict[str, Any]]:
    upstream_names = [item["name"] for item in upstream_tag_payload["results"]]
    destination_names = {item["name"] for item in destination_tag_payload["results"]}
    wanted = [
        tag for tag in selected_tags(policy.mode, upstream_names) if tag not in destination_names
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
