# my_bi_tool/routes/auth.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from my_bi_tool.extensions import mysql
from my_bi_tool.forms.auth_forms import RegistrationForm, LoginForm

auth_bp = Blueprint('auth', __name__, template_folder='../../templates')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        username = form.username.data.strip()
        email = form.email.data.strip()
        hashed_pw = generate_password_hash(form.password.data)

        cur = mysql.connection.cursor()
        cur.execute("SELECT id FROM users WHERE username = %s OR email = %s", (username, email))
        existing_user = cur.fetchone()
        if existing_user:
            flash('Username or email already exists!', 'danger')
        else:
            cur.execute("""
                INSERT INTO users (username, email, password)
                VALUES (%s, %s, %s)
            """, (username, email, hashed_pw))
            mysql.connection.commit()
            cur.close()
            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('auth.login'))
        cur.close()

    return render_template('register.html', form=form)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data.strip()
        password_input = form.password.data

        cur = mysql.connection.cursor()
        cur.execute("SELECT id, password FROM users WHERE username = %s", (username,))
        user = cur.fetchone()
        cur.close()

        if user and check_password_hash(user[1], password_input):
            session['user_id'] = user[0]
            flash('Login successful!', 'success')
            return redirect(url_for('main.dashboard'))
        else:
            flash('Invalid username or password', 'danger')

    return render_template('login.html', form=form)

@auth_bp.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))

