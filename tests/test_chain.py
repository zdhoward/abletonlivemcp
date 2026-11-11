import math

import pytest

from abletonlivemcp.bridge import BridgeError
from abletonlivemcp.chain import (
    ChainError,
    Refusal,
    WriteInterrupted,
    _resolve,
    checked,
    make_plan,
    parse_display,
    set_parameters,
    set_to_display,
)


@pytest.mark.parametrize(
    "text,expected",
    [
        ("1.00 kHz", (1000.0, "hz")),
        ("80.0 Hz", (80.0, "hz")),
        ("1.20 s", (1200.0, "ms")),
        ("30.0 ms", (30.0, "ms")),
        ("-18.0 dB", (-18.0, "db")),
        ("4.00 : 1", (4.0, None)),
        ("100 %", (100.0, "%")),
        ("-inf dB", (-math.inf, "db")),
    ],
)
def test_parse_display(text, expected):
    assert parse_display(text) == expected


def test_parse_display_rejects_words():
    assert parse_display("Soft Sine") is None


def _db(v):
    return -60.0 + 60.0 * v**0.5  # nonlinear, rising: 0 -> -60 dB, 1 -> 0 dB


def _hz(v):
    return 20.0 * 1000.0**v  # 20 Hz .. 20 kHz


def _fmt_hz(hz):
    return f"{hz / 1000:.2f} kHz" if hz >= 1000 else f"{hz:.1f} Hz"


class FakeLive:
    """One track; each loaded device gets Threshold, Frequency, Ratio, Type and Device On."""

    TYPES = ["Low Shelf", "Bell", "High Pass 12dB"]

    def __init__(self, devices=("Compressor", "EQ Eight")):
        self.browser = list(devices)
        self.devices = []
        self.vals = []
        self.calls = []
        self.writes = []

    def call(self, method, p=None):
        p = p or {}
        self.calls.append(method)
        if method == "browser_list":
            return {"items": [{"name": n} for n in self.browser]}
        if method == "load_item":
            before = len(self.devices)
            self.devices.append(p["path"][0])
            self.vals.append(
                {"Threshold": 0.5, "Frequency": 0.3, "Ratio": 0.1, "Type": 0.0, "On": 1.0}
            )
            return {"loaded": p["path"][0], "devices_before": before, "devices_after": before + 1}
        if method == "device_parameters":
            rows = [
                ("Device On", "On", 0, 1, True),
                ("Threshold", "Threshold", 0, 1, False),
                ("Frequency", "Frequency", 0, 1, False),
                ("Ratio", "Ratio", 0, 1, False),
                ("Type", "Type", 0, 2, True),
            ]
            return [
                {
                    "index": i,
                    "ref": f"{p['device']}:{i}",
                    "name": n,
                    "value": self.vals[p["device"]][k],
                    "min": lo,
                    "max": hi,
                    "is_quantized": q,
                    "display": self._display(n, self.vals[p["device"]][k]),
                }
                for i, (n, k, lo, hi, q) in enumerate(rows)
            ]
        if method == "sample_parameters":
            return {
                "results": [
                    self.call(
                        "sample_parameter", {"parameter": r["parameter"], "values": r["values"]}
                    )
                    for r in p["requests"]
                ]
            }
        if method == "set_device_parameters":
            self.writes.append([w["parameter"] for w in p["writes"]])
            return {"results": [self._write(w["parameter"], w["value"]) for w in p["writes"]]}
        if method == "sample_parameter":
            n = ["On", "Threshold", "Frequency", "Ratio", "Type"][p["parameter"]]
            return {"name": n, "displays": [self._display(n, v) for v in p["values"]]}
        raise AssertionError(method)

    def _write(self, ref, value):
        """Writes name a parameter by the reference its read issued ('device:index')."""
        device, index = (int(x) for x in ref.split(":"))
        n = ["On", "Threshold", "Frequency", "Ratio", "Type"][index]
        self.vals[device][n] = value
        return {"name": n, "value": value, "display": self._display(n, value)}

    def _display(self, name, v):
        if name == "Threshold":
            return f"{_db(v):.1f} dB"
        if name == "Frequency":
            return _fmt_hz(_hz(v))
        if name == "Ratio":
            return f"{1 + 19 * v * v:.2f} : 1"
        if name == "Type":
            return self.TYPES[int(v)]
        return "On" if v else "Off"


def _param(live, name, device=0):
    return next(p for p in live.call("device_parameters", {"device": device}) if p["name"] == name)


