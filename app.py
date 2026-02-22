from flask import Flask, redirect, render_template, request, url_for, session,flash
from functools import wraps
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail,Message 
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///stu.db"
app.secret_key = 'my secret key'

db = SQLAlchemy(app)

class Expense(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String,nullable=False)
    amount=db.Column(db.Integer,nullable=False)
    user=db.Column(db.String,nullable=False)
    


@app.context_processor
def inject_user():
    return dict(username=session.get('user'))



def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return wrapper

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        if password=="":
            flash("Plese enter password")
            return(redirect(url_for('login')))
            
        
        if email=="":
            flash("Please enter email")
            return(redirect(url_for('login')))
        
        username = email.split('@')[0]
        session['user'] = username
        return redirect(url_for('profile'))
    return render_template('login.html')

@app.route('/profile')
@login_required
def profile():
    
    return render_template('profile.html')

@app.route('/logout')
def logout():
    session.pop('user',None)
    return (redirect(url_for('login'))) 
@app.route('/emi')
@login_required
def emi():
    return render_template('emi.html') 
@app.route('/signin',methods=['GET','POST'])
def sign_in():
    if request.method=='POST':
        email=request.form.get('email')
    return render_template('sigin.html')

with app.app_context():
    db.create_all()


@app.route('/edit',methods=['GET','POST'])
def edit():
    if request.method=='POST':
        name=request.form.get('expense')
        amount=request.form.get('amount')
        
        if not name:
            flash("Expense can not be empty")
            return redirect(url_for('edit'))
        
        try:
            amount=float(amount)
        except ValueError:
            flash("Amount must be in positive Integers")
            return redirect(url_for('expense'))
        
    expensesa=Expense.query.filter_by(user=session['user']).all()
    return render_template('edit.html',expenses=expensesa)
        
        
        
        


@app.route('/expense',methods=['GET','POST'])
@login_required
def expense():
    if request.method=='POST':
        name=request.form.get('expense')
        amount=request.form.get('amount')
        
        if not name:
            flash("Expense must be a number","expense_error")
            return redirect(url_for('expense'))
        
        try:
            amount=float(amount)
        except ValueError:
            flash("Amount must be in number","expense_error")
            return redirect(url_for('expense'))
        
        new_expense=Expense(
            name=name,
            amount=amount,
            user=session['user']
        )
        db.session.add(new_expense)
        db.session.commit()
        return redirect(url_for('expense'))

    
    expenses = Expense.query.filter_by(user=session['user']).all()

    return render_template("Expense.html", expenses=expenses)
    
with app.app_context():
    db.create_all()

    

if __name__ == '__main__':
    app.run(debug=True)