# my_bi_tool/routes/data.py

import os
import csv
import json
import re
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.utils import secure_filename
from my_bi_tool.extensions import mysql

data_bp = Blueprint('data', __name__, template_folder='../../templates')

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'csv'}

# For chunk-based reading of large CSVs
CHUNK_SIZE = 5000

# Ensure the upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def detect_type(value):
    """
    Dynamically detect type: currency, percentage, numeric, date, or text.
    More robust fallback to text if parsing fails.
    """
    if value is None:
        return "text", None

    val = str(value).strip()
    if not val:
        return "text", None

    # Attempt percentage
    if val.endswith('%'):
        try:
            inner = val[:-1].strip()
            return "percentage", float(inner)
        except ValueError:
            pass

    # Attempt currency
    currency_pattern = r'^[$€¥₤]?[A-Za-z\s]*[\d,]+(\.\d+)?$'
    if re.match(currency_pattern, val):
        try:
            numeric = float(re.sub(r'[^\d\.]', '', val))
            return "currency", numeric
        except ValueError:
            pass

    # Attempt numeric
    try:
        # Remove commas for e.g. "1,234" -> 1234
        return "numeric", float(val.replace(',', ''))
    except ValueError:
        pass

    # Attempt date
    date_formats = [
        '%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%d-%b-%y', '%d-%b-%Y',
        '%Y.%m.%d', '%d.%m.%Y', '%m.%d.%Y', '%d %b %Y', '%b %d %Y',
        '%d %B %Y', '%B %d %Y'
    ]
    for fmt in date_formats:
        try:
            dt = datetime.strptime(val, fmt)
            return "date", dt.strftime('%Y-%m-%d')
        except ValueError:
            pass

    # Fallback text
    return "text", val

@data_bp.route('/upload', methods=['GET', 'POST'])
def upload():
    """
    Chunk-based CSV upload to handle large files.
    """
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

            # Insert into uploads
            cur = mysql.connection.cursor()
            cur.execute("""
                INSERT INTO uploads (user_id, filename, uploaded_at)
                VALUES (%s, %s, %s)
            """, (session['user_id'], filename, datetime.now()))
            upload_id = cur.lastrowid

            numericTrackers = {}
            headers = None
            total_rows_inserted = 0

            with open(filepath, 'r', encoding='utf-8', newline='') as csvfile:
                reader = csv.reader(csvfile)
                chunk_data = []

                for i, row_vals in enumerate(reader):
                    if i == 0:
                        # First row => headers
                        headers = row_vals
                        numericTrackers = {h: [] for h in headers}
                        continue

                    chunk_data.append(row_vals)

                    # If chunk is large enough, process
                    if len(chunk_data) >= CHUNK_SIZE:
                        total_rows_inserted += process_chunk(chunk_data, headers, numericTrackers, upload_id, cur)
                        chunk_data.clear()

                # leftover rows
                if chunk_data:
                    total_rows_inserted += process_chunk(chunk_data, headers, numericTrackers, upload_id, cur)

            # Summaries
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

            summary_json = json.dumps({"ds_summary": ds_summary}, ensure_ascii=False)
            cur.execute("""
                INSERT INTO uploaded_data_json (upload_id, row_data)
                VALUES (%s, %s)
            """, (upload_id, summary_json))

            mysql.connection.commit()
            cur.close()

            flash(f'File "{filename}" uploaded successfully! Rows processed: {total_rows_inserted}', 'success')
            return redirect(url_for('data.my_uploads'))
        else:
            flash('Invalid file type. Please upload a CSV file.', 'danger')
            return redirect(url_for('data.upload'))

    return render_template('upload.html')

def process_chunk(chunk_data, headers, numericTrackers, upload_id, cursor):
    """
    Insert chunk of rows and update numeric trackers.
    """
    rows_inserted = 0
    for rowVals in chunk_data:
        if len(rowVals) != len(headers):
            # skip mismatch
            continue

        row_dict = dict(zip(headers, rowVals))
        processed_data = {}
        types_data = {}

        for k, v in row_dict.items():
            dtype, val = detect_type(v)
            processed_data[k] = val
            types_data[k] = dtype
            if dtype in ['numeric', 'currency', 'percentage']:
                numericTrackers[k].append(val)

        final_dict = {
            "original": row_dict,
            "processed": processed_data,
            "types": types_data
        }
        json_data = json.dumps(final_dict, ensure_ascii=False)
        cursor.execute("""
            INSERT INTO uploaded_data_json (upload_id, row_data)
            VALUES (%s, %s)
        """, (upload_id, json_data))
        rows_inserted += 1
    return rows_inserted

