"""
Full-text search utilities for HHD-HY Survey App.

Algorithm design:
  - Inverted index pattern (GeeksforGeeks / LeetCode hash-map approach)
  - TF-IDF scoring for result ranking (Papers With Code NLP basics)
  - Fuzzy matching with Levenshtein distance (HackerRank string algorithms)

Reference: GeeksforGeeks — Inverted Index, TF-IDF
"""

from __future__ import annotations
import re
import math
from collections import defaultdict
from typing import Any


# ─── Text normaliser ──────────────────────────────────────────────────────────

def _tokenise(text: str) -> list[str]:
    """Lowercase, strip diacritics-safe tokenisation (handles Vietnamese)."""
    if not isinstance(text, str):
        text = str(text)
    # Keep unicode letters and digits, split on everything else
    return re.findall(r'\w+', text.lower())


def _normalise(text: str) -> str:
    return " ".join(_tokenise(text))


# ─── Levenshtein distance (GeeksforGeeks DP approach) ─────────────────────────

def levenshtein(s1: str, s2: str) -> int:
    """
    Classic DP Levenshtein distance.
    Time: O(m·n)   Space: O(min(m,n))  — two-row optimisation.
    """
    if s1 == s2:
        return 0
    if len(s1) < len(s2):
        s1, s2 = s2, s1
    prev = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1, 1):
        curr = [i]
        for j, c2 in enumerate(s2, 1):
            curr.append(min(prev[j] + 1,       # deletion
                            curr[j - 1] + 1,   # insertion
                            prev[j - 1] + (0 if c1 == c2 else 1)))  # substitution
        prev = curr
    return prev[-1]


def fuzzy_match(query: str, target: str, max_dist: int = 2) -> bool:
    """Return True if any token in `target` is within `max_dist` edits of `query`."""
    q = query.lower().strip()
    for tok in _tokenise(target):
        if levenshtein(q, tok) <= max_dist:
            return True
    return False


# ─── In-memory TF-IDF index ───────────────────────────────────────────────────

class SurveySearchIndex:
    """
    Lightweight inverted-index over survey/response text for fast search.

    Build once, query many times (cache in st.session_state).
    """

    def __init__(self) -> None:
        # doc_id → raw document dict
        self._docs: dict[str, dict] = {}
        # token → {doc_id: term_freq}
        self._index: dict[str, dict[str, float]] = defaultdict(dict)
        # doc_id → total token count
        self._doc_len: dict[str, int] = {}

    # ── Build ──────────────────────────────────────────────────────────────────

    def add_document(self, doc_id: str, doc: dict, fields: list[str]) -> None:
        """Index a document by extracting text from `fields`."""
        self._docs[doc_id] = doc
        text = " ".join(str(doc.get(f, "")) for f in fields)
        tokens = _tokenise(text)
        self._doc_len[doc_id] = len(tokens) or 1
        # Term frequency
        tf: dict[str, int] = defaultdict(int)
        for tok in tokens:
            tf[tok] += 1
        for tok, cnt in tf.items():
            self._index[tok][doc_id] = cnt / self._doc_len[doc_id]

    def build_from_surveys(self, surveys: list[dict]) -> None:
        for s in surveys:
            self.add_document(
                s["uuid"],
                s,
                fields=["title", "description"],
            )

    def build_from_responses(self, responses: list[dict], survey_title: str = "") -> None:
        for i, r in enumerate(responses):
            doc = {"_idx": i, "_survey": survey_title}
            doc.update(r.get("response_data", {}))
            self.add_document(str(i), doc, fields=list(doc.keys()))

    # ── Query ─────────────────────────────────────────────────────────────────

    def search(self, query: str, top_k: int = 50, fuzzy: bool = True) -> list[tuple[str, float]]:
        """
        BM25-lite scoring (simplified TF·IDF).
        Returns list of (doc_id, score) sorted by score descending.

        BM25 reference: Robertson & Zaragoza, 2009 — commonly cited on
        Papers With Code retrieval benchmarks.
        """
        tokens = _tokenise(query)
        if not tokens:
            return []

        N = len(self._docs)
        if N == 0:
            return []

        scores: dict[str, float] = defaultdict(float)
        k1, b = 1.5, 0.75
        avg_len = sum(self._doc_len.values()) / N

        for tok in tokens:
            # Exact match
            matched_docs = dict(self._index.get(tok, {}))

            # Fuzzy expansion (Levenshtein ≤ 1 for short tokens, ≤ 2 otherwise)
            if fuzzy and tok not in self._index:
                threshold = 1 if len(tok) <= 4 else 2
                for idx_tok, idx_docs in self._index.items():
                    if levenshtein(tok, idx_tok) <= threshold:
                        for doc_id, tf in idx_docs.items():
                            matched_docs[doc_id] = matched_docs.get(doc_id, 0) + tf * 0.5

            # IDF
            df = len(matched_docs)
            if df == 0:
                continue
            idf = math.log((N - df + 0.5) / (df + 0.5) + 1)

            for doc_id, tf in matched_docs.items():
                dl = self._doc_len.get(doc_id, 1)
                tf_norm = tf * (k1 + 1) / (tf + k1 * (1 - b + b * dl / avg_len))
                scores[doc_id] += idf * tf_norm

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return ranked[:top_k]

    def get_doc(self, doc_id: str) -> dict | None:
        return self._docs.get(doc_id)

    def __len__(self) -> int:
        return len(self._docs)


# ─── Convenience helpers ──────────────────────────────────────────────────────

def search_responses(
    responses: list[dict],
    query: str,
    top_k: int = 200,
) -> list[int]:
    """
    Search responses by query string.
    Returns list of original indices sorted by relevance.
    Falls back to simple substring match when query is very short.
    """
    if not query or not responses:
        return list(range(len(responses)))

    query = query.strip()

    # For very short queries use fast substring filter
    if len(query) <= 2:
        q_low = query.lower()
        return [
            i for i, r in enumerate(responses)
            if q_low in str(r).lower()
        ]

    idx = SurveySearchIndex()
    idx.build_from_responses(responses)
    ranked = idx.search(query, top_k=top_k)
    return [int(doc_id) for doc_id, _ in ranked if int(doc_id) < len(responses)]


def search_surveys(surveys: list[dict], query: str) -> list[dict]:
    """Search surveys by title/description. Returns filtered+ranked list."""
    if not query or not surveys:
        return surveys
    idx = SurveySearchIndex()
    idx.build_from_surveys(surveys)
    ranked = idx.search(query, top_k=len(surveys))
    result = []
    seen = set()
    for doc_id, _ in ranked:
        doc = idx.get_doc(doc_id)
        if doc and doc_id not in seen:
            result.append(doc)
            seen.add(doc_id)
    return result
