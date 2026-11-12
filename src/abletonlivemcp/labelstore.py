"""The global labels sidecar: labels for things that are not part of one Set (plugins, devices,
samples), kept in one JSON file under a private data directory.

Directory: ``ABLETONLIVEMCP_DATA_DIR`` (an absolute path; tests and the final proof point it at a
scratch folder), else ``~/.abletonlivemcp/data``. The directory is refused when it, or any parent,
is a symlink, junction or reparse point. Every write is atomic: the new content goes to a temporary
file in the same directory, is flushed to disk, and replaces ``labels.json`` in one step; a lock
file serialises writers across processes. A corrupt or oversized file is never overwritten: the
write refuses and leaves it for the owner to inspect.
"""

from __future__ import annotations

import contextlib
import json
import os
import tempfile
import threading
import time
from pathlib import Path

from .config import ConfigError, checked_path
from .errors import Invalid

DATA_DIR_ENV = "ABLETONLIVEMCP_DATA_DIR"
FILE_NAME = "labels.json"
MAX_FILE_BYTES = 1024 * 1024
MAX_ENTRIES = 5000
LOCK_WAIT = 5.0
STALE_LOCK = 30.0
GLOBAL_KINDS = ("plugin", "device", "sample")
_thread_lock = threading.Lock()


class LabelStoreError(Invalid):
    """The sidecar cannot be read or written safely (nothing was changed)."""


def data_dir() -> Path:
    override = os.environ.get(DATA_DIR_ENV)
    path = Path(override) if override else Path.home() / ".abletonlivemcp" / "data"
    if not path.is_absolute():
        raise LabelStoreError(f"{DATA_DIR_ENV} must be an absolute path")
    try:
        return checked_path(path)
    except ConfigError as exc:
        raise LabelStoreError(str(exc)) from exc


def _empty() -> dict:
    return {"version": 1, "entries": {kind: {} for kind in GLOBAL_KINDS}}


def load() -> dict:
    """The sidecar content (an empty store when the file does not exist yet)."""
    path = data_dir() / FILE_NAME
    try:
        if not path.exists():
            return _empty()
        if path.stat().st_size > MAX_FILE_BYTES:
            raise LabelStoreError(f"{path} is larger than {MAX_FILE_BYTES} bytes")
        value = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise LabelStoreError(f"cannot read {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise LabelStoreError(f"{path} is not valid JSON: {exc}") from exc
    entries = value.get("entries") if isinstance(value, dict) else None
    if not isinstance(entries, dict) or not all(
        isinstance(entries.get(k, {}), dict) for k in entries
    ):
        raise LabelStoreError(f"{path} does not have the expected shape")
    for kind in GLOBAL_KINDS:
        entries.setdefault(kind, {})
    return {"version": 1, "entries": entries}


@contextlib.contextmanager
def _locked(directory: Path):
    """One writer at a time, across threads and processes (an exclusive lock file)."""
    lock = directory / (FILE_NAME + ".lock")
    deadline = time.monotonic() + LOCK_WAIT
    with _thread_lock:
        while True:
            try:
                fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.close(fd)
                break
            except FileExistsError:
                with contextlib.suppress(OSError):
                    if time.time() - lock.stat().st_mtime > STALE_LOCK:
                        lock.unlink()
                        continue
                if time.monotonic() > deadline:
                    raise LabelStoreError("the labels file is busy; retry later") from None
                time.sleep(0.05)
        try:
            yield
        finally:
            with contextlib.suppress(OSError):
                lock.unlink()


def _write_atomic(directory: Path, store: dict) -> None:
    text = json.dumps(store, ensure_ascii=False, sort_keys=True, indent=1)
    if len(text.encode("utf-8")) > MAX_FILE_BYTES:
        raise LabelStoreError("the labels file would exceed its size limit")
    fd, name = tempfile.mkstemp(prefix=".labels-", suffix=".tmp", dir=directory)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, directory / FILE_NAME)
    finally:
        with contextlib.suppress(OSError):
            os.unlink(name)


def merge(existing: dict | None, labels: list[str], category: str | None, mode: str):
    """One entry after applying ``mode`` (replace | add | remove); None means the entry is gone.
    Labels keep first-seen order and are unique."""
    old_labels = list((existing or {}).get("labels", []))
    old_category = (existing or {}).get("category")
    if mode == "replace":
        new_labels, new_category = list(dict.fromkeys(labels)), category
    elif mode == "add":
        new_labels = list(dict.fromkeys(old_labels + labels))
        new_category = category if category is not None else old_category
    elif mode == "remove":
        new_labels = [x for x in old_labels if x not in set(labels)]
        new_category = None if category == "" else old_category
    else:
        raise LabelStoreError("mode must be replace, add or remove")
    if not new_labels and not new_category:
        return None
    entry: dict = {"labels": new_labels}
    if new_category:
        entry["category"] = new_category
    return entry


def apply(items: list[dict], mode: str) -> dict:
    """Apply ``[{kind, key, labels, category}]`` to the sidecar in one atomic write. Returns the
    changed entries (``None`` for a removed one) keyed ``kind``/``key``."""
    directory = data_dir()
    directory.mkdir(parents=True, exist_ok=True)
    checked_path(directory)
    changed: dict = {}
    with _locked(directory):
        store = load()
        for item in items:
            table = store["entries"][item["kind"]]
            entry = merge(table.get(item["key"]), item["labels"], item.get("category"), mode)
            if entry is None:
                table.pop(item["key"], None)
            else:
                table[item["key"]] = entry
            changed[f"{item['kind']}/{item['key']}"] = entry
        if sum(len(t) for t in store["entries"].values()) > MAX_ENTRIES:
            raise LabelStoreError(f"more than {MAX_ENTRIES} global labels")
        _write_atomic(directory, store)
    return changed
