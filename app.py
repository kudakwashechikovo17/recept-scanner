from flask import Flask, render_template, request
import boto3

app = Flask(__name__)
textract = boto3.client('textract')   # picks up your AWS creds & region

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
        summary, items = extract_receipt(file)
        return render_template('results.html', summary=summary, items=items)
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