def test_solves_db_ratio_and_frequency_through_unit_changes():
    live = FakeLive()
    live.call("load_item", {"path": ["Compressor"]})
    for name, target, want in [
        ("Threshold", "-18 dB", -18.0),
        ("Ratio", 4, 4.0),
        ("Frequency", "80 Hz", 80.0),
        ("Frequency", "1 kHz", 1000.0),
        ("Frequency", "12 kHz", 12000.0),
    ]:
        r = set_to_display(live.call, {"track": 0, "device": 0}, _param(live, name), target)
        assert r["exact"], r
        assert parse_display(r["actual"])[0] == pytest.approx(want, rel=0.02)


def test_quantized_option_and_on_off():
    live = FakeLive()
    live.call("load_item", {"path": ["EQ Eight"]})
    loc = {"track": 0, "device": 0}
    r = set_to_display(live.call, loc, _param(live, "Type"), "High Pass 12dB")
    assert r["actual"] == "High Pass 12dB"
    assert set_to_display(live.call, loc, _param(live, "Device On"), False)["actual"] == "Off"
    with pytest.raises(ChainError, match="options are"):
        set_to_display(live.call, loc, _param(live, "Type"), "Band Reject")


@pytest.mark.parametrize(
    "name,target,message",
    [
        ("Threshold", -18, "give a unit"),
        ("Threshold", "5 dB", "outside"),
        ("Threshold", "10 Hz", "does not match"),
        ("Ratio", "4 dB", "no unit"),
        ("Threshold", "loud", "cannot read a number"),
    ],
)
def test_bad_targets_are_refused(name, target, message):
    live = FakeLive()
    live.call("load_item", {"path": ["Compressor"]})
    with pytest.raises(ChainError, match=message):
        set_to_display(live.call, {"track": 0, "device": 0}, _param(live, name), target)


class StubPlugin:
    """A plugin whose `Style` is words reported as a continuous parameter, and `Mix` a bare 0..1."""

    STYLES = ["Clean", "Classic", "Opto", "Vocal"]
    PARAMS = [
        {"index": 0, "ref": "r0", "name": "Style", "min": 0.0, "max": 1.0, "is_quantized": False},
        {"index": 1, "ref": "r1", "name": "Mix", "min": 0.0, "max": 1.0, "is_quantized": False},
    ]

    def __init__(self):
        self.calls = []
        self.writes = []

    def _display(self, index, v):
        return self.STYLES[min(int(v * 4), 3)] if index == 0 else f"{v:.2f}"

    def call(self, method, p):
        self.calls.append(method)
        if method == "sample_parameters":
            return {
                "results": [
                    {"displays": [self._display(r["parameter"], v) for v in r["values"]]}
                    for r in p["requests"]
                ]
            }
        assert method == "set_device_parameters"
        self.writes.append([w["parameter"] for w in p["writes"]])
        return {
            "results": [
                {"display": self._display(int(w["parameter"][1:]), w["value"]), "value": w["value"]}
                for w in p["writes"]
            ]
        }


def test_option_names_reported_as_continuous_are_matched_by_text():
    stub = StubPlugin()
    results, problems = set_parameters(stub.call, {}, [(StubPlugin.PARAMS[0], "vocal")])
    assert not problems and results[0]["actual"] == "Vocal" and results[0]["exact"]
    results, problems = set_parameters(stub.call, {}, [(StubPlugin.PARAMS[0], "Warm")])
    assert not results and "options are ['Clean', 'Classic', 'Opto', 'Vocal']" in problems[0]


def test_raw_targets_are_written_as_given_without_sampling():
    stub = StubPlugin()
    results, problems = set_parameters(stub.call, {}, [(StubPlugin.PARAMS[1], {"raw": 0.3})])
    assert not problems and results[0]["exact"] and results[0]["actual"] == "0.30"
    assert stub.calls == ["set_device_parameters"]
    for bad in [{"raw": 2}, {"raw": True}, {"raw": "x"}, {}]:
        _, problems = set_parameters(stub.call, {}, [(StubPlugin.PARAMS[1], bad)])
        assert "raw value must be a number" in problems[0]


def _loaded(*names):
    live = FakeLive()
    for n in names:
        live.call("load_item", {"path": [n]})
    return live


