import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen


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
            "Accept": ", ".join(
                [
                    "application/vnd.docker.distribution.manifest.list.v2+json",
                    "application/vnd.oci.image.index.v1+json",
                    "application/vnd.docker.distribution.manifest.v2+json",
                ]
            )
        },
        method="HEAD",
    )
    with urlopen(request) as response:
        digest = response.headers["Docker-Content-Digest"]
    return digest
