"""RAG BM25 sobre os markdowns do universo."""
import re
from pathlib import Path

from rank_bm25 import BM25Okapi


def tokenize(text):
    return re.findall(r"[a-z0-9]+", text.lower())


def chunk_text(text, source, max_chars=800):
    chunks, buf = [], ""
    for para in text.split("\n\n"):
        para = para.strip()
        if not para:
            continue
        if buf and len(buf) + len(para) > max_chars:
            chunks.append({"source": source, "text": buf.strip()})
            buf = para
        else:
            buf = f"{buf}\n\n{para}" if buf else para
    if buf.strip():
        chunks.append({"source": source, "text": buf.strip()})
    return chunks


class Rag:
    def __init__(self, chunks):
        self.chunks = chunks
        self._bm25 = BM25Okapi([tokenize(c["text"]) for c in chunks]) if chunks else None

    @classmethod
    def from_paths(cls, paths, exts=(".md",)):
        chunks = []
        for raw in paths:
            p = Path(raw)
            if p.is_file():
                files = [(p, p.name)]
            elif p.is_dir():
                files = [(f, str(f.relative_to(p))) for f in p.rglob("*")
                         if f.is_file() and f.suffix.lower() in exts]
            else:
                files = []
            for f, name in files:
                if f.suffix.lower() in exts:
                    chunks.extend(chunk_text(f.read_text(encoding="utf-8", errors="ignore"), name))
        return cls(chunks)

    def retrieve(self, query, k=5):
        if not self._bm25:
            return []
        scores = self._bm25.get_scores(tokenize(query))
        ranked = sorted(zip(scores, self.chunks), key=lambda x: x[0], reverse=True)
        return [c for s, c in ranked[:k] if s > 0]
