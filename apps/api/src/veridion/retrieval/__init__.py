"""Evidence retrieval: BM25 keyword scoring plus requirement-aware signals.

The retriever is deliberately transparent: every result explains why it matched
(query terms, exact phrases, extracted metrics, section headings). Semantic
embeddings can be added behind the same interface if the evaluation suite shows
they improve recall.
"""

from __future__ import annotations

import math
import re
import unicodedata
from collections import Counter
from dataclasses import dataclass, field

_TOKEN = re.compile(r"[a-z0-9]+")
STOPWORDS = frozenset(
    ["a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has", "have", "in", "into", "is", "it", "its", "of", "on", "or", "our", "that", "the", "their", "this", "to", "was", "were", "which", "with", "we", "us", "than", "then", "these", "those", "also", "been", "being", "per", "such", "not", "no"]
)
# per/not/no are stopwords for scoring but phrase matching still sees the raw text.


def _stem(token: str) -> str:
    if len(token) > 4 and token.endswith("ies"):
        return token[:-3] + "y"
    if len(token) > 4 and token.endswith("es") and token[-3] in "sxz":
        return token[:-2]
    if len(token) > 3 and token.endswith("s") and not token.endswith("ss"):
        return token[:-1]
    return token


def tokenize(text: str) -> list[str]:
    folded = unicodedata.normalize("NFKC", text).lower().replace("co₂", "co2")
    return [_stem(t) for t in _TOKEN.findall(folded) if t not in STOPWORDS]


@dataclass
class Doc:
    id: str
    text: str
    section: str | None = None
    kind: str = "paragraph"
    metric_keys: frozenset[str] = frozenset()


@dataclass
class Hit:
    id: str
    score: float
    bm25: float
    terms: list[str] = field(default_factory=list)
    phrases: list[str] = field(default_factory=list)
    metrics: list[str] = field(default_factory=list)
    section_match: bool = False

    def explanation(self) -> dict:
        return {
            "score": round(self.score, 3),
            "bm25": round(self.bm25, 3),
            "terms": self.terms,
            "phrases": self.phrases,
            "metrics": self.metrics,
            "section_match": self.section_match,
        }


KIND_WEIGHT = {"heading": 0.35, "table": 0.6, "table_row": 1.0, "paragraph": 1.0, "list_item": 1.0}


class BM25Index:
    def __init__(self, docs: list[Doc], k1: float = 1.4, b: float = 0.75) -> None:
        self.docs = docs
        self.k1, self.b = k1, b
        self.tokens = [tokenize(d.text) for d in docs]
        self.tf = [Counter(t) for t in self.tokens]
        self.lengths = [len(t) for t in self.tokens]
        self.avgdl = (sum(self.lengths) / len(self.lengths)) if docs else 1.0
        df: Counter[str] = Counter()
        for tokens in self.tokens:
            df.update(set(tokens))
        n = len(docs)
        self.idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}

    def bm25(self, index: int, query: list[str]) -> tuple[float, list[str]]:
        tf = self.tf[index]
        length = self.lengths[index] or 1
        score = 0.0
        matched = []
        for term in set(query):
            f = tf.get(term)
            if not f:
                continue
            idf = self.idf.get(term, 0.0)
            score += idf * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * length / self.avgdl))
            matched.append(term)
        return score, sorted(matched)

    def search(self, query: str, *, phrases: list[str] | None = None, metric_keys: set[str] | None = None,
               section_terms: list[str] | None = None, limit: int = 10, min_score: float = 0.0) -> list[Hit]:
        q_tokens = tokenize(query)
        phrase_list = [p.lower() for p in (phrases or []) if len(p.split()) >= 1]
        raw: list[tuple[int, float, list[str]]] = []
        for i in range(len(self.docs)):
            s, terms = self.bm25(i, q_tokens)
            raw.append((i, s, terms))
        top_bm25 = max((s for _, s, _ in raw), default=0.0) or 1.0

        hits: list[Hit] = []
        for i, s, terms in raw:
            doc = self.docs[i]
            lowered = doc.text.lower()
            matched_phrases = [p for p in phrase_list if p in lowered]
            matched_metrics = sorted(doc.metric_keys & metric_keys) if metric_keys else []
            section_match = bool(section_terms and doc.section and any(
                t.lower() in doc.section.lower() for t in section_terms))
            score = 0.6 * (s / top_bm25)
            score += min(0.45, 0.15 * len(matched_phrases))
            score += 0.5 if matched_metrics else 0.0
            score += 0.1 if section_match else 0.0
            score *= KIND_WEIGHT.get(doc.kind, 1.0)
            if score <= min_score or (s == 0 and not matched_phrases and not matched_metrics):
                continue
            hits.append(Hit(doc.id, score, s, terms, matched_phrases, matched_metrics, section_match))
        hits.sort(key=lambda h: (-h.score, h.id))
        return hits[:limit]
