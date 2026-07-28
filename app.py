from flask import Flask, redirect, render_template, request, url_for, session, flash, Response
from functools import wraps
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import csv
import io

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///stu.db"
app.secret_key = 'my_secret_key_b2b_enterprise'

db = SQLAlchemy(app)

# ---------------------------------------------------------------------------
# Database Schemas
# ---------------------------------------------------------------------------

# Expense Database Schema
class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String, nullable=True, default="Operational")
    payment_mode = db.Column(db.String, nullable=True, default="UPI")
    user = db.Column(db.String, nullable=False)
    date_time = db.Column(db.String, nullable=False)

# User Schema
class User(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String, nullable=False, unique=True)
    username = db.Column(db.String, nullable=True)
    password = db.Column(db.String, nullable=False)
    role = db.Column(db.String, nullable=True, default="owner")
    budget = db.Column(db.Float, nullable=True)
    
    


class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)             # 🔹 Mandatory
    father_name = db.Column(db.String, nullable=False)      # 🔹 Mandatory
    mobile = db.Column(db.String, nullable=False)           # 🔹 Mandatory
    designation = db.Column(db.String, nullable=False)      # 🔹 Mandatory
    salary = db.Column(db.Float, nullable=False)            # 🔹 Mandatory
    
    # Optional Fields
    religion = db.Column(db.String, nullable=True)
    alternate_mobile = db.Column(db.String, nullable=True)
    email = db.Column(db.String, nullable=True)
    current_address = db.Column(db.String, nullable=True)
    permanent_address = db.Column(db.String, nullable=True)
    
    join_date = db.Column(db.String, nullable=False)
    owner_username = db.Column(db.String, nullable=False)

# 🔹 3. Attendance Schema (Now linked to Employee, not User)
class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, nullable=False)
    employee_name = db.Column(db.String, nullable=False)
    date = db.Column(db.String, nullable=False)
    check_in_time = db.Column(db.String, nullable=False)
    status = db.Column(db.String, default="Present")
    owner_username = db.Column(db.String, nullable=False)

