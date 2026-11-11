"""Resources and prompts register, render and stay out of the tool surface (batch 6)."""

from __future__ import annotations

import asyncio
import json
import re

from abletonlivemcp import knowledge, prompts, resources, server

PROMPT_NAMES = {
    "vocal_chain", "organize_session", "setup_scene", "mix_check", "explain_chain",
    "diagnose_connection", "safe_tweak", "build_drum_rack", "macro_fx_rack", "arrange_sections",
}  # fmt: skip


def run(coro):
    return asyncio.run(coro)


def test_prompts_listed_and_render():
    listed = {p.name for p in run(server.mcp.list_prompts())}
    assert PROMPT_NAMES <= listed
    for name in PROMPT_NAMES:
        got = run(server.mcp.get_prompt(name, {}))
        assert "".join(m.content.text for m in got.messages).strip()


def test_prompts_name_only_real_tools():
    known = set(server.SPECS)
    allowed_missing = set()  # every final tool a prompt names must be registered once batches merge
    text = " ".join(
        f()
        for f in (
            prompts._organize_session, prompts._setup_scene, prompts._mix_check,
            prompts._explain_chain, prompts._diagnose_connection, prompts._safe_tweak,
            prompts._build_drum_rack, prompts._macro_fx_rack, prompts._arrange_sections,
        )
    )  # fmt: skip
    from abletonlivemcp.proof_contract import FINAL_SURFACE

    final = {t for names in FINAL_SURFACE.values() for t in names}
    named = set(re.findall(r"\blive_[a-z]+(?:_[a-z]+)*\b", text + prompts._vocal_chain()))
    assert named <= final | known | allowed_missing, sorted(named - final - known)


def test_mix_check_is_read_only_guidance():
    text = prompts._mix_check()
    assert "NO writes" in text
    for tool in ("live_set_tracks", "live_create_tracks", "live_delete"):
        assert tool not in text


def test_vocal_presets_fallback_and_stages():
    presets = prompts.vocal_presets()
    assert presets and all(p["stages"] for p in presets.values())
    assert "Stages:" in prompts._vocal_chain("no_such_preset")


def test_resources_listed():
    uris = {str(r.uri) for r in run(server.mcp.list_resources())}
    for uri in (
        "live://session", "live://tracks", "live://capabilities", "docs://conventions/units",
        "docs://safety", "docs://limits", "knowledge://index",
    ):  # fmt: skip
        assert uri in uris
    templates = {t.uri_template for t in run(server.mcp.list_resource_templates())}
    assert "live://track/{track}/device/{device}/parameters" in templates
    assert "knowledge://{page}" in templates


def test_static_docs_and_knowledge_read_offline():
    for uri, marker in (
        ("docs://safety", "read_only"),
        ("docs://conventions/units", "0-based"),
        ("docs://limits", "macro"),
    ):
        text = "".join(c.content for c in run(server.mcp.read_resource(uri)))
        assert marker in text
    if knowledge.available():
        index = json.loads(
            "".join(c.content for c in run(server.mcp.read_resource("knowledge://index")))
        )
        assert index and {"page", "title"} <= set(index[0])


def test_live_resource_uses_registered_tool_and_reports_unavailable():
    spec = type("Spec", (), {"fn": staticmethod(lambda **kw: {"tempo": 120}), "toolset": "core"})
    fake = type("S", (), {"SPECS": {"live_get_session": spec}, "ENABLED": frozenset({"core"})})
    assert json.loads(resources._call_tool(fake, "live_get_session")) == {"tempo": 120}
    assert "unavailable" in json.loads(resources._call_tool(fake, "live_get_tracks"))


def test_registering_adds_no_tools():
    assert not {n for n in server.SPECS if "prompt" in n or "resource" in n}
