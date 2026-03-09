from flask import Flask, redirect, render_template, request, url_for, session,flash
from functools import wraps
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail,Message 
from werkzeug.security import generate_password_hash,check_password_hash
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///stu.db"
app.secret_key = 'my secret key'

db = SQLAlchemy(app)

#Expense-database-Schema
class Expense(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String,nullable=False)
    amount=db.Column(db.Float,nullable=False)
    user=db.Column(db.String,nullable=False)
    
#User-Schema
class User(db.Model):
    user_id=db.Column(db.Integer,primary_key=True)
    email=db.Column(db.String,nullable=False,unique=True)
    username=db.Column(db.String,nullable=False)
    password=db.Column(db.String,nullable=False)
    
    


@app.context_processor
def inject_user():
    return dict(username=session.get('user'))


#logincheck
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return wrapper
#home
@app.route('/')
@login_required
def home():
    return render_template('index.html')
#login page
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
        
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password,password):
            session['user'] = user.username
            print("logged in succesful")
            return redirect(url_for('home'))
        flash("Invalid email or password","danger")
    return render_template('login.html')
#profile page
@app.route('/profile')  
@login_required
def profile():
    
    return render_template('profile.html')
#logout button
@app.route('/logout')
def logout():
    session.pop('user',None)
    return (redirect(url_for('login'))) 


#emi page
@app.route('/emi')
@login_required
def emi():
    return render_template('emi.html') 
@app.route('/signin',methods=['GET','POST'])

#sign-in page
def sign_in():
    if request.method=='POST':
        email=request.form.get('email')
        password=request.form.get('password')
        username=request.form.get('username')
        if User.query.filter_by(email=email).first():
            flash("Email already Exist","danger")
            return redirect(url_for('sign_in'))
        hashed_password=generate_password_hash(password,method='pbkdf2:sha256')
        new_user=User(
            email=email,
            password=hashed_password,
            username=username,         
        )
        db.session.add(new_user)
        print("BEFORE COMMIT")
        db.session.commit()
        print("AFTER COMMIT")
        print(new_user.user_id)
        flash("Account creation successfull","success")
        
        return redirect(url_for('sign_in'))
        
    return render_template('sigin.html')






#Expense-edit
@app.route('/edit/<int:id>',methods=['GET','POST'])
@login_required
def edit(id):
    expense=Expense.query.get_or_404(id)
    if expense.user!= session['user']:
        flash("Unauthorised access","danger ")
        return redirect(url_for('expense'))
    if request.method=='POST':
        name=request.form.get('expense')
        amount=request.form.get('amount')
        
        if not name:
            flash("Expense can not be empty","edit expense error")
            return redirect(url_for('edit',id=id))
        
        try:
            amount=float(amount)
        except ValueError:
            flash("Amount must be in positive Integers","edit amount error")
            return redirect(url_for('edit',id=id))
        expense.name=name
        expense.amount=amount
        db.session.commit()
        
        flash("Expense updated succesfully")
        return redirect(url_for('edit',id=id))
    return render_template("edit.html", expense=expense)    
        
        

#expense-route
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
        #adding-expense
        db.session.add(new_expense)
        db.session.commit()
        flash("Expense added","success")
        return redirect(url_for('expense'))

    
    expenses = Expense.query.filter_by(user=session['user']).all()
    return render_template("Expense.html", expenses=expenses)
    
    
@app.route('/delete/<int:id>', methods=["POST"])
@login_required
def delete(id):
    expense=Expense.query.get_or_404(id)
    if expense.user != session['user']:
        flash("Unauthorised access", "danger ")
        return redirect(url_for('expense'))
    
    db.session.delete(expense)
    db.session.commit()

    flash("Expense deleted succesfully","success")
    return redirect(url_for('expense'))    
              
    
    
#database-creation 
with app.app_context():
    db.create_all()

    

if __name__ == '__main__':
    app.run(debug=True)