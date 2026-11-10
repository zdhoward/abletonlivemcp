"""Turn a chain of roles into concrete devices for THIS user's Live, and say what was decided.

Input stages look like {"role": "compressor", "intent": {"threshold": "-18 dB", "ratio": 4}}.
For each stage the resolver:
  1. orders the candidate devices: the user's preferences for that role first, then the stock
     device (so a chain with no preferences builds the same way on any machine);
  2. drops candidates that are not installed (stock: Live's browser; plugins: a browser search);
  3. skips "opaque" devices, which Live will load but will not let a script configure;
  4. maps each intent value onto the chosen device's parameters through its adapter.
The report explains every choice, substitution and guess, so nothing is silent.
"""

from __future__ import annotations

from .adapters import PLUGINS, STOCK, Adapter, adapters_for, known_roles
from .chain import ChainError, parse_display


class _Unmapped(Exception):
    pass


def _norm(name: str) -> str:
    """Compare plugin names loosely: ignore case, spaces, punctuation and a _x64 suffix.

    Live lists the same plugin as 'ValhallaVintageVerb_x64', 'Pro-C 2' or 'FabFilter Pro-C 2'
    depending on the vendor. Version numbers stay, so 'Pro-C' and 'Pro-C 2' remain different.
    """
    squashed = "".join(ch for ch in name.lower() if ch.isalnum())
    for suffix in ("x64", "x86"):
        squashed = squashed.removesuffix(suffix)
    return squashed.removeprefix("fabfilter")


def _translate(spec: dict, value):
    """One intent value -> (build_chain target, note or None)."""
    v, level = (
        (value.get("value"), value.get("level")) if isinstance(value, dict) else (value, None)
    )
    mode = spec.get("mode", "display")
    if mode == "display":
        if v is None:
            raise _Unmapped("needs a physical value such as '1.2 s'")
        return v, None
    if mode == "percent_raw":
        parsed = parse_display(str(v)) if v is not None else None
        if parsed is None or parsed[1] != "%":
            raise _Unmapped("needs a percentage such as '12 %'")
        return {"raw": parsed[0] / 100}, f"{spec['param']} written as a bare fraction (no units)"
    levels = spec["levels"]
    if level not in levels:
        raise _Unmapped(f"needs a level, one of {sorted(levels)}")
    raw = levels[level]
    return {"raw": raw}, f"{spec['param']}: level {level!r} -> {raw} is a guess, not calibrated"


class Inventory:
    """What this Live has, looked up lazily through the bridge and cached for one plan."""

    def __init__(self, call):
        self._call = call
        self._stock: set[str] | None = None
        self._plugins: dict[str, list[str] | None] = {}

    def stock_has(self, name: str) -> bool:
        if self._stock is None:
            listing = self._call("browser_list", {"root": STOCK, "path": []})
            items = listing["items"] if isinstance(listing, dict) else listing
            self._stock = {(i["name"] if isinstance(i, dict) else i).lower() for i in items}
        return name.lower() in self._stock

    def plugin_path(self, name: str) -> list[str] | None:
        """Browser path of an installed plugin, preferring VST3 over VST; None if absent."""
        if name not in self._plugins:
            found = self._call("browser_search", {"root": PLUGINS, "query": name, "limit": 15})
            hits = [
                h for h in found["results"] if h["is_loadable"] and _norm(h["name"]) == _norm(name)
            ]
            hits.sort(key=lambda h: h["path"][0] != "VST3")
            self._plugins[name] = hits[0]["path"] if hits else None
        return self._plugins[name]


def _candidates(role: str, prefs: dict) -> tuple[list[Adapter], list[str]]:
    """Adapters in the order to try, plus preferred names that have no adapter yet."""
    available = adapters_for(role)
    by_name = {a.device.lower(): a for a in available}
    wanted = [str(n) for n in (prefs.get(role) or [])]
    ordered = [by_name[n.lower()] for n in wanted if n.lower() in by_name]
    unknown = [n for n in wanted if n.lower() not in by_name]
    rest = sorted((a for a in available if a not in ordered), key=lambda a: a.root != STOCK)
    return ordered + rest, unknown


def _map_intent(adapter: Adapter, intent: dict) -> tuple[dict, list[str]]:
    params: dict = {}
    notes: list[str] = []
    for key, value in intent.items():
        spec = adapter.params.get(key)
        if spec is None:
            notes.append(f"{adapter.device} has no mapping for {key!r}; skipped")
            continue
        try:
            target, note = _translate(spec, value)
        except _Unmapped as exc:
            notes.append(f"{adapter.device}: {key!r} {exc}; skipped")
            continue
        params[spec["param"]] = target
        params.update(adapter.setup.get(key, {}))
        if note:
            notes.append(f"{adapter.device}: {note}")
    return params, notes


def plan_chain(call, stages: list[dict], preferences: dict | None = None) -> dict:
    """Resolve role stages into concrete `build_chain` stages. Only reads from Live."""
    prefs = {k.lower(): v for k, v in (preferences or {}).items()}
    if not isinstance(stages, list) or not stages:
        raise ChainError("'stages' must be a non-empty list")
    inventory = Inventory(call)
    concrete, report = [], []
    for stage in stages:
        role = stage.get("role") if isinstance(stage, dict) else None
        intent = stage.get("intent", {}) if isinstance(stage, dict) else None
        if role not in known_roles() or not isinstance(intent, dict):
            raise ChainError(
                f"each stage needs a known 'role' {known_roles()}; 'intent' must be an object"
            )
        order, no_adapter = _candidates(role, prefs)
        why: list[str] = [f"no adapter yet for preferred {n!r}" for n in no_adapter]
        chosen = None
        for adapter in order:
            if adapter.root == STOCK:
                path = [adapter.device] if inventory.stock_has(adapter.device) else None
            else:
                path = inventory.plugin_path(adapter.device)
            if path is None:
                why.append(f"{adapter.device}: not installed")
            elif adapter.access == "opaque":
                why.append(f"{adapter.device}: installed but not controllable. {adapter.notes}")
            else:
                chosen = (adapter, path)
                break
        if chosen is None:
            raise ChainError(f"no usable device for role {role!r}: {why}")
        adapter, path = chosen
        params, notes = _map_intent(adapter, intent)
        entry = {"device": adapter.device, "params": params}
        if adapter.root != STOCK:
            entry |= {"root": adapter.root, "path": path}
        concrete.append(entry)
        report.append(
            {
                "role": role,
                "device": adapter.device,
                "access": adapter.access,
                "skipped": why,
                "notes": notes,
            }
        )
    return {"stages": concrete, "report": report}
