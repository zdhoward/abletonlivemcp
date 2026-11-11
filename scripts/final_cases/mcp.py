"""Hooks for scripts/final_cases/mcp.json: prompts/list+get and resources/list+read over the
final session's MCP client (read-only; no writes)."""

from __future__ import annotations

PROMPTS = {
    "vocal_chain", "organize_session", "setup_scene", "mix_check", "explain_chain",
    "diagnose_connection", "safe_tweak", "build_drum_rack", "macro_fx_rack", "arrange_sections",
}  # fmt: skip
STATIC_DOCS = ("docs://conventions/units", "docs://safety", "docs://limits")
LIVE_READS = (
    "live://session", "live://tracks", "live://track/0", "live://capabilities",
)  # fmt: skip


def _text(result) -> str:
    return "".join(getattr(c, "text", "") or "" for c in result.contents)


async def check_prompts(run, case, chk):
    session = run.h.session
    names = {p.name for p in (await session.list_prompts()).prompts}
    chk.require(
        PROMPTS <= names, "prompts/list has every prompt", f"missing {sorted(PROMPTS - names)}"
    )
    for name in sorted(PROMPTS):
        got = await session.get_prompt(name, {})
        body = "".join(getattr(m.content, "text", "") for m in got.messages)
        chk.require(bool(body.strip()), f"prompts/get {name}")


async def check_resources(run, case, chk):
    session = run.h.session
    listed = {str(r.uri) for r in (await session.list_resources()).resources}
    for uri in (*STATIC_DOCS, *LIVE_READS[:2], "knowledge://index"):
        chk.require(uri in listed, f"resources/list has {uri}")
    for uri in (*STATIC_DOCS, "knowledge://index", *LIVE_READS):
        text = _text(await session.read_resource(uri))
        chk.require(bool(text.strip()), f"resources/read {uri}", text[:80])
