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

from abletonlivemcp import server
from abletonlivemcp.errors import Invalid
from abletonlivemcp.models import BatchTarget, TrackSel
from abletonlivemcp.models_clips import CueEdit

MODES = ["legacy", "auto"]


class DeleteTarget(BatchTarget):
    track: TrackSel


def _surface(applied: list, monkeypatch) -> MCPServer:
    monkeypatch.setattr(server, "_writable", lambda *_args: None)

    def live_fake_delete(targets: list[DeleteTarget], keep_empty: bool = False) -> dict:
        """Remove tracks (test double)."""
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
def test_accept_lists_targets_and_applies(mode, monkeypatch):
    applied, asked = [], []
    result = _call(
        _surface(applied, monkeypatch), mode, _answer("accept", {"confirm": True}, asked)
    )
    assert not result.is_error, _text(result)
    assert applied == [[2, "return:0"]]
    (params,) = asked
    assert params.mode == "form"
    assert "1. track=2; expect_name='Bass'" in params.message
    assert "2. track='return:0'; expect_name=None" in params.message
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
