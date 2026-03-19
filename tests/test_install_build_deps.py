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


def test_install_build_deps_debian_uses_apt_and_rustup(tmp_path: Path) -> None:
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
    write_fake_command(
        bin_dir,
        "curl",
        'printf "curl %s\\n" "$*" >>"$FAKE_COMMAND_LOG"\n'
        'printf "#!/usr/bin/env bash\\nexit 0\\n"',
    )
    write_fake_command(
        bin_dir,
        "sh",
        'printf "sh %s\\n" "$*" >>"$FAKE_COMMAND_LOG"',
    )

    env = os.environ.copy()
    env["PATH"] = f"{bin_dir}:{env['PATH']}"
    env["FAKE_COMMAND_LOG"] = str(log_file)
    env["PG_MAJOR"] = "17"

    result = subprocess.run(
        ["/usr/bin/bash", "scripts/install-build-deps-debian.sh"],
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
            "libpq-dev libssl-dev llvm-dev pkg-config "
            "postgresql-server-dev-17 zlib1g-dev"
        ),
    ]
    assert "curl -fsSL https://sh.rustup.rs" in commands
    assert (
        "sh -s -- -y --profile minimal --default-toolchain stable "
        "--component rustfmt"
    ) in commands
    assert len(commands) == 5
    assert commands[4].startswith("rm -rf /var/lib/apt/lists/")


def test_install_build_deps_alpine_uses_apk_and_packaged_rust(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    log_file = tmp_path / "commands.log"

    write_fake_command(
        bin_dir,
        "apk",
        'if [[ "$1" == "info" ]]; then\n'
        '  printf "clang19\\n"\n'
        "  exit 0\n"
        "fi\n"
        'printf "apk %s\\n" "$*" >>"$FAKE_COMMAND_LOG"',
    )
    write_fake_command(
        bin_dir,
        "curl",
        'printf "curl %s\\n" "$*" >>"$FAKE_COMMAND_LOG"\n'
        'printf "#!/usr/bin/env bash\\nexit 0\\n"',
    )
    write_fake_command(
        bin_dir,
        "sh",
        'printf "sh %s\\n" "$*" >>"$FAKE_COMMAND_LOG"',
    )

    env = os.environ.copy()
    env["PATH"] = f"{bin_dir}:{env['PATH']}"
    env["FAKE_COMMAND_LOG"] = str(log_file)

    result = subprocess.run(
        ["/usr/bin/bash", "scripts/install-build-deps-alpine.sh"],
        cwd=Path(__file__).resolve().parents[1],
        env=env,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    commands = log_file.read_text(encoding="utf-8").splitlines()

    assert commands == [
        (
            "apk add --no-cache --virtual .build-deps bash build-base clang curl git "
            "llvm-dev openssl-dev pkgconf rust rustfmt cargo"
        ),
        "apk add --no-cache clang19-libclang",
    ]
