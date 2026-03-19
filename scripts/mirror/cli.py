import argparse
import json
from pathlib import Path
from typing import Any

from scripts.mirror.config import load_policy
from scripts.mirror.docker_hub import fetch_tags
from scripts.mirror.planner import build_publish_plan, selected_tags
from scripts.mirror.registry import resolve_manifest_digest, resolve_source_digest


def matrix_payload(plan: list[dict[str, Any]]) -> str:
    return json.dumps({"include": plan}, sort_keys=True)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plan postgres-ulid mirror builds.")
    parser.add_argument(
        "--policy",
        type=Path,
        default=Path("mirror-policy.json"),
        help="Path to the mirror policy file.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path to write the matrix payload.",
    )
    parser.add_argument(
        "--source-namespace",
        default="library",
        help="Docker Hub namespace for the upstream repository.",
    )
    parser.add_argument(
        "--source-repository",
        default="postgres",
        help="Docker Hub repository name for the upstream repository.",
    )
    parser.add_argument(
        "--target-namespace",
        default="lcdss",
        help="Docker Hub namespace for the mirror repository.",
    )
    parser.add_argument(
        "--target-repository",
        default="postgres-ulid",
        help="Docker Hub repository name for the mirror repository.",
    )
    return parser.parse_args(argv)


def build_matrix(
    policy_path: Path,
    source_namespace: str,
    source_repository: str,
    target_namespace: str,
    target_repository: str,
) -> list[dict[str, Any]]:
    policy = load_policy(policy_path)
    upstream = fetch_tags(source_namespace, source_repository)
    destination = fetch_tags(target_namespace, target_repository)
    upstream_names = [item["name"] for item in upstream["results"]]
    selected = selected_tags(upstream_names, policy.minimum_major, policy.families)
    destination_names = {item["name"] for item in destination["results"]}

    digest_by_tag = {
        tag: resolve_manifest_digest(f"{source_namespace}/{source_repository}", tag)
        for tag in selected
    }
    destination_source_digest_by_tag = {
        tag: resolve_source_digest(f"{target_namespace}/{target_repository}", tag)
        for tag in selected
        if tag in destination_names
    }

    plan = build_publish_plan(
        policy=policy,
        upstream_tag_payload=upstream,
        destination_tag_payload=destination,
        digest_by_tag=digest_by_tag,
        destination_source_digest_by_tag=destination_source_digest_by_tag,
    )
    matrix = []
    for item in plan:
        matrix.append(
            {
                "digest": item["digest"],
                "base_image": (
                    f"docker.io/{source_namespace}/{source_repository}@{item['digest']}"
                ),
                "dockerfile": item["dockerfile"],
                "target_tags": item["target_tags"],
            }
        )
    return matrix


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    payload = matrix_payload(
        build_matrix(
            policy_path=args.policy,
            source_namespace=args.source_namespace,
            source_repository=args.source_repository,
            target_namespace=args.target_namespace,
            target_repository=args.target_repository,
        )
    )
    if args.output:
        args.output.write_text(payload, encoding="utf-8")
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
