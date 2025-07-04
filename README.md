# Earthsafe Receipt Scanner

This project is a simple Flask application that sends uploaded receipt
images or PDFs to Amazon Textract's `AnalyzeExpense` API and displays the
parsed data.

## Setup
1. Create a Python virtual environment and activate it.
2. Install dependencies with pip or run the provided helper script:
   ```bash
   pip install -r requirements.txt
   # or simply
   ./setup.sh
   ```
   The script first checks for wheel files inside `wheels/` and installs
   them if present. You can pre-download wheels using:
   `pip download -d wheels -r requirements.txt` on a machine with
   internet access. Otherwise it falls back to fetching packages from
   PyPI, which requires a connection.
3. Ensure your AWS credentials are configured so `boto3` can access
   Textract.
4. Run the app:
   ```bash
   python app.py
   ```

The application will create a local SQLite database (`receipts.db`) and
an `uploads/` directory for storing documents.

The app provides pages to upload receipts, browse uploaded documents, and view an aggregated dashboard of extraction results.
