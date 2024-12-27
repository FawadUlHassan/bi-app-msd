# my_bi_tool/routes/main.py
from flask import Blueprint, render_template, session, flash, redirect, url_for
from my_bi_tool.extensions import mysql

main_bp = Blueprint('main', __name__, template_folder='../../templates')

@main_bp.route('/')
def index():
    # You can redirect '/' straight to '/dashboard' or show a landing page
    return redirect(url_for('main.dashboard'))

@main_bp.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Please log in to access the dashboard', 'danger')
        return redirect(url_for('auth.login'))
    return render_template('dashboard.html', username=get_username())

def get_username():
    if 'user_id' in session:
        cur = mysql.connection.cursor()
        cur.execute("SELECT username FROM users WHERE id = %s", (session['user_id'],))
        user = cur.fetchone()
        cur.close()
        return user[0] if user else None
    return None

