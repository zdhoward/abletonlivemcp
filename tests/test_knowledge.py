"""Knowledge reader contract, against a tiny synthetic page. Never reads the repo's knowledge/."""

import pytest

from abletonlivemcp import knowledge

PAGE = """# Synthetic Page

Intro line about widgets.

## Alpha targets

Set the widget to 7 units. UNVERIFIED note.

### Detail

Fine print about gadgets.

## Beta

Nothing about the first topic here.
"""


@pytest.fixture
def kb(tmp_path, monkeypatch):
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "synthetic.md").write_text(PAGE, encoding="utf8")
    monkeypatch.setenv("ABLETONLIVEMCP_KNOWLEDGE", str(tmp_path))
    return tmp_path


def test_list_search_and_read_use_only_the_configured_folder(kb):
    assert knowledge.knowledge_root() == kb and knowledge.available()
    (page,) = knowledge.list_pages()
    assert page["page"] == "sub/synthetic" and page["title"] == "Synthetic Page"
    assert page["sections"] == 4 and page["unconfirmed_tags"] == 1

    top = knowledge.search("widget units", 3)["results"][0]
    assert top["page"] == "sub/synthetic" and top["section"].endswith("Alpha targets")
    assert top["all_words"]

    section = knowledge.read_page("sub/synthetic", "Alpha targets")
    assert "7 units" in section["text"] and "gadgets" in section["text"]  # sub-section included
    assert "Nothing about" not in section["text"]


def test_bad_requests_are_refused(kb):
    with pytest.raises(knowledge.KnowledgeError):
        knowledge.read_page("../pyproject")
    with pytest.raises(knowledge.KnowledgeError, match="no section"):
        knowledge.read_page("sub/synthetic", "Missing")
    with pytest.raises(knowledge.KnowledgeError):
        knowledge.search("a")  # no word of 2+ characters
    with pytest.raises(knowledge.KnowledgeError, match="limit"):
        knowledge.search("widget", 0)


def test_missing_folder_is_reported(tmp_path, monkeypatch):
    monkeypatch.setenv("ABLETONLIVEMCP_KNOWLEDGE", str(tmp_path / "absent"))
    assert not knowledge.available()
    with pytest.raises(knowledge.KnowledgeError, match="not found"):
        knowledge.list_pages()
