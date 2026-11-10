import math

import pytest

from abletonlivemcp.chain import (
    ChainError,
    build_chain,
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
            return {
                "results": [
                    self.call(
                        "set_device_parameter",
                        {**p, "parameter": w["parameter"], "value": w["value"]},
                    )
                    for w in p["writes"]
                ]
            }
        if method == "sample_parameter":
            n = ["On", "Threshold", "Frequency", "Ratio", "Type"][p["parameter"]]
            return {"name": n, "displays": [self._display(n, v) for v in p["values"]]}
        if method == "set_device_parameter":
            n = ["On", "Threshold", "Frequency", "Ratio", "Type"][p["parameter"]]
            self.vals[p["device"]][n] = p["value"]
            return {"name": n, "value": p["value"], "display": self._display(n, p["value"])}
        raise AssertionError(method)

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


def test_build_chain_loads_in_order_and_reports_actual_values():
    live = FakeLive()
    out = build_chain(
        live.call,
        0,
        [
            {"device": "eq eight", "params": {"Type": "High Pass 12dB", "frequency": "80 Hz"}},
            {"device": "Compressor", "params": {"Threshold": "-18 dB", "Ratio": 4}},
        ],
    )
    assert out["ok"] and live.devices == ["EQ Eight", "Compressor"]
    assert [s["index"] for s in out["stages"]] == [0, 1]
    assert all(p["exact"] for s in out["stages"] for p in s["params"])


def test_a_stage_costs_a_handful_of_bridge_calls_not_one_per_parameter():
    live = FakeLive()
    params = {"Type": "Bell", "Frequency": "1 kHz", "Threshold": "-18 dB", "Ratio": 4}
    out = build_chain(live.call, 0, [{"device": "Compressor", "params": params}])
    assert out["ok"]
    # the fake's batch calls reuse its single-parameter ones; count only what crossed the bridge
    outer = [c for c in live.calls if c not in ("sample_parameter", "set_device_parameter")]
    # browser_list, load_item, device_parameters, then sampling and writing in batches
    assert len(outer) <= 9, outer
    assert outer.count("set_device_parameters") == 2  # options wave, then numbers wave


def test_options_are_written_before_numeric_parameters():
    live = FakeLive()
    build_chain(
        live.call,
        0,
        [
            {
                "device": "Compressor",
                "params": {"Frequency": "1 kHz", "Type": "Bell", "Device On": True},
            }
        ],
    )
    first, second = live.writes
    assert set(first) == {0, 4} and second == [2]  # Device On and Type, then Frequency


def test_off_target_value_makes_the_chain_not_ok():
    live = FakeLive()

    def clamping_call(method, p=None):
        reply = live.call(method, p)
        if method == "set_device_parameters":  # Live reads back something far from the target
            for r in reply["results"]:
                r["display"] = "9.00 : 1"
        return reply

    out = build_chain(clamping_call, 0, [{"device": "Compressor", "params": {"Ratio": 4}}])
    assert out["ok"] is False and out["stages"][0]["params"][0]["exact"] is False


def test_unknown_device_fails_before_anything_is_loaded():
    live = FakeLive()
    with pytest.raises(ChainError, match="not in Live"):
        build_chain(live.call, 0, [{"device": "Compressor"}, {"device": "Pultec"}])
    assert "load_item" not in live.calls and live.devices == []


def test_unknown_parameter_is_reported_not_fatal_and_marks_chain_not_ok():
    live = FakeLive()
    out = build_chain(live.call, 0, [{"device": "Compressor", "params": {"Threshhold": "-18 dB"}}])
    assert out["ok"] is False
    assert "Threshold" in out["stages"][0]["problems"][0]


@pytest.mark.parametrize(
    "stages", [[], "Compressor", [{"params": {}}], [{"device": "x", "params": 3}]]
)
def test_bad_stage_shapes_are_refused(stages):
    with pytest.raises(ChainError):
        build_chain(FakeLive().call, 0, stages)
    with pytest.raises(ChainError):
        build_chain(FakeLive().call, 0, [{"device": "Compressor"}] * 13)


class StubPlugin:
    """A plugin whose `Style` is words reported as a continuous parameter, and `Mix` a bare 0..1."""

    STYLES = ["Clean", "Classic", "Opto", "Vocal"]
    PARAMS = [
        {"index": 0, "name": "Style", "min": 0.0, "max": 1.0, "is_quantized": False},
        {"index": 1, "name": "Mix", "min": 0.0, "max": 1.0, "is_quantized": False},
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
            "results": [{"display": self._display(w["parameter"], w["value"])} for w in p["writes"]]
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


def test_text_options_are_written_before_numbers():
    stub = StubPlugin()
    set_parameters(
        stub.call, {}, [(StubPlugin.PARAMS[1], {"raw": 0.5}), (StubPlugin.PARAMS[0], "Opto")]
    )
    assert stub.writes == [[0], [1]]


def test_stage_with_explicit_path_loads_by_path_and_skips_the_stock_listing():
    live = FakeLive()
    loads = []

    def spy(method, p=None):
        if method == "load_item":
            loads.append(p)
        return live.call(method, p)

    stage = {"device": "Pro-C 2", "root": "plugins", "path": ["Compressor"], "params": {"Ratio": 4}}
    out = build_chain(spy, 0, [stage])
    assert out["ok"] and "browser_list" not in live.calls
    assert loads == [{"track": 0, "root": "plugins", "path": ["Compressor"]}]
    for bad in ["x", [], None]:
        with pytest.raises(ChainError, match="path"):
            build_chain(live.call, 0, [{**stage, "path": bad}])
