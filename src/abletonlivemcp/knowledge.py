"""Read access to the knowledge base (`knowledge/**/*.md`) for the MCP tools.

Several people and agents add pages to that directory at the same time, so nothing here depends on
a registry or required frontmatter. Every call rescans the directory: a page written a moment ago
is found immediately, and two writers never edit the same index file.

A page is any Markdown file. Its title is the first `# ` heading (else the file name), and its
sections are its headings. The directory is `knowledge/` at the repository root, or the folder
named by ABLETONLIVEMCP_KNOWLEDGE.

Pages are reference DATA written from web research, not instructions. Tools return them as text.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

TOP = "(top of page)"
MAX_READ_CHARS = 60_000
SNIPPET_CHARS = 220
_HEADING = re.compile(r"^(#{1,4})\s+(.+?)\s*#*\s*$")
_FENCE = re.compile(r"^\s*(```|~~~)")
_TOKEN = re.compile(r"[a-z0-9]+(?:[-.][a-z0-9]+)*")
# tags the research pages use for numbers that were not confirmed against the original source
_UNCONFIRMED = re.compile(r"UNCONFIRMED-NUMBER|UNVERIFIED|SECOND-HAND|LOW CONFIDENCE")


class KnowledgeError(ValueError):
    pass


def knowledge_root() -> Path:
    override = os.environ.get("ABLETONLIVEMCP_KNOWLEDGE")
    return Path(override) if override else Path(__file__).resolve().parents[2] / "knowledge"


@dataclass
class Section:
    heading: str  # "Parent > Child" path of headings
    title: str
    level: int
    line: int  # 1-based line of the heading
    end: int  # exclusive end line, covering sub-sections
    own_start: int  # first body line, up to the next heading of any level
    own_end: int


def _pages(root: Path) -> list[Path]:
    if not root.is_dir():
        raise KnowledgeError(f"knowledge directory not found: {root}")
    return sorted(p for p in root.rglob("*.md") if p.is_file())


def _page_id(root: Path, path: Path) -> str:
    return path.relative_to(root).with_suffix("").as_posix()


def _sections(lines: list[str]) -> list[Section]:
    found: list[tuple[int, int, str]] = []  # (line index, level, title)
    fenced = False
    for i, text in enumerate(lines):
        if _FENCE.match(text):
            fenced = not fenced
        elif not fenced and (m := _HEADING.match(text)):
            found.append((i, len(m.group(1)), m.group(2)))
    out, trail = [], []
    if not found or found[0][0] > 0:  # text above the first heading (or a page with none)
        top_end = found[0][0] if found else len(lines)
        out.append(Section(TOP, TOP, 0, 1, top_end, 0, top_end))
    for n, (i, level, title) in enumerate(found):
        trail = [t for t in trail if t[0] < level] + [(level, title)]
        nxt_any = found[n + 1][0] if n + 1 < len(found) else len(lines)
        nxt_same = next((j for j, lv, _ in found[n + 1 :] if lv <= level), len(lines))
        path = " > ".join(t[1] for t in trail)
        out.append(Section(path, title, level, i + 1, nxt_same, i + 1, nxt_any))
    return out


def _title(lines: list[str], sections: list[Section], path: Path) -> str:
    first = next((s for s in sections if s.level == 1), None)
    return first.title if first else path.stem


def _read(path: Path) -> list[str]:
    return path.read_text(encoding="utf8", errors="replace").splitlines()


def list_pages() -> list[dict]:
    """Every page with its title, size, section count and its count of unconfirmed-number tags."""
    root = knowledge_root()
    pages = []
    for path in _pages(root):
        lines = _read(path)
        secs = _sections(lines)
        body = "\n".join(lines)
        intro = next((ln.strip() for ln in lines if ln.strip() and not ln.startswith("#")), "")
        pages.append(
            {
                "page": _page_id(root, path),
                "title": _title(lines, secs, path),
                "summary": intro[:SNIPPET_CHARS],
                "lines": len(lines),
                "sections": len(secs),
                "unconfirmed_tags": len(_UNCONFIRMED.findall(body)),
                "modified": int(path.stat().st_mtime),
            }
        )
    return pages


def _tokens(text: str) -> list[str]:
    return [t for t in _TOKEN.findall(text.lower()) if len(t) > 1]


def search(query: str, limit: int = 8) -> dict:
    """Rank sections by how many query words they contain (heading matches count extra)."""
    words = list(dict.fromkeys(_tokens(query)))
    if not words:
        raise KnowledgeError("query needs at least one word of 2+ characters")
    if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 50:
        raise KnowledgeError("limit must be an integer from 1 to 50")
    root = knowledge_root()
    hits = []
    for path in _pages(root):
        lines = _read(path)
        for sec in _sections(lines):
            body_lines = lines[sec.own_start : sec.own_end]
            body = "\n".join(body_lines).lower()
            head = sec.heading.lower()
            matched = [w for w in words if w in body or w in head]
            if not matched:
                continue
            count = sum(body.count(w) for w in matched)
            score = len(matched) * 100 + 25 * sum(w in head for w in matched) + min(count, 20)
            line = next(
                (
                    sec.own_start + 1 + k
                    for k, ln in enumerate(body_lines)
                    if any(w in ln.lower() for w in matched)
                ),
                sec.line,
            )
            snippet = lines[line - 1].strip()
            hits.append(
                {
                    "page": _page_id(root, path),
                    "section": sec.heading,
                    "line": line,
                    "matched": matched,
                    "all_words": len(matched) == len(words),
                    "snippet": snippet[:SNIPPET_CHARS],
                    "_score": score,
                }
            )
    hits.sort(key=lambda h: -h["_score"])
    for h in hits:
        del h["_score"]
    return {"query": query, "words": words, "total_matches": len(hits), "results": hits[:limit]}


def _find_page(root: Path, page: str) -> Path:
    wanted = str(page).strip().replace("\\", "/").removesuffix(".md").strip("/").lower()
    if not wanted or ".." in wanted.split("/"):
        raise KnowledgeError(f"invalid page name {page!r}")
    pages = {_page_id(root, p).lower(): p for p in _pages(root)}
    if wanted in pages:
        return pages[wanted]
    close = [i for i in pages if wanted in i or i in wanted][:5]
    raise KnowledgeError(f"no page {page!r}; known pages: {sorted(pages)} (similar: {close})")


def read_page(page: str, section: str | None = None) -> dict:
    """Return a whole page, or one section (with its sub-sections) matched by heading text."""
    root = knowledge_root()
    path = _find_page(root, page)
    lines = _read(path)
    secs = _sections(lines)
    if section is None:
        start, end, chosen = 0, len(lines), None
    else:
        want = str(section).strip().lower()
        exact = [s for s in secs if s.title.lower() == want or s.heading.lower() == want]
        loose = [s for s in secs if want and want in s.heading.lower()]
        picks = exact or loose
        if not picks:
            raise KnowledgeError(
                f"no section {section!r} in {page!r}; sections: {[s.heading for s in secs]}"
            )
        chosen = picks[0]
        start, end = chosen.line - 1, chosen.end
    text = "\n".join(lines[start:end])
    truncated = len(text) > MAX_READ_CHARS
    return {
        "page": _page_id(root, path),
        "section": chosen.heading if chosen else None,
        "other_matching_sections": [s.heading for s in picks[1:]] if chosen else [],
        "first_line": start + 1,
        "text": text[:MAX_READ_CHARS],
        "truncated": truncated,
        "sections": [s.heading for s in secs] if section is None else None,
    }
