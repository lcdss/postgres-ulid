import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class MirrorPolicy:
    minimum_major: int
    families: tuple[str, ...]


def load_policy(path: Path) -> MirrorPolicy:
    raw = json.loads(path.read_text(encoding="utf-8"))
    minimum_major = raw.get("minimum_major")
    if not isinstance(minimum_major, int):
        raise ValueError("policy requires integer minimum_major")
    families = raw.get("families")
    if (
        not isinstance(families, list)
        or not families
        or any(not isinstance(family, str) or not family for family in families)
    ):
        raise ValueError("policy requires non-empty string families")
    return MirrorPolicy(
        minimum_major=minimum_major,
        families=tuple(families),
    )
