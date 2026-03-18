import json
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


def resolve_config_label(image: str, tag: str, label: str) -> str | None:
    token = fetch_registry_token(image)
    manifest_request = Request(
        f"https://registry-1.docker.io/v2/{image}/manifests/{tag}",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": MANIFEST_ACCEPT,
        },
    )
    with urlopen(manifest_request) as response:
        manifest_payload = json.load(response)

    config_digest = manifest_payload.get("config", {}).get("digest")
    if config_digest is None:
        return None

    blob_request = Request(
        f"https://registry-1.docker.io/v2/{image}/blobs/{config_digest}",
        headers={"Authorization": f"Bearer {token}"},
    )
    with urlopen(blob_request) as response:
        config_payload = json.load(response)
    return config_payload.get("config", {}).get("Labels", {}).get(label)
