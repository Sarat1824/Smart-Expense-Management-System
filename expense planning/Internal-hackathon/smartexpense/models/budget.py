from ..extensions import db


class Budget(db.Model):
    __tablename__ = "budgets"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    month = db.Column(db.String(7), nullable=False)  # e.g., '2025-10'
    limit_amount = db.Column(db.Float, nullable=False)
    spent_amount = db.Column(db.Float, default=0.0)

    __table_args__ = (
        db.UniqueConstraint("user_id", "month", name="uq_user_month"),
    )
