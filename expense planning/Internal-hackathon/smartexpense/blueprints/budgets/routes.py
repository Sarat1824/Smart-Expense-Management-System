from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from sqlalchemy import func
from ...extensions import db
from ...models import Budget, BudgetCategory, Expense, Category

budgets_bp = Blueprint("budgets", __name__, url_prefix="/budgets")


@budgets_bp.route("/", methods=["GET", "POST"])
@login_required
def manage_budgets():
    if request.method == "POST":
        month = request.form.get("month")
        limit_amount = float(request.form.get("limit_amount"))
        b = Budget.query.filter_by(user_id=current_user.id, month=month).first()
        if b:
            b.limit_amount = limit_amount
        else:
            db.session.add(Budget(user_id=current_user.id, month=month, limit_amount=limit_amount))
        db.session.commit()
        flash("Budget saved", "success")
        return redirect(url_for("budgets.manage_budgets"))

    budgets = Budget.query.filter_by(user_id=current_user.id).order_by(Budget.month.desc()).all()
    return render_template("budgets/list.html", budgets=budgets)


@budgets_bp.route("/categories", methods=["GET", "POST"])
@login_required
def category_budgets():
    month = request.values.get("month")
    if not month:
        # default to current month
        from datetime import date
        month = date.today().strftime("%Y-%m")

    if request.method == "POST":
        category_id = int(request.form.get("category_id"))
        limit_amount = float(request.form.get("limit_amount"))
        bc = BudgetCategory.query.filter_by(user_id=current_user.id, category_id=category_id, month=month).first()
        if bc:
            bc.limit_amount = limit_amount
        else:
            db.session.add(BudgetCategory(user_id=current_user.id, category_id=category_id, month=month, limit_amount=limit_amount))
        db.session.commit()
        flash("Category budget saved", "success")
        return redirect(url_for("budgets.category_budgets", month=month))

    # Fetch all expense-type categories
    categories = Category.query.filter_by(user_id=current_user.id, type="expense").order_by(Category.name).all()

    # Existing budgets for month
    bc_rows = BudgetCategory.query.filter_by(user_id=current_user.id, month=month).all()
    bc_map = {row.category_id: row for row in bc_rows}

    # Compute spent per category for month
    month_spend = dict(
        db.session.query(Expense.category_id, func.coalesce(func.sum(Expense.amount), 0.0))
        .filter(
            Expense.user_id == current_user.id,
            func.strftime('%Y-%m', Expense.spent_on) == month
        )
        .group_by(Expense.category_id)
        .all()
    )

    # Build view model list
    view = []
    for c in categories:
        limit = bc_map.get(c.id).limit_amount if bc_map.get(c.id) else None
        spent = float(month_spend.get(c.id, 0.0))
        status = "none"
        if limit is not None:
            status = "over" if spent > limit else ("near" if spent >= 0.9 * limit else "ok")
        view.append({"category": c, "limit": limit, "spent": spent, "status": status})

    return render_template("budgets/categories.html", month=month, categories=categories, rows=view)
