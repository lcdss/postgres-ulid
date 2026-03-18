import os
import stat
import subprocess
from pathlib import Path


def write_fake_pg_config(
    bin_dir: Path,
    pkglibdir: str,
    sharedir: str,
) -> Path:
    pg_config = bin_dir / "pg_config"
    pg_config.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        'case "${1:-}" in\n'
        '  --pkglibdir)\n'
        f'    printf "%s\\n" "{pkglibdir}"\n'
        "    ;;\n"
        '  --sharedir)\n'
        f'    printf "%s\\n" "{sharedir}"\n'
        "    ;;\n"
        "  *)\n"
        '    printf "unexpected arg: %s\\n" "${1:-}" >&2\n'
        "    exit 1\n"
        "    ;;\n"
        "esac\n",
        encoding="utf-8",
    )
    pg_config.chmod(pg_config.stat().st_mode | stat.S_IEXEC)
    return pg_config


def test_stage_extension_artifacts_preserves_pg_config_layout(tmp_path: Path) -> None:
    install_root = tmp_path / "install-root"
    pkglibdir = install_root / "usr/lib/postgresql/15/lib"
    extension_dir = install_root / "usr/share/postgresql/15/extension"
    pkglibdir.mkdir(parents=True)
    extension_dir.mkdir(parents=True)

    (pkglibdir / "pgx_ulid.so").write_text("shared object", encoding="utf-8")
    (extension_dir / "pgx_ulid.control").write_text("control file", encoding="utf-8")
    (extension_dir / "pgx_ulid--0.2.3.sql").write_text("sql", encoding="utf-8")

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    pg_config = write_fake_pg_config(
        bin_dir=bin_dir,
        pkglibdir="/usr/lib/postgresql/15/lib",
        sharedir="/usr/share/postgresql/15",
    )

    output_root = tmp_path / "out"
    env = os.environ.copy()
    env["PATH"] = f"{bin_dir}:{env['PATH']}"

    result = subprocess.run(
        [
            "/usr/bin/bash",
            "scripts/stage-extension-artifacts.sh",
            str(pg_config),
            str(install_root),
            str(output_root),
        ],
        cwd=Path(__file__).resolve().parents[1],
        env=env,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert (
        output_root / "usr/lib/postgresql/15/lib/pgx_ulid.so"
    ).read_text(encoding="utf-8") == "shared object"
    assert (
        output_root / "usr/share/postgresql/15/extension/pgx_ulid.control"
    ).read_text(encoding="utf-8") == "control file"
    assert (
        output_root / "usr/share/postgresql/15/extension/pgx_ulid--0.2.3.sql"
    ).read_text(encoding="utf-8") == "sql"
