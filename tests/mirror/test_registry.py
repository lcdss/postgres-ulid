import json

from scripts.mirror.registry import resolve_config_label, resolve_source_digest


class FakeResponse:
    def __init__(self, payload: dict):
        self._payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self._payload).encode("utf-8")


def test_resolve_config_label_reads_label_from_image_config(monkeypatch) -> None:
    requests = []

    def fake_fetch_registry_token(image: str) -> str:
        assert image == "lcdss/postgres-ulid"
        return "token"

    def fake_urlopen(request):
        requests.append(request.full_url)
        if request.full_url.endswith("/manifests/16-alpine"):
            return FakeResponse(
                {
                    "config": {
                        "digest": "sha256:config",
                    }
                }
            )
        if request.full_url.endswith("/blobs/sha256:config"):
            return FakeResponse(
                {
                    "config": {
                        "Labels": {
                            "io.github.lcdss.postgres-ulid.source-digest": "sha256:bbb"
                        }
                    }
                }
            )
        raise AssertionError(request.full_url)

    monkeypatch.setattr(
        "scripts.mirror.registry.fetch_registry_token", fake_fetch_registry_token
    )
    monkeypatch.setattr("scripts.mirror.registry.urlopen", fake_urlopen)

    label = resolve_config_label(
        "lcdss/postgres-ulid",
        "16-alpine",
        "io.github.lcdss.postgres-ulid.source-digest",
    )

    assert label == "sha256:bbb"
    assert requests == [
        "https://registry-1.docker.io/v2/lcdss/postgres-ulid/manifests/16-alpine",
        "https://registry-1.docker.io/v2/lcdss/postgres-ulid/blobs/sha256:config",
    ]


def test_resolve_config_label_returns_none_when_label_is_missing(monkeypatch) -> None:
    def fake_fetch_registry_token(image: str) -> str:
        assert image == "lcdss/postgres-ulid"
        return "token"

    def fake_urlopen(request):
        if request.full_url.endswith("/manifests/16-alpine"):
            return FakeResponse(
                {
                    "config": {
                        "digest": "sha256:config",
                    }
                }
            )
        if request.full_url.endswith("/blobs/sha256:config"):
            return FakeResponse({"config": {"Labels": {}}})
        raise AssertionError(request.full_url)

    monkeypatch.setattr(
        "scripts.mirror.registry.fetch_registry_token", fake_fetch_registry_token
    )
    monkeypatch.setattr("scripts.mirror.registry.urlopen", fake_urlopen)

    label = resolve_config_label(
        "lcdss/postgres-ulid",
        "16-alpine",
        "io.github.lcdss.postgres-ulid.source-digest",
    )

    assert label is None


def test_resolve_source_digest_reads_digest_from_attestation(monkeypatch) -> None:
    def fake_fetch_registry_token(image: str) -> str:
        assert image == "lcdss/postgres-ulid"
        return "token"

    def fake_urlopen(request):
        if request.full_url.endswith("/manifests/17-alpine"):
            return FakeResponse(
                {
                    "manifests": [
                        {
                            "digest": "sha256:image-manifest",
                            "mediaType": "application/vnd.oci.image.manifest.v1+json",
                            "platform": {
                                "architecture": "amd64",
                                "os": "linux",
                            },
                        },
                        {
                            "annotations": {
                                "vnd.docker.reference.type": "attestation-manifest",
                            },
                            "digest": "sha256:attestation-manifest",
                            "mediaType": "application/vnd.oci.image.manifest.v1+json",
                            "platform": {
                                "architecture": "unknown",
                                "os": "unknown",
                            },
                        },
                    ]
                }
            )
        if request.full_url.endswith("/manifests/sha256:image-manifest"):
            return FakeResponse(
                {
                    "config": {
                        "digest": "sha256:image-config",
                    }
                }
            )
        if request.full_url.endswith("/blobs/sha256:image-config"):
            return FakeResponse({"config": {"Labels": {}}})
        if request.full_url.endswith("/manifests/sha256:attestation-manifest"):
            return FakeResponse(
                {
                    "config": {
                        "digest": "sha256:attestation-config",
                    },
                    "layers": [
                        {
                            "digest": "sha256:attestation-layer",
                            "mediaType": "application/vnd.in-toto+json",
                        }
                    ],
                }
            )
        if request.full_url.endswith("/blobs/sha256:attestation-layer"):
            return FakeResponse(
                {
                    "predicate": {
                        "buildDefinition": {
                            "externalParameters": {
                                "request": {
                                    "args": {
                                        "build-arg:BASE_IMAGE": (
                                            "docker.io/library/postgres@sha256:bbb"
                                        )
                                    }
                                }
                            }
                        }
                    }
                }
            )
        if request.full_url.endswith("/blobs/sha256:attestation-config"):
            return FakeResponse({"config": {}})
        raise AssertionError(request.full_url)

    monkeypatch.setattr(
        "scripts.mirror.registry.fetch_registry_token", fake_fetch_registry_token
    )
    monkeypatch.setattr("scripts.mirror.registry.urlopen", fake_urlopen)

    digest = resolve_source_digest("lcdss/postgres-ulid", "17-alpine")

    assert digest == "sha256:bbb"
