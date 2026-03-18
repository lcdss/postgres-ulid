import os
import stat
import subprocess
from pathlib import Path


def write_executable(path: Path, body: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        f"{body}\n",
        encoding="utf-8",
    )
    path.chmod(path.stat().st_mode | stat.S_IEXEC)


def test_find_pg_config_prefers_path_entry(tmp_path: Path) -> None:
    path_dir = tmp_path / "path-bin"
    pg_config = path_dir / "pg_config"
    write_executable(pg_config)

    env = os.environ.copy()
    env["PATH"] = f"{path_dir}:{env['PATH']}"
    env["PG_CONFIG_SEARCH_ROOTS"] = str(tmp_path / "unused")

    result = subprocess.run(
        ["/usr/bin/bash", "scripts/find-pg-config.sh"],
        cwd=Path(__file__).resolve().parents[1],
        env=env,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == str(pg_config)


def test_find_pg_config_falls_back_to_major_specific_location(tmp_path: Path) -> None:
    pg_config = tmp_path / "usr/lib/postgresql/15/bin/pg_config"
    write_executable(pg_config)

    env = os.environ.copy()
    env["PATH"] = "/bin"
    env["PG_MAJOR"] = "15"
    env["PG_CONFIG_SKIP_PATH"] = "1"
    env["PG_CONFIG_SEARCH_ROOTS"] = str(tmp_path / "usr/lib/postgresql")

    result = subprocess.run(
        ["/usr/bin/bash", "scripts/find-pg-config.sh"],
        cwd=Path(__file__).resolve().parents[1],
        env=env,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == str(pg_config)


def test_find_pg_config_errors_when_not_found(tmp_path: Path) -> None:
    env = os.environ.copy()
    env["PATH"] = "/bin"
    env["PG_CONFIG_SKIP_PATH"] = "1"
    env["PG_CONFIG_SEARCH_ROOTS"] = str(tmp_path / "missing")

    result = subprocess.run(
        ["/usr/bin/bash", "scripts/find-pg-config.sh"],
        cwd=Path(__file__).resolve().parents[1],
        env=env,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert result.stderr.strip() == "pg_config not found"
