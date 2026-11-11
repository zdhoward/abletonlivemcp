"""The per-domain module contract: declarations merge fail-closed and every module installs."""

import ast
import re
import sys
import types
from pathlib import Path

import pytest

SCRIPT_DIR = Path(__file__).resolve().parents[1] / "remote_script" / "AbletonLiveMCP"
sys.path.insert(0, str(SCRIPT_DIR.parent))

from AbletonLiveMCP import handlers, safety  # noqa: E402
from abletonlivemcp import install  # noqa: E402


def _module(name, methods):
    module = types.ModuleType(name)
    module.METHODS = methods
    return module


def _handler(*_a):
    return None


def test_domain_list_matches_the_files_the_installer_requires():
    on_disk = {p.name for p in SCRIPT_DIR.glob("*.py")}
    domains = {f"{m.__name__.rsplit('.', 1)[-1]}.py" for m in safety.DOMAINS}
    assert domains == {n for n in on_disk if n.startswith("dom_")}
    assert install.REQUIRED == on_disk  # nothing on disk is optional, nothing required is missing
    assert set(install.source_files()) == on_disk


def test_merge_matches_the_handler_table():
    reads = {m for m, k in safety.CLASSIFICATION.items() if k == safety.READ}
    writes = {m for m, k in safety.CLASSIFICATION.items() if k == safety.WRITE}
    assert set(safety.HANDLERS) == reads | writes
    assert set(safety.TARGETS) == writes
    assert set(handlers._handlers(object(), object(), object())) == reads | writes
    assert {m for m, k in safety.CLASSIFICATION.items() if k == safety.CONTROL} == {
        "lease_acquire",
        "lease_release",
    }


@pytest.mark.parametrize(
    "methods",
    [
        {"tracks": (_handler, "read", None)},  # duplicate of dom_tracks
        {"lease_acquire": (_handler, "read", None)},  # duplicate of a gate method
        {"x": (_handler, "control", None)},  # control is reserved for the gate
        {"x": (_handler, "admin", None)},  # unclassified kind
        {"x": (_handler, None, None)},
        {"x": (None, "read", None)},  # no handler
        {"x": (_handler, "read")},  # wrong arity
        {"x": (_handler, "read", ())},  # a read takes no targets
        {"x": (_handler, "write", None)},  # a write must declare its targets
        {"x": (_handler, "write", (("track", "bogus"),))},  # unknown reference kind
        {"x": (_handler, "write", (("track",),))},
        {"x": (_handler, "write", [("track", "track")])},
        {"": (_handler, "read", None)},
    ],
)
def test_bad_declarations_fail_closed(methods):
    with pytest.raises(safety.DeclarationError):
        safety._merge(safety.DOMAINS + (_module("dom_bad", methods),))


def test_a_module_without_methods_fails_closed():
    with pytest.raises(safety.DeclarationError):
        safety._merge((types.ModuleType("dom_empty"),))


def test_duplicate_across_two_new_modules_fails_closed():
    a = _module("dom_a", {"same": (_handler, "read", None)})
    b = _module("dom_b", {"same": (_handler, "write", ())})
    with pytest.raises(safety.DeclarationError, match="duplicate"):
        safety._merge((a, b))


def test_domain_modules_use_relative_imports_and_the_stdlib_only():
    """Live's embedded Python loads the script as a package with no ctypes and no site-packages;
    domain modules also must not import ``safety`` (it imports them)."""
    allowed = {"math", "itertools", "json", "Live"}
    paths = sorted(SCRIPT_DIR.glob("dom_*.py")) + sorted(SCRIPT_DIR.glob("probe_p*.py"))
    for path in paths:
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Import):
                assert {a.name.split(".")[0] for a in node.names} <= allowed, path.name
            elif isinstance(node, ast.ImportFrom):
                if node.level == 0:
                    assert node.module.split(".")[0] in allowed, path.name
                elif node.module is None and path.name == "dom_probe.py":
                    # the fixed probe table: only the flat probe_pNN modules
                    assert all(re.fullmatch(r"probe_p\d\d", a.name) for a in node.names)
                else:
                    assert node.module in ("core", "dom_common"), (path.name, node.module)
