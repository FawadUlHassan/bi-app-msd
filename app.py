import os
import csv
import json
import re
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mysqldb import MySQL
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config.from_object('config.Config')

mysql = MySQL(app)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'csv'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def detect_type(value):
    """Dynamically detect type: currency, percentage, numeric, date, or text."""
    if value is None:
        return "text", None

    val = str(value).strip()
    if not val:
        return "text", None

    # Check for percentage
    if val.endswith('%'):
        try:
            return "percentage", float(val.rstrip('%').strip())
        except ValueError:
            return "text", val

    # Check for currency (approx. logic)
    currency_pattern = r'^[A-Za-z\.\s]*[\d,]+(\.\d+)?$'
    if re.match(currency_pattern, val):
        try:
            numeric = float(re.sub(r'[^\d\.]', '', val))
            return "currency", numeric
        except ValueError:
            return "text", val

    # Check numeric
    try:
        return "numeric", float(val)
    except ValueError:
        pass

    # Check date
    date_formats = ['%d-%b-%y', '%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y']
    for fmt in date_formats:
        try:
            dt = datetime.strptime(val, fmt)
            return "date", dt.strftime('%Y-%m-%d')
        except ValueError:
            continue

    # Default to text
    return "text", val


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=50)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

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

        cur = mysql.connection.cursor()
        cur.execute("SELECT id FROM users WHERE username = %s OR email = %s", (username, email))
        existing_user = cur.fetchone()
        if existing_user:
            flash('Username or email already exists!', 'danger')
        else:
            cur.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
                        (username, email, password))
            mysql.connection.commit()
            cur.close()
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

            with open(filepath, newline='', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile, delimiter=',')
                rows = list(reader)
                if not rows:
                    flash('Uploaded CSV is empty', 'info')
                    return redirect(url_for('upload'))

                headers = rows[0]
                data_rows = rows[1:]

                cur = mysql.connection.cursor()
                cur.execute("TRUNCATE TABLE uploaded_data_json")

                # We'll gather stats for numeric columns for a simple data science summary
                numericTrackers = {h: [] for h in headers}

                for rowVals in data_rows:
                    if len(rowVals) == len(headers):
                        row_dict = dict(zip(headers, rowVals))
                        processed_data = {}
                        types_data = {}

                        for k, v in row_dict.items():
                            dtype, val = detect_type(v)
                            processed_data[k] = val
                            types_data[k] = dtype
                            # If numeric, store in numericTrackers
                            if dtype in ['numeric','currency','percentage']:
                                numericTrackers[k].append(val)

                        final_dict = {
                            "original": row_dict,
                            "processed": processed_data,
                            "types": types_data
                        }

                        json_data = json.dumps(final_dict, ensure_ascii=False)
                        cur.execute("INSERT INTO uploaded_data_json (row_data) VALUES (%s)", (json_data,))

                # Quick data science summary for numeric columns
                ds_summary = {}
                for k, arr in numericTrackers.items():
                    valid = [x for x in arr if x is not None]
                    if valid:
                        ds_summary[k] = {
                            "count": len(valid),
                            "min": min(valid),
                            "max": max(valid),
                            "mean": sum(valid)/len(valid),
                            "distinct": len(set(valid))
                        }

                # We store ds_summary as a single row with row_data='__SUMMARY__'
                summary_json = json.dumps({"ds_summary": ds_summary}, ensure_ascii=False)
                cur.execute("INSERT INTO uploaded_data_json (row_data) VALUES (%s)", (summary_json,))

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
    ds_summary = {}
    for r in rows:
        try:
            parsed = json.loads(r[0])  # => { original, processed, types } or { ds_summary }
            if "ds_summary" in parsed:
                ds_summary = parsed["ds_summary"]
            else:
                parsed_rows.append(parsed)
        except Exception as e:
            print("Error parsing JSON:", e)

    if not parsed_rows:
        flash('No valid data to visualize.', 'info')
        return redirect(url_for('upload'))

    all_keys = list(parsed_rows[0]["original"].keys())
    data_json = json.dumps(parsed_rows, ensure_ascii=False)
    columns_json = json.dumps(all_keys, ensure_ascii=False)
    ds_summary_json = json.dumps(ds_summary, ensure_ascii=False)

    return render_template('visualization.html', 
                           data_json=data_json, 
                           columns_json=columns_json,
                           ds_summary_json=ds_summary_json)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
