"""Theme clustering for CommentPulse.

Uses TF-IDF + KMeans for deterministic clustering, then applies keyword-based
category classification (question, pain, objection, praise, urgent-support).
"""

import re
import sqlite3
from collections import Counter
from typing import Optional

import numpy as np
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer

from .db import (
    get_comments,
    add_theme,
    assign_theme,
)


# Category keyword signals — order matters (first match wins)
CATEGORY_SIGNALS = [
    ("urgent-support", [
        r"\bhelp\b", r"\bugent\b", r"\berror\b", r"\bcrash\b", r"\bnot working\b",
        r"\bstuck\b", r"\bcan'?t\b", r"\bbroken\b", r"\bplease\b",
    ]),
    ("question", [
        r"\?", r"\bhow (do|to|can)\b", r"\bwhat\b", r"\bwhy\b", r"\bwhen\b",
        r"\bwhere\b", r"\bcan (you|i)\b", r"\bis (it|there)\b",
    ]),
    ("objection", [
        r"\btoo expensive\b", r"\btoo hard\b", r"\bnot worth\b", r"\bwhy would\b",
        r"\bwouldn'?t use\b", r"\bdon'?t (need|want|like)\b", r"\bprefer\b",
    ]),
    ("pain", [
        r"\bstruggle\b", r"\bfrustrat\w*\b", r"\bannoy\w*\b", r"\bwish\b",
        r"\bif only\b", r"\bproblem\b", r"\bissue\b", r"\btoo (slow|complex|much)\b",
        r"\bconfus\w*\b", r"\boverwhelm\w*\b",
    ]),
    ("praise", [
        r"\blove\b", r"\bgreat\b", r"\bawesome\b", r"\bamazing\b", r"\bthank\w*\b",
        r"\bperfect\b", r"\bbrilliant\b", r"\buseful\b", r"\bhelpful\b",
    ]),
]


def classify_category(text: str) -> str:
    """Classify a comment into a category based on keyword signals."""
    lower = text.lower()
    for category, patterns in CATEGORY_SIGNALS:
        for pat in patterns:
            if re.search(pat, lower):
                return category
    return "general"


def cluster_comments(conn: sqlite3.Connection, n_clusters: int = 5,
                     source_id: Optional[int] = None) -> list[dict]:
    """Cluster comments using TF-IDF + KMeans, create themes, and assign comments.

    Returns a list of created themes with stats.
    """
    comments = get_comments(conn, source_id=source_id)
    if len(comments) < 3:
        # Too few comments for meaningful clustering — single theme
        theme_id = add_theme(conn, label="All comments", category="general",
                             summary="Not enough comments for clustering.",
                             confidence=0.3)
        for c in comments:
            assign_theme(conn, c["id"], theme_id)
        return [{"theme_id": theme_id, "label": "All comments", "comment_count": len(comments)}]

    texts = [c["text"] for c in comments]

    # TF-IDF vectorization
    vectorizer = TfidfVectorizer(
        max_features=500,
        stop_words="english",
        ngram_range=(1, 2),
        min_df=1,
    )
    tfidf_matrix = vectorizer.fit_transform(texts)

    # Adjust cluster count if we have fewer comments than requested
    actual_clusters = min(n_clusters, len(comments) // 2) or 1

    # KMeans clustering
    km = KMeans(n_clusters=actual_clusters, random_state=42, n_init=10)
    labels = km.fit_predict(tfidf_matrix)

    # Get top terms per cluster for labels
    feature_names = vectorizer.get_feature_names_out()
    themes_created = []

    for cluster_idx in range(actual_clusters):
        cluster_mask = labels == cluster_idx
        cluster_comments = [comments[i] for i in range(len(comments)) if cluster_mask[i]]
        cluster_texts = [texts[i] for i in range(len(comments)) if cluster_mask[i]]

        if not cluster_comments:
            continue

        # Top terms for this cluster
        cluster_center = km.cluster_centers_[cluster_idx]
        top_indices = cluster_center.argsort()[-5:][::-1]
        top_terms = [feature_names[i] for i in top_indices]
        label = " / ".join(top_terms[:3])

        # Dominant category
        categories = [classify_category(t) for t in cluster_texts]
        category = Counter(categories).most_common(1)[0][0]

        # Confidence = fraction of comments in dominant category
        confidence = categories.count(category) / len(categories)

        theme_id = add_theme(
            conn,
            label=label,
            category=category,
            summary=f"Cluster of {len(cluster_comments)} comments about: {', '.join(top_terms)}",
            confidence=round(confidence, 2),
        )

        for c in cluster_comments:
            assign_theme(conn, c["id"], theme_id)

        themes_created.append({
            "theme_id": theme_id,
            "label": label,
            "category": category,
            "comment_count": len(cluster_comments),
            "confidence": round(confidence, 2),
            "top_terms": top_terms,
        })

    return themes_created
