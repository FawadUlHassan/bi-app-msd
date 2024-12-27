# my_bi_tool/routes/data.py
import os
import csv
import json
import re
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.utils import secure_filename
from my_bi_tool.extensions import mysql

data_bp = Blueprint('data', __name__, template_folder='../../templates')

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'csv'}

# Ensure upload directory exists
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

@data_bp.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'user_id' not in session:
        flash('Please log in to access the upload page', 'danger')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part in the request', 'danger')
            return redirect(url_for('data.upload'))

        file = request.files['file']
        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect(url_for('data.upload'))

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)

            with open(filepath, newline='', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile, delimiter=',')
                rows = list(reader)
                if not rows:
                    flash('Uploaded CSV is empty', 'info')
                    return redirect(url_for('data.upload'))

                headers = rows[0]
                data_rows = rows[1:]

                cur = mysql.connection.cursor()
                # CAREFUL: This TRUNCATE will remove existing data.
                # For multi-file support, you should store each upload in a separate table or with an upload_id.
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
                            if dtype in ['numeric', 'currency', 'percentage']:
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
            return redirect(url_for('data.visualization'))
        else:
            flash('Invalid file type. Please upload a CSV file.', 'danger')
            return redirect(url_for('data.upload'))

    return render_template('upload.html')

@data_bp.route('/visualization')
def visualization():
    if 'user_id' not in session:
        flash('Please log in to access visualization', 'danger')
        return redirect(url_for('auth.login'))

    cur = mysql.connection.cursor()
    cur.execute("SELECT row_data FROM uploaded_data_json")
    rows = cur.fetchall()
    cur.close()

    if not rows:
        flash('No data available. Please upload a CSV file first.', 'info')
        return redirect(url_for('data.upload'))

    parsed_rows = []
    ds_summary = {}
    for r in rows:
        try:
            parsed = json.loads(r[0])
            if "ds_summary" in parsed:
                ds_summary = parsed["ds_summary"]
            else:
                parsed_rows.append(parsed)
        except Exception as e:
            print("Error parsing JSON:", e)

    if not parsed_rows:
        flash('No valid data to visualize.', 'info')
        return redirect(url_for('data.upload'))

    all_keys = list(parsed_rows[0]["original"].keys())
    data_json = json.dumps(parsed_rows, ensure_ascii=False)
    columns_json = json.dumps(all_keys, ensure_ascii=False)
    ds_summary_json = json.dumps(ds_summary, ensure_ascii=False)

    return render_template('visualization.html',
                           data_json=data_json,
                           columns_json=columns_json,
                           ds_summary_json=ds_summary_json)
