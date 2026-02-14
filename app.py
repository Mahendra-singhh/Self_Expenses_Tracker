from flask import Flask, redirect, render_template, request, url_for, session,flash
from functools import wraps
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail,Message 
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///stu.db"
app.secret_key = 'my secret key'

db = SQLAlchemy(app)

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
    username = session.get('user')
    return render_template('profile.html', username=username)

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
    

if __name__ == '__main__':
    app.run(debug=True)