def test_options_are_written_before_numbers_in_few_bridge_calls():
    """The one authoritative ordering/cost check (writes name parameters by reference)."""
    live = _loaded("Compressor")
    loc = {"track": 0, "device": 0}
    items = [
        (_param(live, "Frequency"), "1 kHz"),
        (_param(live, "Type"), "Bell"),
        (_param(live, "Device On"), True),
        (_param(live, "Threshold"), "-18 dB"),
    ]
    results, problems = set_parameters(live.call, loc, items)
    assert not problems and all(r["exact"] for r in results)
    assert [r["name"] for r in results] == ["Frequency", "Type", "Device On", "Threshold"]
    first, second = live.writes
    assert set(first) == {"0:0", "0:4"} and set(second) == {"0:2", "0:1"}  # options, then numbers
    assert live.calls.count("set_device_parameters") == 2
    assert live.calls.count("sample_parameters") <= 6  # batched rounds, not one per parameter


def test_off_target_readback_is_reported_not_claimed_exact():
    live = _loaded("Compressor")

    def clamping(method, p=None):
        reply = live.call(method, p)
        if method == "set_device_parameters":  # Live reads back something far from the target
            for r in reply["results"]:
                r["display"] = "9.00 : 1"
        return reply

    (r,), problems = set_parameters(
        clamping, {"track": 0, "device": 0}, [(_param(live, "Ratio"), 4)]
    )
    assert not problems and (r["exact"], r["off_target"], r["actual"]) == (False, True, "9.00 : 1")
    assert r["original"] == {"value": 0.1, "display": "1.19 : 1"}  # what it was before


@pytest.mark.parametrize(
    "cause,check",
    [
        ({"refused": True, "applied": False, "code": "read_only", "message": "off"}, "refusal"),
        (BridgeError("Timeout", "lost", may_have_applied=True), "unknown"),
    ],
)
def test_interrupted_write_keeps_what_was_applied_and_does_not_retry(cause, check):
    live = _loaded("Compressor")
    sent = []

    def flaky(method, p=None):
        if method == "set_device_parameters":
            sent.append(method)
            if len(sent) == 2:  # the numbers wave fails after the options wave landed
                if isinstance(cause, Exception):
                    raise cause
                return cause
        return live.call(method, p)

    items = [(_param(live, "Type"), "Bell"), (_param(live, "Frequency"), "1 kHz")]
    with pytest.raises(WriteInterrupted) as stop:
        set_parameters(checked(flaky), {"track": 0, "device": 0}, items)
    done = stop.value.results
    assert [r["name"] for r in done] == ["Type"] and done[0]["exact"]  # applied, kept, reported
    if check == "refusal":
        assert isinstance(stop.value.cause, Refusal) and stop.value.cause.code == "read_only"
    else:
        assert stop.value.cause.may_have_applied is True
    assert len(sent) == 2  # no retry and no substitute write
    assert live.vals[0]["Frequency"] == 0.3  # the refused numeric write never landed


@pytest.mark.parametrize(
    "stages", [[], "Compressor", [{"params": {}}], [{"device": "x", "params": 3}]]
)
def test_bad_stage_shapes_are_refused_before_any_bridge_call(stages):
    def never(*_a):
        pytest.fail("the bridge must not be called for an invalid plan")

    with pytest.raises(ChainError):
        make_plan(never, stages, 0, {}, None)
    with pytest.raises(ChainError):
        make_plan(never, [{"device": "Compressor"}] * 13, 0, {}, None)


def test_plan_with_explicit_path_skips_the_stock_listing_and_checks_the_path():
    live = FakeLive()
    calls = []

    def call(method, p=None):
        calls.append(method)
        if method == "session_info":
            return {"generation": 3}
        if method == "device_list":
            owner = {"kind": "track", "name": "Vox", "has_midi_input": False}
            return {"owner": owner, "container": "track", "devices": []}
        return live.call(method, p)

    stage = {"device": "Pro-C 2", "root": "plugins", "path": ["Compressor"], "params": {"Ratio": 4}}
    plan = make_plan(call, [stage], 0, {}, None)
    assert "browser_list" not in calls and "load_item" not in calls  # planning loads nothing
    assert (plan.stages[0].root, plan.stages[0].path) == ("plugins", ("Compressor",))
    assert plan.target.generation == 3 and plan.target.name == "Vox"
    for bad in ["x", [], None]:
        with pytest.raises(ChainError, match="path"):
            make_plan(call, [{**stage, "path": bad}], 0, {}, None)


def test_parameter_names_resolve_uniquely_and_typos_are_reported_with_suggestions():
    params = _loaded("Compressor").call("device_parameters", {"device": 0})
    assert _resolve(params, "threshold")["name"] == "Threshold"
    with pytest.raises(ChainError, match="Threshold"):
        _resolve(params, "Threshhold")
