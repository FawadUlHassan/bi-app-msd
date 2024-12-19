import os
import csv
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mysqldb import MySQL
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length
from werkzeug.security import generate_password_hash, check_password_hash
import plotly.graph_objs as go
import plotly.io as pio
import json
import re

# Initialize the app
app = Flask(__name__)
app.config.from_object('config.Config')

# Initialize MySQL
mysql = MySQL(app)

def convert_to_numeric(value):
    val_str = str(value).strip()

    # Remove leading alphabets (e.g. currency) and spaces
    val_str = re.sub(r'^[A-Za-z\s]+', '', val_str)
    # Remove commas
    val_str = val_str.replace(',', '')

    percentage = False
    if val_str.endswith('%'):
        percentage = True
        val_str = val_str[:-1].strip()

    try:
        num = float(val_str)
        # If you want to convert percentages to actual percents (e.g. "50%" -> 50.0):
        # it's already done by just removing '%' above.
        # If you wanted "50%" to become 0.5, you would do:
        # if percentage:
        #     num = num / 100.0
        return num
    except ValueError:
        return None

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'csv'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Create uploads directory if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Registration Form
class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=50)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

# Login Form
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        username = form.username.data.strip()
        email = form.email.data.strip()
        password = generate_password_hash(form.password.data)
        
        # Check if username or email already exists
        cur = mysql.connection.cursor()
        cur.execute("SELECT id FROM users WHERE username = %s OR email = %s", (username, email))
        existing_user = cur.fetchone()
        if existing_user:
            flash('Username or email already exists!', 'danger')
        else:
            cur.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s)", (username, email, password))
            mysql.connection.commit()
            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('login'))
        cur.close()

    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
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
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'danger')

    return render_template('login.html', form=form)

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Please log in to access the dashboard', 'danger')
        return redirect(url_for('login'))
    return render_template('dashboard.html', username=get_username())

def get_username():
    if 'user_id' in session:
        cur = mysql.connection.cursor()
        cur.execute("SELECT username FROM users WHERE id = %s", (session['user_id'],))
        user = cur.fetchone()
        cur.close()
        return user[0] if user else None
    return None


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'user_id' not in session:
        flash('Please log in to access the upload page', 'danger')
        return redirect(url_for('login'))

    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part in the request', 'danger')
            return redirect(url_for('upload'))

        file = request.files['file']

        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect(url_for('upload'))

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            with open(filepath, newline='') as csvfile:
                reader = csv.reader(csvfile, delimiter=',')
                rows = list(reader)

                if not rows:
                    flash('Uploaded CSV is empty', 'info')
                    return redirect(url_for('upload'))

                headers = rows[0]
                data_rows = rows[1:]  # Actual data rows

                cur = mysql.connection.cursor()
                cur.execute("TRUNCATE TABLE uploaded_data_json")

                for row in data_rows:
                    if len(row) == len(headers):
                        row_dict = dict(zip(headers, row))
                        numeric_data = {}
                        for k, v in row_dict.items():
                            numeric_val = convert_to_numeric(v)
                            numeric_data[k] = numeric_val

                        final_dict = {
                            "original": row_dict,
                            "numeric": numeric_data
                        }

                        json_data = json.dumps(final_dict)
                        cur.execute("INSERT INTO uploaded_data_json (row_data) VALUES (%s)", (json_data,))

                mysql.connection.commit()
                cur.close()

            flash('File uploaded and data saved successfully!', 'success')
            return redirect(url_for('visualization'))
        else:
            flash('Invalid file type. Please upload a CSV file.', 'danger')
            return redirect(url_for('upload'))

    return render_template('upload.html')


@app.route('/visualization')
def visualization():
    if 'user_id' not in session:
        flash('Please log in to access visualization', 'danger')
        return redirect(url_for('login'))

    cur = mysql.connection.cursor()
    cur.execute("SELECT row_data FROM uploaded_data_json")
    rows = cur.fetchall()
    cur.close()

    if not rows:
        flash('No data available. Please upload a CSV file first.', 'info')
        return redirect(url_for('upload'))

    parsed_rows = []
    for r in rows:
        try:
            parsed = json.loads(r[0])  # parsed['original'], parsed['numeric']
            parsed_rows.append(parsed)
        except Exception as e:
            print("Error parsing JSON:", e)

    if not parsed_rows:
        flash('No valid data to visualize.', 'info')
        return redirect(url_for('upload'))

    # All keys are taken from 'original' since it's guaranteed all rows share same keys
    all_keys = list(parsed_rows[0]["original"].keys())

    data_json = json.dumps(parsed_rows)
    columns_json = json.dumps(all_keys)

    return render_template('visualization.html', data_json=data_json, columns_json=columns_json)


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

