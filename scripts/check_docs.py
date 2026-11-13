"""Check maintained documentation without network access or a Live connection.

Usage: python scripts/check_docs.py [--root CHECKOUT]
Dated release notes/manifests are historical records and are not rewritten or audited.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

DOCUMENTS = (
    "README.md", "CONTRIBUTING.md", "SECURITY.md", "CODE_OF_CONDUCT.md",
    "docs/setup.md", "docs/usage.md", "docs/permissions.md", "docs/validation.md",
)
CLIENTS = ("claude", "codex", "opencode")


def anchors(text: str) -> set[str]:
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    result = set()
    counts: dict[str, int] = {}
    for heading in re.findall(r"^#{1,6} (.+)$", text, re.M):
        slug = re.sub(r"[^\w -]", "", heading.lower()).replace(" ", "-")
        count = counts.get(slug, 0)
        result.add(f"{slug}-{count}" if count else slug)
        counts[slug] = count + 1
    return result


def check(root: Path) -> list[str]:
    errors = []
    texts = {name: (root / name).read_text(encoding="utf-8") for name in DOCUMENTS}
    for name, text in texts.items():
        if text.count("```") % 2:
            errors.append(f"{name}: unclosed code fence")
        targets = re.findall(r"\]\(([^)]+)\)", text)
        targets += re.findall(r'<img\b[^>]*\bsrc="([^"]+)"', text)
        for target in targets:
            parsed = urlsplit(target)
            if parsed.scheme or parsed.netloc:
                continue
            linked = (root / name).parent / unquote(parsed.path) if parsed.path else root / name
            if not linked.exists():
                errors.append(f"{name}: missing link target {target}")
            elif parsed.fragment and linked.suffix == ".md":
                if unquote(parsed.fragment) not in anchors(linked.read_text(encoding="utf-8")):
                    errors.append(f"{name}: missing anchor {target}")
        if name in ("README.md", "docs/setup.md"):
            for block in re.findall(r"```json\n(.*?)\n```", text, re.S):
                try:
                    json.loads(block)
                except json.JSONDecodeError as exc:
                    errors.append(f"{name}: invalid JSON example: {exc}")

    for client in CLIENTS:
        pattern = rf"^{client} mcp add .+$"
        readme = set(re.findall(pattern, texts["README.md"], re.M))
        setup = set(re.findall(pattern, texts["docs/setup.md"], re.M))
        if len(readme) != 1 or readme != setup:
            errors.append(f"{client}: README and setup registration commands must match")

    metadata = (root / "pyproject.toml").read_text(encoding="utf-8")
    package = re.search(r'^name = "([^"]+)"', metadata, re.M)
    installs = re.findall(r"^pip install ([\w-]+)$", texts["README.md"], re.M)
    if not package or installs != [package[1]]:
        errors.append("README pip install must use the distribution name from pyproject.toml")
    for command in ("abletonlivemcp", "abletonlivemcp-install"):
        if not re.search(rf'^{re.escape(command)} = "', metadata, re.M):
            errors.append(f"Documented executable missing from package scripts: {command}")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    errors = check(args.root)
    if errors:
        raise SystemExit("Documentation checks failed:\n" + "\n".join(errors))
    print(
        f"Documentation checks passed: {len(DOCUMENTS)} files, links, examples and client commands"
    )


if __name__ == "__main__":
    main()
