import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class MirrorPolicy:
    mode: str
    minimum_major: int | None = None


def load_policy(path: Path) -> MirrorPolicy:
    raw = json.loads(path.read_text(encoding="utf-8"))
    mode = raw["mode"]
    if mode == "major-alpine":
        minimum_major = raw.get("minimum_major")
        if not isinstance(minimum_major, int):
            raise ValueError("major-alpine policy requires integer minimum_major")
        return MirrorPolicy(mode=mode, minimum_major=minimum_major)
    if mode not in {"all-tags"}:
        raise ValueError(f"Unsupported mirror mode: {mode}")
    return MirrorPolicy(mode=mode)
