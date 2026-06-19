from ..extensions import db


class BudgetCategory(db.Model):
    __tablename__ = "budget_categories"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False)
    month = db.Column(db.String(7), nullable=False)  # YYYY-MM
    limit_amount = db.Column(db.Float, nullable=False)

    __table_args__ = (
        db.UniqueConstraint("user_id", "category_id", "month", name="uq_user_cat_month"),
    )
