from datetime import date
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from ...extensions import db
from ...models import Expense, Category

income_bp = Blueprint("income", __name__, url_prefix="/income")


@income_bp.route("/")
@login_required
def list_income():
    income_rows = (
        Expense.query.join(Category, Expense.category_id == Category.id)
        .filter(Expense.user_id == current_user.id, Category.type == "income")
        .order_by(Expense.spent_on.desc())
        .all()
    )
    return render_template("income/list.html", income_rows=income_rows)


@income_bp.route("/create", methods=["GET", "POST"])
@login_required
def create_income():
    categories = (
        Category.query.filter_by(user_id=current_user.id, type="income")
        .order_by(Category.name)
        .all()
    )
    if request.method == "POST":
        title = request.form.get("title")
        category_id = request.form.get("category_id")
        amount = float(request.form.get("amount"))
        payment_mode = request.form.get("payment_mode")
        date_str = request.form.get("spent_on")
        on_date = date.fromisoformat(date_str) if date_str else date.today()
        note = request.form.get("note")
        row = Expense(
            user_id=current_user.id,
            title=title,
            category_id=category_id,
            amount=amount,
            payment_mode=payment_mode,
            spent_on=on_date,
            note=note,
        )
        db.session.add(row)
        db.session.commit()
        flash("Income added", "success")
        return redirect(url_for("income.list_income"))
    return render_template("income/form.html", categories=categories)
