"""
NLP utility functions for HHD-HY Survey App.

Techniques:
  - Word frequency / word-cloud generation (no heavy ML deps required)
  - Vietnamese + English stopword filtering
  - N-gram extraction (bigrams) — standard NLP practice
  - Sentiment word scoring (simple lexicon approach, Papers With Code baseline)

References:
  - Hugging Face / Papers With Code — NLP pre-processing patterns
  - GeeksforGeeks — Word frequency algorithms
  - NLTK documentation — Tokenisation, n-gram patterns
"""

from __future__ import annotations
import re
import json
from collections import Counter


# ─── Stopwords (Vietnamese + English) ────────────────────────────────────────

_VI_STOPWORDS = frozenset([
    "và", "của", "là", "có", "trong", "với", "không", "được", "để", "cho",
    "các", "một", "những", "này", "đó", "từ", "về", "đã", "sẽ", "hay",
    "nhưng", "mà", "thì", "cũng", "vì", "nếu", "như", "khi", "bởi", "tại",
    "theo", "đến", "bằng", "lên", "xuống", "ra", "vào", "hơn", "nên", "chỉ",
    "hoặc", "lại", "sau", "trước", "đây", "tôi", "bạn", "họ", "chúng", "ta",
    "rất", "nhiều", "ít", "vẫn", "đang", "đó", "đây", "ai", "gì", "nào",
])

_EN_STOPWORDS = frozenset([
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "should",
    "could", "may", "might", "shall", "can", "need", "dare", "ought",
    "i", "you", "he", "she", "it", "we", "they", "me", "him", "her", "us",
    "them", "my", "your", "his", "its", "our", "their", "this", "that",
    "these", "those", "and", "but", "or", "nor", "for", "yet", "so",
    "in", "on", "at", "to", "of", "up", "by", "as", "not", "no", "yes",
    "with", "from", "into", "about", "more", "also", "than", "then",
])

STOPWORDS = _VI_STOPWORDS | _EN_STOPWORDS


# ─── Tokeniser ────────────────────────────────────────────────────────────────

def tokenise(text: str, min_len: int = 2) -> list[str]:
    """Unicode-aware tokeniser — keeps Vietnamese characters."""
    tokens = re.findall(r'\w+', text.lower())
    return [t for t in tokens if len(t) >= min_len and t not in STOPWORDS]


# ─── Word frequency ───────────────────────────────────────────────────────────

def word_frequency(texts: list[str], top_n: int = 50, min_len: int = 2) -> list[tuple[str, int]]:
    """
    Count word frequencies across a list of text strings.
    Returns top_n (word, count) tuples sorted by frequency.
    """
    counter: Counter = Counter()
    for text in texts:
        if not isinstance(text, str):
            continue
        counter.update(tokenise(text, min_len=min_len))
    return counter.most_common(top_n)


# ─── Bigram extraction ────────────────────────────────────────────────────────

def extract_bigrams(texts: list[str], top_n: int = 30) -> list[tuple[str, int]]:
    """Extract most common adjacent word pairs (bigrams)."""
    counter: Counter = Counter()
    for text in texts:
        tokens = tokenise(text)
        for i in range(len(tokens) - 1):
            counter[(tokens[i], tokens[i + 1])] += 1
    return [(" ".join(bg), cnt) for bg, cnt in counter.most_common(top_n)]


# ─── Simple word-cloud data builder ───────────────────────────────────────────

def build_wordcloud_data(
    texts: list[str], top_n: int = 60
) -> list[dict]:
    """
    Build word-cloud data (list of {text, value} dicts) suitable for
    a Plotly treemap or st.dataframe display when wordcloud lib is not available.
    """
    freq = word_frequency(texts, top_n=top_n)
    if not freq:
        return []
    max_cnt = freq[0][1]
    return [
        {"text": word, "value": cnt, "size": round(10 + 30 * cnt / max_cnt)}
        for word, cnt in freq
    ]


# ─── Sentiment scoring (simple positive/negative lexicon) ─────────────────────
# Minimal lexicon — covers common Vietnamese survey sentiment words.
# Reference: Papers With Code sentiment baselines (VADER-style approach).

_POS_VI = frozenset([
    "tốt", "xuất sắc", "tuyệt vời", "hài lòng", "ưng ý", "tốt lắm",
    "chất lượng", "hiệu quả", "nhanh", "chính xác", "đầy đủ", "thân thiện",
    "chuyên nghiệp", "dễ sử dụng", "tiện lợi", "phù hợp", "đồng ý",
    "thích", "yêu thích", "ủng hộ", "khuyến nghị", "tin tưởng",
])
_NEG_VI = frozenset([
    "kém", "tệ", "xấu", "chậm", "sai", "thiếu", "khó khăn", "phức tạp",
    "không hài lòng", "chưa tốt", "cần cải thiện", "không đồng ý",
    "không thích", "khó hiểu", "bất tiện", "không phù hợp",
])
_POS_EN = frozenset([
    "good", "great", "excellent", "satisfied", "happy", "helpful",
    "fast", "accurate", "complete", "friendly", "professional",
    "easy", "convenient", "suitable", "agree", "like", "love",
    "recommend", "trust", "efficient",
])
_NEG_EN = frozenset([
    "bad", "poor", "slow", "wrong", "missing", "difficult", "complex",
    "unsatisfied", "unhappy", "disagree", "dislike", "confusing",
    "inconvenient", "unsuitable", "needs improvement",
])


def sentiment_score(text: str) -> dict:
    """
    Returns {'positive': int, 'negative': int, 'neutral': bool, 'label': str}
    using a simple lexicon lookup.
    """
    text_lower = text.lower()
    pos = sum(1 for w in _POS_VI | _POS_EN if w in text_lower)
    neg = sum(1 for w in _NEG_VI | _NEG_EN if w in text_lower)
    label = "positive" if pos > neg else "negative" if neg > pos else "neutral"
    return {"positive": pos, "negative": neg, "neutral": pos == neg, "label": label}


def batch_sentiment(texts: list[str]) -> dict:
    """Aggregate sentiment over a list of texts."""
    counts = Counter()
    for text in texts:
        if not isinstance(text, str):
            continue
        counts[sentiment_score(text)["label"]] += 1
    total = sum(counts.values()) or 1
    return {
        "positive": counts["positive"],
        "negative": counts["negative"],
        "neutral": counts["neutral"],
        "total": total,
        "positive_pct": round(counts["positive"] / total * 100, 1),
        "negative_pct": round(counts["negative"] / total * 100, 1),
        "neutral_pct": round(counts["neutral"] / total * 100, 1),
    }
