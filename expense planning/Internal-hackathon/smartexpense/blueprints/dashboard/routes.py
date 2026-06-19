from datetime import date
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from sqlalchemy import func
from ...extensions import db
from ...models import Expense, Category, Budget


dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


@dashboard_bp.route("/")
@login_required
def index():
    today = date.today()
    month_prefix = today.strftime("%Y-%m")
    # Monthly totals
    q_base = db.session.query(func.coalesce(func.sum(Expense.amount), 0.0)).filter(
        Expense.user_id == current_user.id,
        func.strftime('%Y-%m', Expense.spent_on) == month_prefix
    )
    total_expense = q_base.join(Category, Expense.category_id == Category.id).filter(Category.type == 'expense').scalar()
    total_income = q_base.join(Category, Expense.category_id == Category.id).filter(Category.type == 'income').scalar()
    total_savings = q_base.join(Category, Expense.category_id == Category.id).filter(Category.type == 'savings').scalar()
    balance = (total_income or 0.0) - (total_expense or 0.0) - (total_savings or 0.0)

    by_category = db.session.query(Category.name, func.sum(Expense.amount)).join(Expense).\
        filter(Expense.user_id == current_user.id, func.strftime('%Y-%m', Expense.spent_on) == month_prefix, Category.type=='expense').\
        group_by(Category.name).all()

    labels = [row[0] for row in by_category]
    data = [float(row[1]) for row in by_category]
    cat_rows = [{"name": n, "total": float(t)} for (n, t) in by_category]
    if total_savings and float(total_savings) > 0:
        cat_rows.append({"name": "Savings", "total": float(total_savings)})


    # Monthly budget alert
    b = Budget.query.filter_by(user_id=current_user.id, month=month_prefix).first()
    budget_limit = b.limit_amount if b else None
    over_budget = bool(budget_limit and total_expense > budget_limit)
    nearing_budget = bool(budget_limit and not over_budget and total_expense >= 0.9 * budget_limit)

    return render_template(
        "dashboard/index.html",
        total_expense=total_expense,
        total_income=total_income,
        total_savings=total_savings,
        balance=balance,
        labels=labels,
        data=data,
        cat_rows=cat_rows,
        month=month_prefix,
        budget_limit=budget_limit,
        over_budget=over_budget,
        nearing_budget=nearing_budget,
    )


@dashboard_bp.route("/seed")
@login_required
def seed_demo():
    """Seed sample categories, income, expenses, and a monthly budget for demo purposes."""
    from datetime import date
    today = date.today()
    month = today.strftime('%Y-%m')

    # Ensure some categories
    cat_names_expense = ["Food", "Travel", "Bills", "Shopping"]
    cat_names_income = ["Salary", "Freelance"]
    cats = {c.name: c for c in Category.query.filter_by(user_id=current_user.id).all()}
    for n in cat_names_expense:
        if n not in cats:
            db.session.add(Category(user_id=current_user.id, name=n, type='expense'))
    for n in cat_names_income:
        if n not in cats:
            db.session.add(Category(user_id=current_user.id, name=n, type='income'))
    db.session.commit()

    cats = {c.name: c for c in Category.query.filter_by(user_id=current_user.id).all()}

    # Add a budget
    b = Budget.query.filter_by(user_id=current_user.id, month=month).first()
    if not b:
        db.session.add(Budget(user_id=current_user.id, month=month, limit_amount=20000))

    # Seed some expenses
    if not Expense.query.filter_by(user_id=current_user.id).first():
        demo = [
            ("Lunch", cats["Food"].id, 250, "UPI"),
            ("Cab", cats["Travel"].id, 320, "Cash"),
            ("Electricity Bill", cats["Bills"].id, 1800, "Card"),
            ("Shoes", cats["Shopping"].id, 2200, "Card"),
        ]
        for title, cat_id, amt, mode in demo:
            db.session.add(Expense(user_id=current_user.id, title=title, category_id=cat_id, amount=amt, payment_mode=mode, spent_on=today))

        # Income rows (stored in same table but with income categories)
        inc_demo = [
            ("Monthly Salary", cats["Salary"].id, 50000, "Bank"),
            ("Side Gig", cats["Freelance"].id, 6000, "UPI"),
        ]
        for title, cat_id, amt, mode in inc_demo:
            db.session.add(Expense(user_id=current_user.id, title=title, category_id=cat_id, amount=amt, payment_mode=mode, spent_on=today))

    db.session.commit()
    from flask import redirect, url_for, flash
    flash("Demo data seeded", "success")
    return redirect(url_for('dashboard.index'))


@dashboard_bp.route("/add-income", methods=["POST"])
@login_required
def add_income():
    from datetime import date as _date
    title = (request.form.get('title') or '').strip()
    amount_raw = request.form.get('amount')
    payment_mode = request.form.get('payment_mode')
    date_str = request.form.get('spent_on')
    note = request.form.get('note')

    # Validate
    if not title or not amount_raw:
        flash('Please fill Title and Amount', 'danger')
        return redirect(url_for('dashboard.index'))

    spent_on = _date.fromisoformat(date_str) if date_str else _date.today()
    amount = float(amount_raw)
    # Use or create a default income category
    cat = Category.query.filter_by(user_id=current_user.id, type='income').order_by(Category.id).first()
    if not cat:
        cat = Category(user_id=current_user.id, name='Income', type='income')
        db.session.add(cat)
        db.session.flush()  # get cat.id without full commit

    db.session.add(Expense(user_id=current_user.id, title=title, category_id=cat.id, amount=amount,
                           payment_mode=payment_mode, spent_on=spent_on, note=note))
    db.session.commit()
    flash('Income added', 'success')
    return redirect(url_for('dashboard.index'))


@dashboard_bp.route("/add-savings", methods=["POST"])
@login_required
def add_savings():
    from datetime import date as _date
    title = (request.form.get('title') or 'Savings').strip()
    amount_raw = request.form.get('amount')
    payment_mode = request.form.get('payment_mode')
    date_str = request.form.get('spent_on')
    note = request.form.get('note')

    if not amount_raw:
        flash('Please enter Amount', 'danger')
        return redirect(url_for('dashboard.index'))

    spent_on = _date.fromisoformat(date_str) if date_str else _date.today()
    amount = float(amount_raw)

    # Use or create a default savings category
    cat = Category.query.filter_by(user_id=current_user.id, type='savings').order_by(Category.id).first()
    if not cat:
        cat = Category(user_id=current_user.id, name='Savings', type='savings')
        db.session.add(cat)
        db.session.flush()

    db.session.add(Expense(user_id=current_user.id, title=title, category_id=cat.id, amount=amount,
                           payment_mode=payment_mode, spent_on=spent_on, note=note))
    db.session.commit()
    flash('Savings added', 'success')
    return redirect(url_for('dashboard.index'))
