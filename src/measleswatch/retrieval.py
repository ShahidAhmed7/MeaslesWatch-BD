"""Source-hash-checked lexical retrieval; no embeddings, private gold, or network."""
from pathlib import Path
import hashlib
import json
import re

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer


class EvidenceStore:
    def __init__(self, public_split):
        self.root = Path(public_split).resolve()
        manifest = json.loads((self.root / "source_manifest.json").read_text())
        self.sources, self.chunks = {}, []
        for source in manifest["sources"]:
            path = self.root / "sources" / f"{source['source_id']}.md"
            if not path.resolve().is_relative_to(self.root):
                raise ValueError("Source path escapes public evidence bundle")
            raw = path.read_bytes()
            if hashlib.sha256(raw).hexdigest() != source["sha256"]:
                raise ValueError(f"Source hash mismatch: {source['source_id']}")
            text = raw.decode()
            self.sources[source["source_id"]] = {**source, "text": text, "lines": text.splitlines()}
            lines = text.splitlines()
            for first in range(0, len(lines), 25):
                last = min(first + 30, len(lines))
                body = "\n".join(lines[first:last])
                if body.strip():
                    self.chunks.append({"source_id": source["source_id"], "line_start": first + 1,
                                        "line_end": last, "text": body, "source_sha256": source["sha256"]})
        self.vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), sublinear_tf=True)
        self.matrix = self.vectorizer.fit_transform([c["text"] for c in self.chunks])

    def retrieve(self, question, source_ids=None, top_k=4):
        allowed = set(source_ids or self.sources)
        scores = (self.matrix @ self.vectorizer.transform([question]).T).toarray().ravel()
        indices = sorted([i for i, c in enumerate(self.chunks) if c["source_id"] in allowed],
                         key=lambda i: (-scores[i], i))[:top_k]
        return [{**self.chunks[i], "retrieval_score": float(scores[i])} for i in indices]

    def full_sources(self, source_ids):
        return [{"source_id": s, "url": self.sources[s]["url"],
                 "sha256": self.sources[s]["sha256"],
                 "numbered_text": "\n".join(f"{i}: {line}" for i, line in enumerate(self.sources[s]["lines"], 1))}
                for s in source_ids]

    def valid_citation(self, citation):
        if not isinstance(citation, dict):
            return False
        source = self.sources.get(citation.get("source_id"))
        a, b = citation.get("line_start"), citation.get("line_end")
        return bool(source and type(a) is int and type(b) is int and 1 <= a <= b <= len(source["lines"]))


def lexical_terms(text):
    return set(re.findall(r"[a-z0-9]+", text.lower()))
