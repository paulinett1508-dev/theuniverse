import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "oraculo"))

from rag import tokenize, chunk_text, Rag


def test_tokenize_lowercases_and_splits():
    assert tokenize("Zion, PostgreSQL!") == ["zion", "postgresql"]


def test_chunk_text_splits_on_blank_lines():
    chunks = chunk_text("a" * 500 + "\n\n" + "b" * 500, "f.md", max_chars=800)
    assert len(chunks) == 2
    assert all(c["source"] == "f.md" for c in chunks)


def test_retrieve_ranks_relevant_first(tmp_path):
    (tmp_path / "zion.md").write_text("O planeta Zion roda no banco PostgreSQL.", encoding="utf-8")
    (tmp_path / "frota.md").write_text("Texto sobre frota de estrelas e cosmologia.", encoding="utf-8")
    (tmp_path / "censo.md").write_text("O Censo varre os planetas e atualiza fichas.", encoding="utf-8")
    rag = Rag.from_paths([str(tmp_path)])
    hits = rag.retrieve("qual banco de dados do zion", k=2)
    assert hits
    assert "PostgreSQL" in hits[0]["text"]


def test_retrieve_empty_index_returns_empty():
    assert Rag([]).retrieve("qualquer", k=3) == []
