import json
from urllib.parse import parse_qs, urlparse
from urllib.parse import urlencode
from urllib.request import Request, urlopen


MANIFEST_ACCEPT = ", ".join(
    [
        "application/vnd.docker.distribution.manifest.list.v2+json",
        "application/vnd.oci.image.index.v1+json",
        "application/vnd.docker.distribution.manifest.v2+json",
        "application/vnd.oci.image.manifest.v1+json",
    ]
)
SOURCE_DIGEST_LABEL = "io.github.lcdss.postgres-ulid.source-digest"


def fetch_registry_token(image: str) -> str:
    query = urlencode(
        {
            "service": "registry.docker.io",
            "scope": f"repository:{image}:pull",
        }
    )
    request = Request(
        f"https://auth.docker.io/token?{query}",
        headers={"Accept": "application/json"},
    )
    with urlopen(request) as response:
        payload = json.load(response)
    return payload["token"]


def resolve_manifest_digest(image: str, tag: str) -> str:
    token = fetch_registry_token(image)
    request = Request(
        f"https://registry-1.docker.io/v2/{image}/manifests/{tag}",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": MANIFEST_ACCEPT,
        },
        method="HEAD",
    )
    with urlopen(request) as response:
        digest = response.headers["Docker-Content-Digest"]
    return digest


def _fetch_manifest_payload(image: str, reference: str, token: str) -> dict:
    request = Request(
        f"https://registry-1.docker.io/v2/{image}/manifests/{reference}",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": MANIFEST_ACCEPT,
        },
    )
    with urlopen(request) as response:
        return json.load(response)


def _fetch_blob_payload(image: str, digest: str, token: str) -> dict:
    request = Request(
        f"https://registry-1.docker.io/v2/{image}/blobs/{digest}",
        headers={"Authorization": f"Bearer {token}"},
    )
    with urlopen(request) as response:
        return json.load(response)


def _select_image_manifest(image: str, manifest_payload: dict, token: str) -> dict | None:
    if "config" in manifest_payload:
        return manifest_payload

    for descriptor in manifest_payload.get("manifests", []):
        annotations = descriptor.get("annotations", {})
        platform = descriptor.get("platform", {})
        if annotations.get("vnd.docker.reference.type") == "attestation-manifest":
            continue
        if platform.get("architecture") == "unknown":
            continue
        if platform.get("os") == "unknown":
            continue
        return _fetch_manifest_payload(image, descriptor["digest"], token)
    return None


def _extract_source_digest_from_base_image_ref(base_image: str | None) -> str | None:
    if base_image is None or "@sha256:" not in base_image:
        return None
    return "sha256:" + base_image.rsplit("@sha256:", 1)[1]


def _extract_source_digest_from_attestation_payload(payload: dict) -> str | None:
    request_args = (
        payload.get("predicate", {})
        .get("buildDefinition", {})
        .get("externalParameters", {})
        .get("request", {})
        .get("args", {})
    )
    source_digest = _extract_source_digest_from_base_image_ref(
        request_args.get("build-arg:BASE_IMAGE")
    )
    if source_digest is not None:
        return source_digest

    dependencies = (
        payload.get("predicate", {})
        .get("buildDefinition", {})
        .get("resolvedDependencies", [])
    )
    for dependency in dependencies:
        uri = dependency.get("uri")
        if uri is None:
            continue
        digest = parse_qs(urlparse(uri).query).get("digest")
        if digest:
            return digest[0]
    return None


def _resolve_config_label_from_manifest(
    image: str,
    manifest_payload: dict,
    token: str,
    label: str,
) -> str | None:
    image_manifest = _select_image_manifest(image, manifest_payload, token)
    if image_manifest is None:
        return None

    config_digest = image_manifest.get("config", {}).get("digest")
    if config_digest is None:
        return None

    config_payload = _fetch_blob_payload(image, config_digest, token)
    return config_payload.get("config", {}).get("Labels", {}).get(label)


def resolve_config_label(image: str, tag: str, label: str) -> str | None:
    token = fetch_registry_token(image)
    manifest_payload = _fetch_manifest_payload(image, tag, token)
    return _resolve_config_label_from_manifest(image, manifest_payload, token, label)


def resolve_source_digest(image: str, tag: str) -> str | None:
    token = fetch_registry_token(image)
    manifest_payload = _fetch_manifest_payload(image, tag, token)

    source_digest = _resolve_config_label_from_manifest(
        image,
        manifest_payload,
        token,
        SOURCE_DIGEST_LABEL,
    )
    if source_digest is not None:
        return source_digest

    for descriptor in manifest_payload.get("manifests", []):
        annotations = descriptor.get("annotations", {})
        if annotations.get("vnd.docker.reference.type") != "attestation-manifest":
            continue
        attestation_manifest = _fetch_manifest_payload(image, descriptor["digest"], token)
        for layer in attestation_manifest.get("layers", []):
            if layer.get("mediaType") != "application/vnd.in-toto+json":
                continue
            statement = _fetch_blob_payload(image, layer["digest"], token)
            source_digest = _extract_source_digest_from_attestation_payload(statement)
            if source_digest is not None:
                return source_digest

    return None
