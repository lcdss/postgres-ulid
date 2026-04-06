from pathlib import Path


def test_runtime_images_copy_init_hook() -> None:
    expected = (
        "COPY scripts/init-enable-pgx-ulid.sh "
        "/docker-entrypoint-initdb.d/10-enable-pgx-ulid.sh"
    )

    for dockerfile_name in ("Dockerfile.alpine", "Dockerfile.debian"):
        dockerfile = Path(dockerfile_name).read_text(encoding="utf-8")
        runtime_stage = dockerfile.split("FROM ${BASE_IMAGE}\n", maxsplit=1)[1]

        assert expected in runtime_stage
