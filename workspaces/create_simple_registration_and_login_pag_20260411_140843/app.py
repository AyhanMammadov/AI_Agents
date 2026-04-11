from flask import Flask, render_template, request, redirect, url_for, session, flash
from models import db, User
from forms import validate_registration, validate_login
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'devkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

@app.before_first_request
def create_tables():
    db.create_all()

@app.route('/')
def index():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        return render_template('base.html', user=user)
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    errors = {}
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm', '')
        errors = validate_registration(name, email, password, confirm)
        if not errors:
            if User.query.filter_by(email=email).first():
                errors['email'] = 'Email уже зарегистрирован.'
            else:
                user = User(name=name, email=email, password_hash=generate_password_hash(password))
                db.session.add(user)
                db.session.commit()
                flash('Регистрация успешна. Войдите в систему.')
                return redirect(url_for('login'))
    return render_template('register.html', errors=errors)

@app.route('/login', methods=['GET', 'POST'])
def login():
    errors = {}
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        errors = validate_login(email, password)
        if not errors:
            user = User.query.filter_by(email=email).first()
            if user and check_password_hash(user.password_hash, password):
                session['user_id'] = user.id
                return redirect(url_for('index'))
            else:
                errors['general'] = 'Неверный email или пароль.'
    return render_template('login.html', errors=errors)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