# Loan / Dues Schema 
class Loans(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String, nullable=False)
    loan_type = db.Column(db.String, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    monthly = db.Column(db.String, nullable=False)
    duration = db.Column(db.String, nullable=False)     


# ---------------------------------------------------------------------------
# Context Processors & Middleware
# ---------------------------------------------------------------------------

@app.context_processor
def inject_user_context():
    """Injects user information and available endpoints into all Jinja templates."""
    return dict(
        username=session.get('user'),
        user_role=session.get('role', 'owner'),
        endpoints=[rule.endpoint for rule in app.url_map.iter_rules()]
    )

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'user' not in session:
            flash("Please login to access the enterprise dashboard.", "warning")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return wrapper


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route('/')
@login_required
def home():
    return redirect(url_for('expense'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role', 'owner')
        remember = request.form.get('login-check')

        if not email:
            flash("Please enter business email.", "danger")
            return redirect(url_for('login'))

        if not password:
            flash("Please enter password.", "danger")
            return redirect(url_for('login'))

        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session['user'] = user.username
            session['role'] = role
            flash(f"Logged in successfully as {role.capitalize()}.", "success")
            return redirect(url_for('expense'))

        flash("Invalid business email or password.", "danger")
        
    return render_template('login.html')


@app.route('/signin', methods=['GET', 'POST'])
def sign_in():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        username = request.form.get('username')
        role = request.form.get('role', 'owner')

        if User.query.filter_by(email=email).first():
            flash("Business account with this email already exists.", "danger")
            return redirect(url_for('sign_in'))

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(
            email=email,
            password=hashed_password,
            username=username,
            role=role
        )
        db.session.add(new_user)
        db.session.commit()

        flash("Account created successfully. Please log in.", "success")
        return redirect(url_for('login'))

    return render_template('sigin.html')


@app.route('/logout')
@login_required
def logout():
    session.clear()
    flash("Logged out from Enterprise Session.", "info")
    return redirect(url_for('login'))


# ---------------------------------------------------------------------------
# Expense & Financial Ledger Routes
# ---------------------------------------------------------------------------

@app.route('/expense', methods=['GET', 'POST'])
@login_required
def expense():
    if request.method == 'POST':
        name = request.form.get('expense')
        amount = request.form.get('amount')
        category = request.form.get('category', 'Operational')
        payment_mode = request.form.get('payment_mode', 'UPI')

        if not name:
            flash("Expense description cannot be empty.", "danger")
            return redirect(url_for('expense'))

        try:
            amount = float(amount)
        except (ValueError, TypeError):
            flash("Amount must be a valid number.", "danger")
            return redirect(url_for('expense'))

        new_expense = Expense(
            name=name,
            amount=amount,
            category=category,
            payment_mode=payment_mode,
            user=session['user'],
            date_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

        db.session.add(new_expense)
        db.session.commit()
        flash("Operational expense recorded in ledger.", "success")
        return redirect(url_for('expense'))

    expenses = Expense.query.filter_by(user=session['user']).order_by(Expense.id.desc()).all()
    total = sum(exp.amount for exp in expenses)
    
    user = User.query.filter_by(username=session['user']).first()
    user_budget = float(user.budget) if (user and user.budget) else 0.0
    remaining = user_budget - float(total)

    return render_template(
        "expense.html",
        expenses=expenses,
        total=total,
        remaining=round(remaining, 2),
        user_budget=user_budget
    )


@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    expense = Expense.query.get_or_404(id)
    if expense.user != session['user']:
        flash("Unauthorized access to business record.", "danger")
        return redirect(url_for('expense'))

    if request.method == 'POST':
        name = request.form.get('expense')
        amount = request.form.get('amount')

        if not name:
            flash("Description cannot be empty.", "danger")
            return redirect(url_for('edit', id=id))

        try:
            amount = float(amount)
        except ValueError:
            flash("Amount must be a positive number.", "danger")
            return redirect(url_for('edit', id=id))

        expense.name = name
        expense.amount = amount
        db.session.commit()

        flash("Ledger entry updated successfully.", "success")
        return redirect(url_for('expense'))

    return render_template("edit.html", expense=expense)


@app.route('/delete/<int:id>', methods=['GET', 'POST'])
@login_required
def delete(id):
    expense = Expense.query.get_or_404(id)
    if expense.user != session['user']:
        flash("Unauthorized access.", "danger")
        return redirect(url_for('expense'))

    db.session.delete(expense)
    db.session.commit()

    flash("Entry deleted from operational ledger.", "success")
    return redirect(url_for('expense'))


@app.route('/budget', methods=['POST'])
@login_required
def budget():
    amount = request.form.get('budget')
    if not amount:
        flash("Please enter an operational cap amount.", "danger")
        return redirect(url_for('expense'))

    try:
        amount = float(amount)
    except ValueError:
        flash("Cap amount must be numeric.", "danger")
        return redirect(url_for('expense'))

    user = User.query.filter_by(username=session['user']).first()
    if user:
        user.budget = amount
        db.session.commit()
        flash("Monthly operational cap updated successfully.", "success")

    return redirect(url_for('expense'))

#Add Employe route
# 🔹 1. View Employee Directory & Onboarding Form
@app.route('/employees', methods=['GET','POST'])
@login_required
def employees():
    current_owner = session.get('user')
    
    # Fetch employees created by the current logged-in owner
    staff_list = Employee.query.filter_by(owner_username=current_owner).all()
    
    return render_template('employee.html', staff_list=staff_list)


# 🔹 2. Handle Form Submission & Trigger Confirmation
@app.route('/add_employee', methods=['GET','POST'])
@login_required
def add_employee():
    if request.method == 'POST':
        current_owner = session.get('user')
        if not current_owner:
          flash("Session expired. Please log in again.", "danger")
          return redirect(url_for('login'))

         # Extract Form Data
        name = request.form.get('name')
        father_name = request.form.get('father_name')
        mobile = request.form.get('mobile')
        designation = request.form.get('designation')
        salary = request.form.get('salary')

    # Optional Fields
        religion = request.form.get('religion')
        alternate_mobile = request.form.get('alternate_mobile')
        email = request.form.get('email')
        current_address = request.form.get('current_address')
        permanent_address = request.form.get('permanent_address')

    # Validate Mandatory Fields
        if not all([name, father_name, mobile, designation, salary]):
            flash("Please fill in all mandatory fields (Name, Father's Name, Phone, Position, Salary).", "danger")
            return redirect(url_for('employees'))

    # Save to Database
        new_emp = Employee(
            name=name,
            father_name=father_name,
            mobile=mobile,
            designation=designation,
            salary=float(salary),
            religion=religion,
            alternate_mobile=alternate_mobile,
            email=email,
            current_address=current_address,
            permanent_address=permanent_address,
            join_date=datetime.now().strftime("%Y-%m-%d"),
            owner_username=current_owner
        )

        db.session.add(new_emp)
        db.session.commit()

    # 🔹 Confirmation Flash Message
        flash(f"🎉 Employee '{name}' has been successfully registered and added to your roster!", "success")
        return redirect(url_for('employees'))

    return render_template("add_employee.html")
    

# ---------------------------------------------------------------------------
# B2B CA / Audit Export Endpoint (CSV Generation)
# ---------------------------------------------------------------------------

@app.route('/export_csv')
@login_required
def export_csv():
    expenses = Expense.query.filter_by(user=session['user']).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # CSV Header
    writer.writerow(['Record ID', 'Expense/Vendor', 'Category', 'Payment Mode', 'Amount (INR)', 'Date Recorded'])
    
    # CSV Rows
    for exp in expenses:
        writer.writerow([
            exp.id,
            exp.name,
            getattr(exp, 'category', 'Operational'),
            getattr(exp, 'payment_mode', 'UPI'),
            exp.amount,
            exp.date_time
        ])
        
    output.seek(0)
    
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename=Enterprise_Audit_Ledger_{session['user']}.csv"}
    )


# ---------------------------------------------------------------------------
# Financial Tools & Modules
# ---------------------------------------------------------------------------

@app.route('/emi', methods=["POST", "GET"])
@login_required
def emi():
    emi_val = None

    if request.method == "POST":
        pr = request.form.get('principal')
        rate = request.form.get('rate')
        time = request.form.get('time')

        if not pr or not rate or not time:
            flash("Please fill in all principal, rate, and duration fields.", "danger")
            return redirect(url_for('emi'))

        try:
            fpr = float(pr)
            frate = float(rate) / (12 * 100)
            ftime = int(time) * 12

            if frate > 0:
                emi_val = (fpr * frate * (1 + frate) ** ftime) / ((1 + frate) ** ftime - 1)
            else:
                emi_val = fpr / ftime
        except ValueError:
            flash("Invalid numeric input for EMI calculation.", "danger")
            return redirect(url_for('emi'))

    return render_template('emi.html', emi=emi_val)


@app.route('/loans', methods=['POST', 'GET'])
@login_required
def loans():
    if request.method == "POST":
        loan_type = request.form.get('loan')
        amount = request.form.get('amount')
        monthly = request.form.get('monthly')
        duration = request.form.get('duration')

        if not loan_type or not amount or not monthly or not duration:
            flash("All loan/receivables details are required.", "danger")
            return redirect(url_for('loans'))

        try:
            new_loan = Loans(
                loan_type=loan_type,
                amount=float(amount),
                monthly=monthly,
                duration=str(duration),
                user=session['user']
            )
            db.session.add(new_loan)
            db.session.commit()
            flash("Client receivable / loan entry recorded.", "success")
        except ValueError:
            flash("Amount must be a numeric value.", "danger")

        return redirect(url_for('loans'))

    user_loans = Loans.query.filter_by(user=session['user']).all()
    return render_template('loans.html', loans=user_loans)


# ---------------------------------------------------------------------------
# Database Initialization & App Runner
# ---------------------------------------------------------------------------

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)