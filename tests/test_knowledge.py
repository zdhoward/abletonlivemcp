import pytest

from abletonlivemcp import server


def test_knowledge_tools_find_and_read_the_real_pages():
    """Runs against the repo's real knowledge/ folder, not a fixture."""
    pages = {p["page"]: p for p in server.knowledge_list()["pages"]}
    assert {"vocals", "drums", "mastering"} <= set(pages)

    top = server.knowledge_search("spotify loudness true peak", 3)["results"][0]
    assert top["page"] == "mastering" and top["all_words"]

    text = server.knowledge_read("mastering", "Loudness and delivery targets")["text"]
    assert "-14 LUFS" in text

    with pytest.raises(ValueError):
        server.knowledge_read("../pyproject")
