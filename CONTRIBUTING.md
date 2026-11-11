# Contributing

Thanks for helping. This is a small project; the process is deliberately light.

## Before you start

Read the [README](README.md) and [known limits](docs/validation.md). The project assists a person working in Ableton Live with
near-native control; it is not a fully autonomous production surface. Open an issue before large changes.

## Setup

```
python -m pip install -e ".[dev]"
ruff check .
pytest
```

Python 3.10+. CI runs on Linux and Windows.

## Guidelines

- Keep PRs small and focused; one change per PR.
- Core logic (file parsing, rack building, planning) must be testable **without Live running**. Only the thin remote-script layer needs Live.
- Tests use small synthetic fixtures in `tests/fixtures/`. Never commit real projects, samples, or presets (`.gitignore` blocks them).
- No telemetry, no network calls home, no secrets.
- State which Live version you tested on in the PR.
- Keep personal knowledge/research local. After distribution changes, run the
  [archive and clean-install checks](README.md#distribution); editable imports alone do not
  prove that a package or clean clone is complete.
- Socket rejection tests must verify bounded parsing and zero dispatch independently of
  diagnostic delivery: Windows can reset a socket closed with unread input.

## Commits and versions

Clear messages that say what and why. Versions follow semantic versioning (`MAJOR.MINOR.PATCH`).

## Conduct

See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
