import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class MirrorPolicy:
    mode: str


def load_policy(path: Path) -> MirrorPolicy:
    raw = json.loads(path.read_text(encoding="utf-8"))
    mode = raw["mode"]
    if mode not in {"alpine-only", "all-tags"}:
        raise ValueError(f"Unsupported mirror mode: {mode}")
    return MirrorPolicy(mode=mode)
