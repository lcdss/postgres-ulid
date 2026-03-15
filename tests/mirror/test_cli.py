import json

from scripts.mirror.cli import matrix_payload


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
