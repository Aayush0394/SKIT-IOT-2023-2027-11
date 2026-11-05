"""Frequency-based item popularity scoring and clustering."""
from datetime import timedelta
import numpy as np
from sklearn.cluster import KMeans
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..models import Item, Transaction, utcnow


def collect_item_activity(db: Session, days: int = 30) -> list[dict]:
    """Collect issue frequency and distinct borrower activity per item."""
    cutoff = utcnow() - timedelta(days=days)
    items = db.scalars(select(Item).order_by(Item.id)).all()
    transactions = db.scalars(select(Transaction).where(Transaction.issued_at >= cutoff)).all()
    stats = {item.id: {"issues": 0, "users": set(), "recent_issues": 0} for item in items}
    recent_cutoff = utcnow() - timedelta(days=max(1, days // 3))
    for tx in transactions:
        row = stats.get(tx.item_id)
        if row is None:
            continue
        row["issues"] += 1
        row["users"].add(tx.user_id)
        if tx.issued_at >= recent_cutoff:
            row["recent_issues"] += 1
    output = []
    for item in items:
        row = stats[item.id]
        output.append({
            "item_id": item.id, "name": item.name, "category": item.category,
            "issue_count": row["issues"], "unique_borrowers": len(row["users"]),
            "recent_issues": row["recent_issues"],
            "quantity_available": item.quantity_available,
        })
    return output


def _feature_matrix(rows: list[dict]) -> np.ndarray:
    """Normalize raw activity into three numeric clustering dimensions."""
    if not rows:
        return np.empty((0, 3), dtype=float)
    return np.asarray([[row["issue_count"], row["unique_borrowers"],
                        row["recent_issues"]] for row in rows], dtype=float)


def assign_popularity_clusters(rows: list[dict], clusters: int = 3) -> list[dict]:
    """Assign low/medium/high groups; safely handle small or empty inventories."""
    if not rows:
        return []
    matrix = _feature_matrix(rows)
    unique_count = len(np.unique(matrix, axis=0))
    cluster_count = min(max(1, clusters), len(rows), unique_count)
    if cluster_count == 1:
        labels = np.zeros(len(rows), dtype=int)
    else:
        model = KMeans(n_clusters=cluster_count, random_state=42, n_init=10)
        labels = model.fit_predict(matrix)
    activity = {label: float(matrix[labels == label].sum()) for label in set(labels)}
    ordered = sorted(activity, key=activity.get)
    names = {label: "low" for label in ordered}
    if len(ordered) >= 2:
        names[ordered[-1]] = "high"
        for label in ordered[1:-1]:
            names[label] = "medium"
    for index, row in enumerate(rows):
        row["popularity_group"] = names[int(labels[index])]
        row["cluster_id"] = int(labels[index])
    return rows


def popularity_report(db: Session, days: int = 30, clusters: int = 3) -> dict:
    rows = collect_item_activity(db, days)
    labelled = assign_popularity_clusters(rows, clusters)
    labelled.sort(key=lambda row: (row["issue_count"], row["unique_borrowers"]), reverse=True)
    return {
        "period_days": days,
        "algorithm": "kmeans_frequency_analysis",
        "item_count": len(labelled),
        "popular_items": [row for row in labelled if row["popularity_group"] == "high"],
        "items": labelled,
    }