@data_bp.route('/my_uploads')
def my_uploads():
    if 'user_id' not in session:
        flash('Please log in first', 'danger')
        return redirect(url_for('auth.login'))

    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT id, filename, uploaded_at
        FROM uploads
        WHERE user_id = %s
        ORDER BY uploaded_at DESC
    """, (session['user_id'],))
    files = cur.fetchall()
    cur.close()

    return render_template('my_uploads.html', files=files)

@data_bp.route('/visualization/<int:upload_id>')
def visualization(upload_id):
    """
    Visualization page for a specific upload_id.
    """
    if 'user_id' not in session:
        flash('Please log in to access visualization', 'danger')
        return redirect(url_for('auth.login'))

    cur = mysql.connection.cursor()
    cur.execute("SELECT row_data FROM uploaded_data_json WHERE upload_id = %s", (upload_id,))
    rows = cur.fetchall()
    cur.close()

    if not rows:
        flash('No data available for this file. Please upload a CSV first.', 'info')
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
        flash('No valid data to visualize for this upload.', 'info')
        return redirect(url_for('data.upload'))

    all_keys = list(parsed_rows[0]["original"].keys())
    data_json = json.dumps(parsed_rows, ensure_ascii=False)
    columns_json = json.dumps(all_keys, ensure_ascii=False)
    ds_summary_json = json.dumps(ds_summary, ensure_ascii=False)

    return render_template(
        'visualization.html',
        upload_id=upload_id,
        data_json=data_json,
        columns_json=columns_json,
        ds_summary_json=ds_summary_json
    )

# ------------------- SAVED CHARTS SECTION ------------------

@data_bp.route('/save_chart/<int:upload_id>', methods=['POST'])
def save_chart(upload_id):
    """
    Save the current chart config to the `charts` table.
    Expects JSON in the request body with fields like:
    {
      "chartTitle": "My Chart",
      "chartType": "bar",
      "xCols": [...],
      "yCols": [...],
      "xKeyword": "...",
      "yKeyword": "..."
    }
    """
    if 'user_id' not in session:
        return jsonify({"success": False, "error": "Unauthorized"}), 401

    chart_data = request.get_json()
    if not chart_data:
        return jsonify({"success": False, "error": "No chart data"}), 400

    chart_title = chart_data.get('chartTitle', 'Untitled Chart')
    config_json = json.dumps(chart_data)

    user_id = session['user_id']
    cur = mysql.connection.cursor()
    cur.execute("""
        INSERT INTO charts (user_id, upload_id, chart_title, config_json, created_at, updated_at)
        VALUES (%s, %s, %s, %s, NOW(), NOW())
    """, (user_id, upload_id, chart_title, config_json))
    mysql.connection.commit()
    new_id = cur.lastrowid
    cur.close()

    return jsonify({"success": True, "chart_id": new_id})

@data_bp.route('/my_charts')
def my_charts():
    """
    Lists all saved charts for the current user.
    """
    if 'user_id' not in session:
        flash('Please log in first', 'danger')
        return redirect(url_for('auth.login'))

    user_id = session['user_id']
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT id, upload_id, chart_title, created_at
        FROM charts
        WHERE user_id = %s
        ORDER BY created_at DESC
    """, (user_id,))
    charts_list = cur.fetchall()
    cur.close()

    return render_template('my_charts.html', charts_list=charts_list)

@data_bp.route('/load_chart/<int:chart_id>')
def load_chart(chart_id):
    """
    Load chart config from DB and redirect to the relevant visualization page with that config.
    We'll pass the config via query params or session, or re-render a specialized template.
    """
    if 'user_id' not in session:
        flash('Please log in first', 'danger')
        return redirect(url_for('auth.login'))

    user_id = session['user_id']
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT upload_id, chart_title, config_json
        FROM charts
        WHERE id = %s AND user_id = %s
    """, (chart_id, user_id))
    row = cur.fetchone()
    cur.close()

    if not row:
        flash('Chart not found or you do not have permission.', 'danger')
        return redirect(url_for('data.my_charts'))

    upload_id, chart_title, config_json = row
    # We can pass the chart config as JSON in the template or in session
    # For demonstration, let's store in session temporarily
    session['temp_chart_config'] = config_json

    # Redirect to the visualization page. The front-end can fetch the stored config from session or another endpoint.
    return redirect(url_for('data.visualization', upload_id=upload_id))

# ------------------- PIVOT TABLE SECTION (OPTIONAL) --------

@data_bp.route('/pivot_table/<int:upload_id>')
def pivot_table(upload_id):
    """
    Example pivot table route using pandas.
    This is optional. Requires 'pandas' in your environment.
    Installs: pip install pandas
    """
    import pandas as pd

    if 'user_id' not in session:
        flash('Please log in first', 'danger')
        return redirect(url_for('auth.login'))

    # Load rows
    cur = mysql.connection.cursor()
    cur.execute("SELECT row_data FROM uploaded_data_json WHERE upload_id = %s", (upload_id,))
    rows = cur.fetchall()
    cur.close()

    if not rows:
        flash('No data found for pivot.', 'info')
        return redirect(url_for('data.upload'))

    data_list = []
    for r in rows:
        parsed = json.loads(r[0])
        if "ds_summary" not in parsed:
            data_list.append(parsed["processed"])

    if not data_list:
        flash('No valid data to pivot.', 'info')
        return redirect(url_for('data.upload'))

    df = pd.DataFrame(data_list)  # Each 'processed' row is a dict
    # Build a simple pivot - for demo let's just do a basic grouping
    # We'll pass the pivot result as HTML
    # For a more dynamic approach, you'd parse user form input for the pivot grouping
    pivot = df.pivot_table(
        index=None,        # or a column name e.g. ["Region"]
        values=None,       # or a numeric column e.g. ["Sales"]
        aggfunc='count'    # or sum, avg, etc.
    )

    pivot_html = pivot.to_html(classes='table table-bordered table-sm')

    return render_template('pivot_table.html', pivot_html=pivot_html, upload_id=upload_id)

