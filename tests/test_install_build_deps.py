import os
import stat
import subprocess
from pathlib import Path


def write_fake_command(
    bin_dir: Path,
    name: str,
    body: str,
) -> None:
    command = bin_dir / name
    command.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        f"{body}\n",
        encoding="utf-8",
    )
    command.chmod(command.stat().st_mode | stat.S_IEXEC)


def test_install_build_deps_uses_apt_for_debian_images(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    log_file = tmp_path / "commands.log"

    write_fake_command(
        bin_dir,
        "apt-get",
        'printf "apt-get %s\\n" "$*" >>"$FAKE_COMMAND_LOG"',
    )
    write_fake_command(
        bin_dir,
        "rm",
        'printf "rm %s\\n" "$*" >>"$FAKE_COMMAND_LOG"',
    )

    env = os.environ.copy()
    env["PATH"] = f"{bin_dir}:{env['PATH']}"
    env["FAKE_COMMAND_LOG"] = str(log_file)

    result = subprocess.run(
        ["/usr/bin/bash", "scripts/install-build-deps.sh"],
        cwd=Path(__file__).resolve().parents[1],
        env=env,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    commands = log_file.read_text(encoding="utf-8").splitlines()

    assert commands[:2] == [
        "apt-get update",
        (
            "apt-get install -y --no-install-recommends "
            "bash build-essential ca-certificates clang curl git libclang-dev "
            "libssl-dev llvm-dev pkg-config rustc cargo"
        ),
    ]
    assert len(commands) == 3
    assert commands[2].startswith("rm -rf /var/lib/apt/lists/")
