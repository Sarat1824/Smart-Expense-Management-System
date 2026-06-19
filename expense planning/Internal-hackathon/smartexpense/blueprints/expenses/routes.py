from datetime import date, datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from ...extensions import db
from ...models import Expense, Category, Budget, BudgetCategory
from sqlalchemy import or_, and_, func


expenses_bp = Blueprint("expenses", __name__, url_prefix="/expenses")


@expenses_bp.route("/")
@login_required
def list_expenses():
    expenses = Expense.query.filter_by(user_id=current_user.id).order_by(Expense.spent_on.desc()).all()
    return render_template("expenses/list.html", expenses=expenses)


def check_budget_exceeded(user_id, amount, category_id=None, date_obj=None):
    """Check if adding this expense would exceed any budget limits."""
    if not date_obj:
        date_obj = date.today()
    
    month_str = date_obj.strftime("%Y-%m")
    
    # First, check against remaining monthly balance (income - expenses - savings)
    # Compute totals for the month
    total_income = db.session.query(
        func.coalesce(func.sum(Expense.amount), 0)
    ).join(Category, Expense.category_id == Category.id).filter(
        Expense.user_id == user_id,
        func.strftime("%Y-%m", Expense.spent_on) == month_str,
        Category.type == 'income'
    ).scalar() or 0
    total_expense = db.session.query(
        func.coalesce(func.sum(Expense.amount), 0)
    ).join(Category, Expense.category_id == Category.id).filter(
        Expense.user_id == user_id,
        func.strftime("%Y-%m", Expense.spent_on) == month_str,
        Category.type == 'expense'
    ).scalar() or 0
    total_savings = db.session.query(
        func.coalesce(func.sum(Expense.amount), 0)
    ).join(Category, Expense.category_id == Category.id).filter(
        Expense.user_id == user_id,
        func.strftime("%Y-%m", Expense.spent_on) == month_str,
        Category.type == 'savings'
    ).scalar() or 0
    remaining_balance = (total_income or 0) - (total_expense or 0) - (total_savings or 0)
    
    if amount > remaining_balance:
        return f"Amount exceeds available balance. Remaining: ₹{remaining_balance:.2f}"
    
    # Check category budget first (if category is provided)
    if category_id:
        category_budget = BudgetCategory.query.filter(
            BudgetCategory.user_id == user_id,
            BudgetCategory.category_id == category_id,
            BudgetCategory.month == month_str
        ).first()
        
        if category_budget:
            total_spent = db.session.query(
                func.coalesce(func.sum(Expense.amount), 0)
            ).filter(
                Expense.user_id == user_id,
                Expense.category_id == category_id,
                func.strftime("%Y-%m", Expense.spent_on) == month_str
            ).scalar() or 0
            
            if total_spent + amount > category_budget.limit_amount:
                return f"Adding this expense would exceed your budget for this category. Remaining: ₹{category_budget.limit_amount - total_spent:.2f}"
    
    # Check overall monthly budget
    monthly_budget = Budget.query.filter_by(
        user_id=user_id,
        month=month_str
    ).first()
    
    if monthly_budget:
        total_monthly_spent = db.session.query(
            func.coalesce(func.sum(Expense.amount), 0)
        ).filter(
            Expense.user_id == user_id,
            func.strftime("%Y-%m", Expense.spent_on) == month_str
        ).scalar() or 0
        
        if total_monthly_spent + amount > monthly_budget.limit_amount:
            return f"Adding this expense would exceed your monthly budget. Remaining: ₹{monthly_budget.limit_amount - total_monthly_spent:.2f}"
    
    return None

@expenses_bp.route("/create", methods=["GET", "POST"])
@login_required
def create_expense():
    categories = (
        Category.query.filter(
            Category.type=="expense",
            or_(Category.user_id==current_user.id, Category.user_id.is_(None))
        ).order_by(Category.name).all()
    )
    
    if request.method == "POST":
        created = 0
        errors = []
        
        for i in (1, 2, 3):
            title = request.form.get(f"title_{i}")
            amount_raw = request.form.get(f"amount_{i}")
            category_id = request.form.get(f"category_id_{i}")
            
            # Skip empty expense entries
            if not title or not amount_raw or not category_id:
                continue
                
            try:
                amount = float(amount_raw)
                if amount <= 0:
                    errors.append(f"Expense {i}: Amount must be greater than zero")
                    continue
                    
                # Check budget before adding
                spent_on_str = request.form.get(f"spent_on_{i}")
                spent_on = date.fromisoformat(spent_on_str) if spent_on_str else date.today()
                
                budget_check = check_budget_exceeded(
                    current_user.id, 
                    amount, 
                    category_id,
                    spent_on
                )
                
                if budget_check:
                    errors.append(f"Expense '{title}': {budget_check}")
                    continue
                
                # If budget check passed, create the expense
                payment_mode = request.form.get(f"payment_mode_{i}")
                note = request.form.get(f"note_{i}")
                
                exp = Expense(
                    user_id=current_user.id, 
                    title=title, 
                    category_id=category_id, 
                    amount=amount,
                    payment_mode=payment_mode, 
                    spent_on=spent_on, 
                    note=note
                )
                
                db.session.add(exp)
                created += 1
                
            except ValueError:
                errors.append(f"Expense {i}: Invalid amount")
                continue
        
        if errors:
            for error in errors:
                flash(error, 'danger')
            
            if created == 0:
                # If no expenses were created due to errors, show the form again
                return render_template("expenses/form.html", categories=categories)
        
        if created > 0:
            try:
                db.session.commit()
                flash(f"{created} expense(s) added successfully", "success")
                if errors:
                    flash("Some expenses were not added due to budget limits", "warning")
            except Exception as e:
                db.session.rollback()
                flash("An error occurred while saving expenses", "danger")
        elif not errors:
            flash("No expenses provided", "warning")
            
        return redirect(url_for("expenses.list_expenses"))
    
    # GET request - show the form
    return render_template("expenses/form.html", categories=categories)
    return render_template("expenses/form.html", categories=categories)

