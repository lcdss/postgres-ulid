from hashlib import sha256
from pathlib import Path


DOCKERFILE_INPUTS = {
    "Dockerfile.alpine": (
        "Dockerfile.alpine",
        "scripts/build-pgx-ulid.sh",
        "scripts/find-pg-config.sh",
        "scripts/install-build-deps-alpine.sh",
        "scripts/stage-extension-artifacts.sh",
    ),
    "Dockerfile.debian": (
        "Dockerfile.debian",
        "scripts/build-pgx-ulid.sh",
        "scripts/find-pg-config.sh",
        "scripts/install-build-deps-debian.sh",
        "scripts/stage-extension-artifacts.sh",
    ),
}


def build_signature_for_dockerfile(dockerfile: str) -> str:
    try:
        inputs = DOCKERFILE_INPUTS[dockerfile]
    except KeyError as exc:
        raise ValueError(f"Unsupported dockerfile: {dockerfile}") from exc

    root = Path(__file__).resolve().parents[2]
    digest = sha256()
    for relative_path in inputs:
        digest.update(relative_path.encode("utf-8"))
        digest.update(b"\0")
        digest.update((root / relative_path).read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()
