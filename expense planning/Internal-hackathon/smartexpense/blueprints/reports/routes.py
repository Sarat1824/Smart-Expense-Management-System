import csv
from io import StringIO
from datetime import date
from sqlalchemy import func
from flask import Blueprint, render_template, request, make_response
from flask_login import login_required, current_user
from ...extensions import db
from ...models import Expense, Category

reports_bp = Blueprint("reports", __name__, url_prefix="/reports")


@reports_bp.route("/")
@login_required
def index():
    # Compute current month totals
    month = date.today().strftime('%Y-%m')
    base = db.session.query(func.coalesce(func.sum(Expense.amount), 0.0)).\
        filter(Expense.user_id == current_user.id, func.strftime('%Y-%m', Expense.spent_on) == month)
    total_expense = base.join(Category, Expense.category_id==Category.id).filter(Category.type=='expense').scalar() or 0.0
    total_income = base.join(Category, Expense.category_id==Category.id).filter(Category.type=='income').scalar() or 0.0
    tracked_savings = base.join(Category, Expense.category_id==Category.id).filter(Category.type=='savings').scalar() or 0.0
    # Prefer explicitly tracked savings; otherwise compute from income - expense
    savings = tracked_savings if tracked_savings > 0 else max(0.0, total_income - total_expense)
    labels = ["Expenses", "Income", "Savings"]
    data = [float(total_expense), float(total_income), float(savings)]
    return render_template("reports/index.html", labels=labels, data=data, month=month,
                           totals={"expense": total_expense, "income": total_income, "savings": savings})


@reports_bp.route("/export.csv")
@login_required
def export_csv():
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Title", "Category", "Amount", "Payment", "Date", "Note"])
    for exp, cat in Expense.query.filter_by(user_id=current_user.id).join(Category, Expense.category_id==Category.id).add_columns(Category.name).all():
        writer.writerow([exp.title, cat, f"{exp.amount:.2f}", exp.payment_mode or "", exp.spent_on.isoformat(), exp.note or ""]) 
    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=expenses.csv"
    response.headers["Content-Type"] = "text/csv"
    return response
