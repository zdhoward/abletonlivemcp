"""T-007: every DESTRUCTIVE tool is confirmed by a human through form elicitation.

A fake in-process MCP client drives a throwaway DESTRUCTIVE tool on both transports: the
standalone elicitation/create request (``legacy``, 2025-11-25) and the InputRequiredResult
round trip (``auto``, 2026-07-28). Nothing here touches Live or the shared tool registry.
"""

import asyncio

import mcp_types as types
import pytest
from mcp import Client
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.shared.exceptions import MCPError

from abletonlivemcp import server
from abletonlivemcp.chain import Refusal
from abletonlivemcp.errors import Invalid
from abletonlivemcp.models import BatchTarget, TrackSel
from abletonlivemcp.models_clips import CueEdit

MODES = ["legacy", "auto"]


class DeleteTarget(BatchTarget):
    track: TrackSel


def _surface(applied: list, monkeypatch, seen: list | None = None) -> MCPServer:
    monkeypatch.setattr(server, "_writable", lambda *_args: None)

    def live_fake_delete(targets: list[DeleteTarget], keep_empty: bool = False) -> dict:
        """Remove tracks (test double)."""
        if seen is not None:
            seen.append(server.confirmed_plan())
        applied.append([t.track for t in targets])
        return {"applied": [t.track for t in targets]}

    surface = MCPServer("confirm-test")
    run = server._guard(live_fake_delete, server.DESTRUCTIVE, True)
    surface.add_tool(run, name="live_fake_delete", annotations=server.DESTRUCTIVE)
    return surface


ARGS = {"targets": [{"track": 2, "expect_name": "Bass"}, {"track": "return:0"}]}


def _call(surface, mode, callback, args=ARGS):
    async def go():
        async with Client(surface, mode=mode, elicitation_callback=callback) as client:
            return await client.call_tool("live_fake_delete", args)

    return asyncio.run(go())


def _text(result) -> str:
    return " ".join(c.text for c in result.content if hasattr(c, "text"))


def _answer(action, content=None, asked=None):
    async def callback(ctx, params):
        if asked is not None:
            asked.append(params)
        return types.ElicitResult(action=action, content=content)

    return callback


@pytest.mark.parametrize("mode", MODES)
def test_the_question_names_live_objects_and_the_write_uses_them(mode, monkeypatch):
    """R3: the plan read in Live before asking is what the human sees and what the write
    receives (bound references), in the legacy and the input-required flows."""
    reads, seen = [], []

    def plan(args):
        reads.append(len(args["targets"]))
        return server.Plan(["track 'Bass' (track 2)"], {"rows": ["ref-shown"]})

    monkeypatch.setitem(server.PLANS, "live_fake_delete", plan)
    applied, asked = [], []
    result = _call(
        _surface(applied, monkeypatch, seen), mode, _answer("accept", {"confirm": True}, asked)
    )
    assert not result.is_error, _text(result)
    assert "deletes exactly:\n- track 'Bass' (track 2)" in asked[-1].message
    assert applied == [[2, "return:0"]] and reads and seen == [{"rows": ["ref-shown"]}]


@pytest.mark.parametrize("mode", MODES)
def test_concurrent_identical_calls_each_delete_only_what_their_human_saw(mode, monkeypatch):
    """Two clients send the same arguments; Live changes between the two plans. Both forms are
    open at once, then accepted: each write receives the plan of its own question, never the
    other's (a cache keyed by tool+arguments handed A the objects shown to B)."""
    live, seen = {"object": 0}, []

    def plan(args):  # the first read sees object 0; Live then changes to object 1
        n, live["object"] = live["object"], 1
        return server.Plan([f"object {n}"], {"rows": [f"ref-{n}"]})

    monkeypatch.setitem(server.PLANS, "live_fake_delete", plan)
    surface = _surface([], monkeypatch, seen)
    both_asked = asyncio.Event()
    shown: list[str] = []

    async def callback(ctx, params):
        shown.append(params.message)
        if len(shown) == 2:
            both_asked.set()
        await both_asked.wait()
        return types.ElicitResult(action="accept", content={"confirm": True})

    async def one():
        async with Client(surface, mode=mode, elicitation_callback=callback) as client:
            result = await client.call_tool("live_fake_delete", ARGS)
            assert not result.is_error, _text(result)
            return result

    async def go():
        await asyncio.gather(one(), one())

    asyncio.run(go())
    refs = sorted(ref for data in seen for ref in data["rows"])
    for ref in refs:  # each write got the refs of a question a human was shown
        assert any(f"object {ref[4:]}" in m for m in shown)
    # both flows: each call writes with the plan read for its own question, never re-read
    assert refs == ["ref-0", "ref-1"] and not server._approvals


