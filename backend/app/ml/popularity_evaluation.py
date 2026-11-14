"""Evaluation helpers for the item popularity clustering model."""
from collections import Counter
import numpy as np
from sklearn.metrics import silhouette_score, davies_bouldin_score
from .popularity_analysis import _feature_matrix, assign_popularity_clusters


def evaluate_popularity_rows(rows: list[dict], requested_clusters: int = 3) -> dict:
    if not rows:
        return {"evaluated": False, "reason": "No item activity available.",
                "item_count": 0, "clusters": []}
    labelled = assign_popularity_clusters([dict(row) for row in rows], requested_clusters)
    matrix = _feature_matrix(labelled)
    labels = [row["cluster_id"] for row in labelled]
    counts = Counter(labels)
    unique_labels = len(counts)
    unique_points = len(np.unique(matrix, axis=0))
    silhouette = None
    davies_bouldin = None
    reason = None

    if unique_labels < 2:
        reason = "At least two non-empty clusters are required."
    elif unique_labels >= len(labelled):
        reason = "Every item is in its own cluster; metrics are undefined."
    elif unique_points < 2:
        reason = "All items have identical activity features."
    else:
        try:
            silhouette = float(silhouette_score(matrix, labels))
            davies_bouldin = float(davies_bouldin_score(matrix, labels))
        except ValueError as exc:
            reason = str(exc)

    cluster_rows = []
    for cluster_id, count in sorted(counts.items()):
        members = [row for row in labelled if row["cluster_id"] == cluster_id]
        cluster_rows.append({
            "cluster_id": int(cluster_id),
            "group": members[0]["popularity_group"],
            "item_count": count,
            "item_names": [row["name"] for row in members],
            "total_issues": sum(row["issue_count"] for row in members),
        })
    return {
        "evaluated": silhouette is not None,
        "item_count": len(labelled),
        "requested_clusters": requested_clusters,
        "actual_clusters": unique_labels,
        "silhouette_score": round(silhouette, 4) if silhouette is not None else None,
        "davies_bouldin_score": round(davies_bouldin, 4) if davies_bouldin is not None else None,
        "reason": reason,
        "clusters": cluster_rows,
        "metric_guide": {
            "silhouette": "Closer to 1 indicates better separated clusters.",
            "davies_bouldin": "Lower values generally indicate tighter clusters.",
        },
    }


def popularity_quality_label(report: dict) -> str:
    score = report.get("silhouette_score")
    if score is None:
        return "not_evaluated"
    if score >= 0.50:
        return "well_separated"
    if score >= 0.25:
        return "moderately_separated"
    return "weakly_separated"
