# Contributing

Thanks for helping. This is a small project; the process is deliberately light.

## Before you start

Read the [README](README.md) and [known limits](docs/validation.md). The project assists a person working in Ableton Live with
near-native control; it is not a fully autonomous production surface. Open an issue before large changes.

## Setup

```
python -m venv .venv
# Windows PowerShell (on macOS/Linux use .venv/bin/python):
.venv/Scripts/python.exe -m pip install -e ".[dev]"
.venv/Scripts/python.exe -m ruff check .
.venv/Scripts/python.exe -m pytest -q
```

Python 3.10+. CI runs tests and Ruff on Python 3.10 through 3.14 on Linux and Windows.
These offline checks do not qualify a Live installation on either OS. macOS is untested.

## Guidelines

- Keep PRs small and focused; one change per PR.
- Core logic (file parsing, rack building, planning) must be testable **without Live running**. Only the thin remote-script layer needs Live.
- Tests use small synthetic fixtures in `tests/fixtures/`. Never commit real projects, samples, or presets (`.gitignore` blocks them).
- No telemetry, no network calls home, no secrets.
- State which Live version you tested on in the PR.
- Keep personal knowledge/research local. After distribution changes, run the
  [archive and clean-install checks](#distribution); editable imports alone do not
  prove that a package or clean clone is complete.
- Socket rejection tests must verify bounded parsing and zero dispatch independently of
  diagnostic delivery: Windows can reset a socket closed with unread input.

## Commits and versions

Clear messages that say what and why. Versions follow semantic versioning (`MAJOR.MINOR.PATCH`).

## Distribution

The root `.gitignore` allowlists public files. Add new documentation deliberately.
Keep personal reference material and local client config outside the public tree.
Wheels and source archives contain runtime modules, the bundled Remote Script,
README/package metadata and license/attribution files. Tests, proof helpers and
developer `probe_pNN.py` modules stay out of both archives.

Build both archives directly from the tree so the check can catch wheel-only leaks:

```powershell
.venv/Scripts/python.exe -m pip install build
.venv/Scripts/python.exe -m build --sdist --wheel
.venv/Scripts/python.exe scripts/check_distribution.py dist --smoke
```

The checker compares runtime modules across both archives and rejects unexpected
files. `--smoke` installs the wheel and dependencies in a disposable environment,
then initializes a stdio client and lists tools without connecting to Live.
Omit that flag to inspect archives only. CI checks both Linux and Windows.
The [1.0.0 distribution manifest](docs/distribution-1.0.0.md) lists every shipped file.

Live proof helpers under `scripts/` are for contributors with a disposable Set.
They can change Live and local configuration; read each helper before running it.
The [validation record](docs/validation.md) distinguishes Live checks from offline tests.

## Windows installer verification

Run `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/check_windows_installer.ps1`
with Claude Code installed. It downloads a real runtime and PyPI package, installs into
a temporary User Library and registers Claude Code in an isolated config directory.
It checks a fresh install, rerun, running-Live refusal, invalid library and preserved
registration conflict. It leaves temporary artifacts for inspection and does not
connect to Live or change your normal Claude configuration.

## Conduct

See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