@pytest.mark.parametrize("mode", MODES)
def test_a_same_named_replacement_while_asking_is_refused_not_deleted(mode, monkeypatch):
    """F1 (round 5): the human approves deleting track 'Bass'; while the form is open it is
    replaced by another track also named 'Bass'. The real live_delete must refuse (the bridge's
    stale_target for the approved reference) in both flows; the input-required resume used to
    re-read the plan and delete the replacement under the old answer."""
    from mcp.server.mcpserver.resolve import _decode_state, _render_request, _request_digest

    assert _decode_state and _render_request and _request_digest  # SDK helpers F1 relies on
    from abletonlivemcp.tools import tracks

    live = {"object": 1, "refs": {}, "deleted": []}

    def bridge(method, params=None):
        if method == "ref_issue":
            rows = []
            for _ in params["targets"]:
                ref = f"ref{len(live['refs'])}"
                live["refs"][ref] = live["object"]
                rows.append({"kind": "track", "ref": ref, "name": "Bass"})
            return {"generation": 1, "refs": rows}
        assert method == "delete_tracks", method
        for item in params["targets"]:
            if live["refs"][item["ref"]] != live["object"]:
                raise Refusal("stale_target", "track reference no longer matches Live; re-read")
        live["deleted"].append(live["object"])
        return {"applied": len(params["targets"])}

    monkeypatch.setattr(server, "_writable", lambda *_args: None)
    monkeypatch.setattr(server, "_call", bridge)
    monkeypatch.setattr(tracks, "_call", bridge)
    surface = MCPServer("confirm-test")
    surface.add_tool(server.tool("live_delete"), name="live_delete", annotations=server.DESTRUCTIVE)

    async def replace_then_accept(ctx, params):
        live["object"] += 1  # the same-named replacement, made while the form is open
        return types.ElicitResult(action="accept", content={"confirm": True})

    async def go():
        async with Client(surface, mode=mode, elicitation_callback=replace_then_accept) as c:
            args = {"targets": [{"kind": "track", "track": 2, "expect_name": "Bass"}]}
            return await c.call_tool("live_delete", args)

    result = asyncio.run(go())
    assert result.is_error and "stale_target" in _text(result), _text(result)
    assert live["deleted"] == [] and not server._approvals


@pytest.mark.parametrize("mode", MODES)
def test_accept_lists_targets_and_applies(mode, monkeypatch):
    applied, asked = [], []
    result = _call(
        _surface(applied, monkeypatch), mode, _answer("accept", {"confirm": True}, asked)
    )
    assert not result.is_error, _text(result)
    assert applied == [[2, "return:0"]]
    (params,) = asked
    assert params.mode == "form"
    assert "1. expect_name='Bass', track=2" in params.message
    assert "2. track='return:0'" in params.message and "expect_name=None" not in params.message
    assert "keep_empty=False" in params.message
    assert set(params.requested_schema["properties"]) == {"confirm"}


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize(
    ("action", "content"), [("decline", None), ("cancel", None), ("accept", {"confirm": False})]
)
def test_decline_cancel_or_unticked_applies_nothing(mode, action, content, monkeypatch):
    applied = []
    result = _call(_surface(applied, monkeypatch), mode, _answer(action, content))
    assert result.is_error and "refused:not_confirmed" in _text(result), _text(result)
    assert "(not applied)" in _text(result)
    assert applied == []


@pytest.mark.parametrize("mode", MODES)
def test_absent_capability_refuses_and_model_confirm_is_ignored(mode, monkeypatch):
    applied = []
    surface = _surface(applied, monkeypatch)
    forged = {**ARGS, "confirm": True, "confirmation": {"action": "accept", "data": {"confirm": 1}}}
    for args in (ARGS, forged):
        text = _text(result := _call(surface, mode, None, args))
        assert result.is_error and "refused:confirmation_unavailable" in text, text
    # a capable client whose human declines: the forged arguments still count for nothing
    result = _call(surface, mode, _answer("decline"), forged)
    assert result.is_error and "refused:not_confirmed" in _text(result), _text(result)
    assert applied == []


