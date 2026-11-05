"""Behaviour-based user classification: Premium, Regular or Risky.

Training labels are generated from transparent business rules because this
project currently has no manually labelled user dataset. Replace them with
reviewed labels when a real training dataset becomes available.
"""
from datetime import timedelta
import numpy as np
from sklearn.tree import DecisionTreeClassifier
from ..models import Transaction, utcnow
from sqlalchemy import select
from sqlalchemy.orm import Session

FEATURE_NAMES = ["transaction_count", "return_rate", "overdue_rate", "average_late_days"]
CLASS_NAMES = {0: "Regular", 1: "Premium", 2: "Risky"}


def _late_days(tx: Transaction) -> int:
    if tx.returned_at is None:
        end_date = utcnow().date()
    else:
        end_date = tx.returned_at.date()
    return max(0, (end_date - tx.due_at.date()).days)


def extract_user_features(db: Session, user_id: int, days: int = 180) -> dict:
    """Build user activity features from the relational transaction table."""
    cutoff = utcnow() - timedelta(days=days)
    rows = db.scalars(select(Transaction).where(
        Transaction.user_id == user_id, Transaction.issued_at >= cutoff
    )).all()
    total = len(rows)
    returned = [tx for tx in rows if tx.status == "returned"]
    overdue = [tx for tx in rows if tx.due_at < utcnow() and tx.status == "issued"]
    late_values = [_late_days(tx) for tx in returned]
    return {
        "transaction_count": total,
        "return_rate": len(returned) / total if total else 0.0,
        "overdue_rate": (len(overdue) + sum(1 for value in late_values if value > 0)) / total if total else 0.0,
        "average_late_days": float(np.mean(late_values)) if late_values else 0.0,
    }


def _rule_label(features: dict) -> int:
    """Create initial pseudo-labels for a small demonstrator model."""
    if features["overdue_rate"] >= 0.35 or features["average_late_days"] >= 5:
        return 2
    if features["transaction_count"] >= 8 and features["return_rate"] >= 0.8:
        return 1
    return 0


def _training_examples() -> tuple[np.ndarray, np.ndarray]:
    """Create representative examples so the classifier can run without labels."""
    examples = [
        [1, 0.5, 0.0, 0], [3, 1.0, 0.0, 0], [5, 0.8, 0.1, 1],
        [10, 0.9, 0.0, 0], [12, 1.0, 0.0, 0], [9, 0.95, 0.0, 0],
        [2, 0.5, 0.5, 6], [4, 0.5, 0.5, 8], [6, 0.7, 0.4, 5],
        [8, 0.6, 0.3, 2], [0, 0.0, 0.0, 0], [7, 0.8, 0.1, 0],
    ]
    labels = [_rule_label(dict(zip(FEATURE_NAMES, row))) for row in examples]
    return np.asarray(examples, dtype=float), np.asarray(labels, dtype=int)


def classify_features(features: dict) -> dict:
    """Fit the small decision tree and classify one feature record."""
    x_train, y_train = _training_examples()
    model = DecisionTreeClassifier(max_depth=4, random_state=42)
    model.fit(x_train, y_train)
    vector = np.asarray([[features[name] for name in FEATURE_NAMES]], dtype=float)
    prediction = int(model.predict(vector)[0])
    probabilities = model.predict_proba(vector)[0]
    confidence = float(max(probabilities))
    return {
        "classification": CLASS_NAMES[prediction],
        "class_id": prediction,
        "confidence": round(confidence, 3),
        "features": features,
        "model": "decision_tree_demo",
        "label_source": "rule_generated_training_examples",
    }


def classify_user(db: Session, user_id: int, days: int = 180) -> dict:
    features = extract_user_features(db, user_id, days)
    return classify_features(features)