@expenses_bp.route("/check-budget", methods=["POST"])
@login_required
def check_budget_api():
    data = request.get_json(silent=True) or request.form
    amount_raw = data.get("amount")
    category_id = data.get("category_id")
    spent_on_str = data.get("spent_on")

    if not amount_raw or not category_id:
        return jsonify({"ok": False, "message": "amount and category_id are required"}), 400

    try:
        amount = float(amount_raw)
    except (TypeError, ValueError):
        return jsonify({"ok": False, "message": "Invalid amount"}), 400

    try:
        date_obj = date.fromisoformat(spent_on_str) if spent_on_str else date.today()
    except Exception:
        date_obj = date.today()

    msg = check_budget_exceeded(current_user.id, amount, category_id, date_obj)
    if msg:
        return jsonify({"ok": False, "message": msg}), 200
    return jsonify({"ok": True, "message": "Within budget"}), 200


@expenses_bp.route("/<int:expense_id>/edit", methods=["GET", "POST"])
@login_required
def edit_expense(expense_id):
    exp = Expense.query.filter_by(id=expense_id, user_id=current_user.id).first_or_404()
    categories = Category.query.filter_by(user_id=current_user.id, type="expense").order_by(Category.name).all()
    if request.method == "POST":
        exp.title = request.form.get("title")
        exp.category_id = request.form.get("category_id")
        exp.amount = float(request.form.get("amount"))
        exp.payment_mode = request.form.get("payment_mode")
        spent_on_str = request.form.get("spent_on")
        exp.spent_on = date.fromisoformat(spent_on_str) if spent_on_str else exp.spent_on
        exp.note = request.form.get("note")
        db.session.commit()
        flash("Expense updated", "success")
        return redirect(url_for("expenses.list_expenses"))
    return render_template("expenses/form.html", expense=exp, categories=categories)


@expenses_bp.route("/<int:expense_id>/delete", methods=["POST"])
@login_required
def delete_expense(expense_id):
    exp = Expense.query.filter_by(id=expense_id, user_id=current_user.id).first_or_404()
    db.session.delete(exp)
    db.session.commit()
    flash("Expense deleted", "info")
    return redirect(url_for("expenses.list_expenses"))


@expenses_bp.route("/categories", methods=["GET", "POST"])
@login_required
def manage_categories():
    # Ensure a common starter set for every account
    def _ensure_defaults():
        defaults = [
            ("Groceries", "expense"),
            ("Clothing", "expense"),
            ("Transport", "expense"),
            ("Bills", "expense"),
            ("Entertainment", "expense"),
        ]
        existing = {c.name.lower(): c for c in Category.query.filter_by(user_id=current_user.id).all()}
        created = 0
        for name, ctype in defaults:
            if name.lower() not in existing:
                db.session.add(Category(user_id=current_user.id, name=name, type=ctype))
                created += 1
        if created:
            db.session.commit()

    if request.method == "POST":
        name = request.form.get("name")
        ctype = "expense"  # force expense-only categories
        if not name:
            flash("Name is required", "danger")
        else:
            # prevent duplicates against user's own and global defaults
            exists = Category.query.filter(or_(Category.user_id==current_user.id, Category.user_id.is_(None)), Category.name==name).first()
            if exists:
                flash("Category name already exists", "warning")
            else:
                db.session.add(Category(user_id=current_user.id, name=name, type=ctype))
                db.session.commit()
                flash("Category added", "success")
        return redirect(url_for("expenses.manage_categories"))

    _ensure_defaults()
    cats = (
        Category.query.filter(
            Category.type=="expense",
            or_(Category.user_id==current_user.id, Category.user_id.is_(None))
        )
        .order_by(Category.name)
        .all()
    )
    return render_template("expenses/categories.html", categories=cats)


@expenses_bp.route("/categories/<int:category_id>/edit", methods=["GET", "POST"])
@login_required
def edit_category(category_id):
    # Only allow editing user's own categories
    cat = Category.query.filter_by(id=category_id, user_id=current_user.id).first_or_404()
    
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            flash("Category name is required", "danger")
        else:
            # Check for duplicate names (case-insensitive) in both user and global categories
            existing = Category.query.filter(
                db.func.lower(Category.name) == name.lower(),
                Category.id != cat.id,
                or_(
                    Category.user_id == current_user.id,
                    Category.user_id.is_(None)  # Also check against global categories
                )
            ).first()
            
            if existing:
                flash("A category with this name already exists", "warning")
            else:
                cat.name = name
                db.session.commit()
                flash("Category updated successfully", "success")
                return redirect(url_for("expenses.manage_categories"))
    
    return render_template("expenses/category_form.html", category=cat)


@expenses_bp.route("/categories/<int:category_id>/delete", methods=["POST"])
@login_required
def delete_category(category_id):
    cat = Category.query.filter_by(id=category_id, user_id=current_user.id).first_or_404()
    # Prevent deletion if referenced by any expenses
    used = Expense.query.filter_by(user_id=current_user.id, category_id=cat.id).first()
    if used:
        flash("Cannot delete category in use by expenses", "danger")
        return redirect(url_for("expenses.manage_categories"))
    db.session.delete(cat)
    db.session.commit()
    flash("Category deleted", "info")
    return redirect(url_for("expenses.manage_categories"))