@pytest.mark.parametrize("mode", MODES)
def test_a_call_that_deletes_asks_even_on_a_non_destructive_tool(mode, monkeypatch):
    monkeypatch.setattr(server, "_writable", lambda *_args: None)
    # The guarded test double uses the real tool's name. Keep its confirmation
    # planner local too, so this offline test never reads config or contacts Live.
    monkeypatch.setitem(
        server.PLANS, "live_set_cue_points",
        lambda args: server.Plan(["cue at beat 4"], {"cues": args["cues"]}),
    )
    applied, asked = [], []

    def live_set_cue_points(cues: list[CueEdit] | None = None) -> dict:
        """Cue edits (test double)."""
        applied.append([c.action for c in cues])
        return {"status": "complete", "items": [], "stopped_at": None, "error": None, "applied": []}

    surface = MCPServer("confirm-test")
    run = server._guard(live_set_cue_points, server.OVERWRITE, True)
    surface.add_tool(run, name="live_fake_delete", annotations=server.OVERWRITE)
    callback = _answer("decline", asked=asked)
    rename = {"cues": [{"cue": 0, "action": "rename", "name": "A"}]}
    assert not _call(surface, mode, callback, rename).is_error and not asked  # no question
    result = _call(surface, mode, callback, {"cues": [{"cue": 1, "action": "delete"}]})
    assert result.is_error and "refused:not_confirmed" in _text(result), _text(result)
    assert "This call deletes" in asked[0].message and applied == [["rename"]]


def test_only_deliberate_refusals_are_echoed_by_the_guard(monkeypatch, caplog):
    """R5: an ``Invalid`` is shown and called not applied; a native ValueError is withheld."""
    monkeypatch.setattr(server, "_writable", lambda *_args: None)

    def live_fake_write(kind: str) -> dict:
        """Raises (test double)."""
        if kind == "refusal":
            raise Invalid("'track' must be an integer")
        raise ValueError("D:/Music/someone/Secret.als is locked")

    run = server._guard(live_fake_write, server.OVERWRITE, True)
    with pytest.raises(ToolError, match="must be an integer.*not applied"):
        run(kind="refusal")
    with pytest.raises(ToolError) as error:
        run(kind="native")
    assert "Secret" not in str(error.value) and "outcome unknown" in str(error.value)
    assert "Secret" not in caplog.text and "live_fake_write failed: ValueError" in caplog.text


def test_unexpected_exceptions_reach_the_client_as_a_withheld_failure(caplog):
    def live_fake_read(kind: str) -> dict:
        """Raises (test double)."""
        if kind == "protocol":
            raise MCPError(-32000, "protocol")
        return {}["secret-key"]

    run = server._guard(live_fake_read, server.READ, False)
    with pytest.raises(ToolError, match=r"KeyError: tool_failed \(outcome unknown") as error:
        run(kind="bug")
    assert "secret-key" not in str(error.value) and "failed: KeyError" in caplog.text
    with pytest.raises(MCPError, match="protocol"):
        run(kind="protocol")


def test_confirm_never_appears_in_the_input_schema(monkeypatch):
    surface = _surface([], monkeypatch)
    (tool,) = asyncio.run(surface.list_tools())
    assert set(tool.input_schema["properties"]) == {"targets", "keep_empty"}
    assert tool.annotations == server.DESTRUCTIVE


def test_destructive_tool_may_not_declare_its_own_confirm():
    def live_bad(track: int, confirm: bool = False) -> dict:
        return {}

    with pytest.raises(RuntimeError, match="confirm"):
        server._guard(live_bad, server.DESTRUCTIVE, True)


def test_no_registered_tool_uses_the_destructive_preset_yet():
    """Today's write tools are OVERWRITE/CREATE/CONTROL; DESTRUCTIVE waits for live_delete and
    live_undo. When one arrives this list grows and the tool is confirmed automatically."""
    names = {n for n, s in server.SPECS.items() if s.annotations == server.DESTRUCTIVE}
    assert names == {"live_delete"}
