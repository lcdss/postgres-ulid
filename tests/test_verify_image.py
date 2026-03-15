import os
import stat
import subprocess
from pathlib import Path


def write_fake_docker(bin_dir: Path) -> None:
    docker = bin_dir / "docker"
    docker.write_text(
        """#!/usr/bin/env bash
set -euo pipefail

state_dir=${FAKE_DOCKER_STATE:?}
command=${1:?}
shift

case "$command" in
  run)
    while [ "$#" -gt 0 ]; do
      case "$1" in
        --name)
          shift
          container=$1
          ;;
      esac
      shift
    done
    printf '%s\\n' "$container" >"$state_dir/container-name"
    : >"$state_dir/running"
    echo "fake-container-id"
    ;;
  rm)
    rm -f "$state_dir/running"
    ;;
  ps)
    if [ -f "$state_dir/running" ]; then
      cat "$state_dir/container-name"
    fi
    ;;
  exec)
    container=$1
    shift
    tool=$1
    shift
    case "$tool" in
      pg_isready)
        echo 1 >"$state_dir/pg-isready-count"
        exit 0
        ;;
      psql)
        count_file="$state_dir/psql-count"
        count=0
        if [ -f "$count_file" ]; then
          count=$(cat "$count_file")
        fi
        count=$((count + 1))
        echo "$count" >"$count_file"
        if [ "$count" -eq 1 ]; then
          echo 'psql: error: connection to server on socket "/var/run/postgresql/.s.PGSQL.5432" failed: No such file or directory' >&2
          exit 2
        fi
        exit 0
        ;;
    esac
    ;;
  logs)
    echo "container logs"
    ;;
esac
""",
        encoding="utf-8",
    )
    docker.chmod(docker.stat().st_mode | stat.S_IEXEC)


def test_verify_image_retries_sql_until_postgres_is_stable(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    write_fake_docker(bin_dir)

    env = os.environ.copy()
    env["PATH"] = f"{bin_dir}:{env['PATH']}"
    env["FAKE_DOCKER_STATE"] = str(tmp_path)

    result = subprocess.run(
        ["bash", "scripts/verify-image.sh", "postgres-ulid:test"],
        cwd=Path(__file__).resolve().parents[1],
        env=env,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert (tmp_path / "psql-count").read_text(encoding="utf-8").strip() == "2"
