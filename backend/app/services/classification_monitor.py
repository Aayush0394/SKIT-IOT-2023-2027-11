"""Batch user classification and manual-review monitoring."""
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..models import User
from ..ml.user_classification import classify_user

ALLOWED_CLASSES = {"Premium", "Regular", "Risky"}


def classify_all_users(db: Session, days: int = 180) -> dict:
    users = db.scalars(select(User).order_by(User.id)).all()
    results = []
    distribution = {name: 0 for name in sorted(ALLOWED_CLASSES)}
    for user in users:
        prediction = classify_user(db, user.id, days)
        label = prediction.get("classification", "Regular")
        if label not in ALLOWED_CLASSES:
            label = "Regular"
        distribution[label] += 1
        results.append({
            "user_id": user.id, "user_name": user.name,
            "classification": label,
            "confidence": prediction.get("confidence", 0.0),
            "features": prediction.get("features", {}),
            "model": prediction.get("model"),
            "label_source": prediction.get("label_source"),
        })
    total = len(results)
    percentages = {
        name: round(count * 100 / total, 2) if total else 0.0
        for name, count in distribution.items()
    }
    return {"period_days": days, "total_users": total,
            "distribution": distribution, "percentages": percentages,
            "users": results}


def classification_review_flags(report: dict, confidence_limit: float = 0.60) -> list[dict]:
    flags = []
    for user in report.get("users", []):
        features = user.get("features", {})
        confidence = float(user.get("confidence") or 0.0)
        reasons = []
        if confidence < confidence_limit:
            reasons.append("low_model_confidence")
        if int(features.get("transaction_count", 0)) < 2:
            reasons.append("insufficient_history")
        if reasons:
            flags.append({
                "user_id": user["user_id"], "user_name": user["user_name"],
                "classification": user["classification"],
                "confidence": confidence, "review_reasons": reasons,
            })
    return flags


def build_classification_monitor(db: Session, days: int = 180) -> dict:
    report = classify_all_users(db, days)
    flags = classification_review_flags(report)
    report["manual_review_count"] = len(flags)
    report["manual_review"] = flags
    report["model_notice"] = (
        "The current classifier uses rule-generated demonstration labels. "
        "Review predictions before making real user decisions."
    )
    return report
