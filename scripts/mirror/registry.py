from urllib.request import Request, urlopen


def resolve_manifest_digest(image: str, tag: str) -> str:
    request = Request(
        f"https://registry-1.docker.io/v2/{image}/manifests/{tag}",
        headers={
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
