"""Check runtime-only archives and optionally a clean stdio install (no Live connection).

Usage: python scripts/check_distribution.py dist [--smoke]
Build first with `python -m build`. --smoke installs dependencies from the configured pip index.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tarfile
import tempfile
import venv
import zipfile
from pathlib import Path, PurePosixPath

SMOKE = """\
import asyncio
import sys
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import abletonlivemcp
from abletonlivemcp.install import REQUIRED, source_files

assert Path(abletonlivemcp.__file__).resolve().is_relative_to(Path(sys.prefix).resolve())
files = source_files()
assert REQUIRED <= files.keys(), sorted(REQUIRED - files.keys())
assert all(files[name].read_bytes() for name in REQUIRED)

async def main():
    params = StdioServerParameters(
        command=sys.executable, args=["-I", "-m", "abletonlivemcp.server"]
    )
    async with stdio_client(params) as (read, write), ClientSession(read, write) as session:
        await session.initialize()
        tools = (await session.list_tools()).tools
        assert tools and any(tool.name == "live_hello" for tool in tools)
        assert all(tool.output_schema is not None for tool in tools)
        print(f"Clean install: {len(REQUIRED)} Remote Script modules, {len(tools)} tools")

asyncio.run(main())
"""


def check_name(name: str) -> PurePosixPath:
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts or "\\" in name:
        raise ValueError(f"Unsafe archive path: {name}")
    return path


def check_archives(directory: Path) -> Path:
    wheels = list(directory.glob("*.whl"))
    sources = list(directory.glob("*.tar.gz"))
    if len(wheels) != 1 or len(sources) != 1:
        raise ValueError("Use a clean build directory containing exactly one wheel and one sdist")
    wheel = wheels[0]
    with zipfile.ZipFile(wheel) as archive:
        wheel_files = {n for n in archive.namelist() if not n.endswith("/")}
        for name in wheel_files:
            path = check_name(name)
            if not (
                (path.parts[0] == "abletonlivemcp" and
                 (path.suffix == ".py" or name == "abletonlivemcp/NOTICE"))
                or path.parts[0].endswith(".dist-info")
            ):
                raise ValueError(f"Unexpected wheel payload: {name}")
        if "abletonlivemcp/NOTICE" not in wheel_files:
            raise ValueError("Wheel is missing NOTICE attribution")

    with tarfile.open(sources[0], "r:gz") as archive:
        source_files = set()
        for member in archive.getmembers():
            path = check_name(member.name)
            if member.isdir():
                continue
            if not member.isfile() or len(path.parts) < 2:
                raise ValueError(f"Unexpected source archive member: {member.name}")
            relative = PurePosixPath(*path.parts[1:])
            name = str(relative)
            # Hatch always includes VCS ignore metadata in sdists, even when excluded.
            allowed = name in {
                ".gitignore", "pyproject.toml", "README.md", "LICENSE", "NOTICE", "PKG-INFO"
            }
            allowed |= name.startswith("src/abletonlivemcp/") and relative.suffix == ".py"
            allowed |= (
                name.startswith("remote_script/AbletonLiveMCP/") and relative.suffix == ".py"
            )
            if not allowed:
                raise ValueError(f"Unexpected source archive payload: {name}")
            source_files.add(name)
        if "NOTICE" not in source_files:
            raise ValueError("Source archive is missing NOTICE attribution")

    # Every source runtime module must survive both package paths, including probe imports.
    source_runtime = {
        name.removeprefix("src/") for name in source_files if name.startswith("src/")
    }
    source_runtime |= {
        "abletonlivemcp/_remote_script/" + name.removeprefix("remote_script/")
        for name in source_files if name.startswith("remote_script/")
    }
    wheel_runtime = {name for name in wheel_files if name.endswith(".py")}
    if source_runtime != wheel_runtime:
        raise ValueError(
            f"Runtime archive mismatch: missing={sorted(source_runtime - wheel_runtime)}, "
            f"extra={sorted(wheel_runtime - source_runtime)}"
        )
    print(f"Archives: {len(wheel_runtime)} matching runtime modules; no development payloads")
    return wheel.resolve()


def smoke_install(wheel: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="abletonlivemcp-package-") as temporary:
        root = Path(temporary)
        environment = root / "venv"
        venv.EnvBuilder(with_pip=True).create(environment)
        python = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        env = {k: v for k, v in os.environ.items() if k not in {
            "PYTHONPATH", "PYTHONHOME", "VIRTUAL_ENV", "ABLETONLIVEMCP_KNOWLEDGE",
        }}
        env.update(
            ABLETONLIVEMCP_CONFIG=str(root / "unprovisioned-bridge.json"),
            ABLETONLIVEMCP_TOOLSETS="core",
        )
        subprocess.run(
            [str(python), "-m", "pip", "install", "--quiet", "--disable-pip-version-check",
             str(wheel)],
            cwd=root, env=env, check=True, timeout=300,
        )
        script = root / "smoke.py"
        script.write_text(SMOKE, encoding="utf-8")
        subprocess.run(
            [str(python), "-I", str(script)], cwd=root, env=env, check=True, timeout=60,
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()
    wheel = check_archives(args.directory)
    if args.smoke:
        smoke_install(wheel)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        sys.exit(f"Distribution check failed: {exc}")
