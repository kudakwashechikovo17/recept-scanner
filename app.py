import os
import json
import sqlite3
from datetime import datetime
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    send_from_directory,
)
import boto3

app = Flask(__name__)
textract = boto3.client('textract')   # picks up your AWS creds & region

UPLOAD_FOLDER = 'uploads'
DB_PATH = 'receipts.db'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """CREATE TABLE IF NOT EXISTS receipts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            summary TEXT,
            items TEXT,
            uploaded_at TEXT
        )"""
    )
    conn.close()


init_db()

def extract_receipt(file_stream):
    resp = textract.analyze_expense(Document={'Bytes': file_stream.read()})
    docs = resp.get('ExpenseDocuments', [])
    if not docs:
        return {}, []

    # Summary fields (vendor, date, total, etc.)
    summary = {
        fld['Type']['Text']: fld['ValueDetection']['Text']
        for fld in docs[0].get('SummaryFields', [])
    }

    # Line-item details
    items = []
    for group in docs[0].get('LineItemGroups', []):
        for line in group.get('LineItems', []):
            items.append({
                f['Type']['Text']: f['ValueDetection']['Text']
                for f in line.get('LineItemExpenseFields', [])
            })

    return summary, items

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file = request.files.get('document')
        if not file:
            return render_template('index.html', error="Please upload a file.")

        filename = datetime.utcnow().strftime('%Y%m%d%H%M%S_') + file.filename
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        with open(filepath, 'rb') as f:
            summary, items = extract_receipt(f)

        conn = sqlite3.connect(DB_PATH)
        conn.execute(
            'INSERT INTO receipts (filename, summary, items, uploaded_at) VALUES (?, ?, ?, ?)',
            (filename, json.dumps(summary), json.dumps(items), datetime.utcnow().isoformat())
        )
        receipt_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
        conn.commit()
        conn.close()

        return redirect(url_for('receipt_detail', receipt_id=receipt_id))

    return render_template('index.html')


@app.route('/receipts')
def receipts():
    conn = sqlite3.connect(DB_PATH)
    receipts = conn.execute('SELECT id, filename, uploaded_at FROM receipts ORDER BY uploaded_at DESC').fetchall()
    conn.close()
    return render_template('receipts.html', receipts=receipts)


@app.route('/dashboard')
def dashboard():
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        'SELECT id, filename, uploaded_at, summary FROM receipts ORDER BY uploaded_at DESC'
    ).fetchall()
    conn.close()
    receipts = []
    for row in rows:
        rid, filename, uploaded_at, summary_json = row
        summary = json.loads(summary_json)
        vendor = summary.get('VENDOR_NAME') or summary.get('VENDOR') or summary.get('MerchantName')
        total = summary.get('TOTAL') or summary.get('TOTAL_AMOUNT') or summary.get('Total')
        date = (
            summary.get('INVOICE_RECEIPT_DATE')
            or summary.get('DATE')
            or summary.get('PurchaseDate')
        )
        receipts.append((rid, filename, vendor or '', date or '', total or '', uploaded_at))

    return render_template('dashboard.html', receipts=receipts)


@app.route('/receipts/<int:receipt_id>')
def receipt_detail(receipt_id):
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute('SELECT filename, summary, items, uploaded_at FROM receipts WHERE id=?', (receipt_id,)).fetchone()
    conn.close()
    if row:
        filename, summary_json, items_json, uploaded_at = row
        summary = json.loads(summary_json)
        items = json.loads(items_json)
        return render_template(
            'results.html', summary=summary, items=items, file=filename, uploaded_at=uploaded_at
        )
    return 'Receipt not found', 404


@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

if __name__ == '__main__':
    app.run(debug=True)
