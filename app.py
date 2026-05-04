import os
import csv
import json
import uuid
import hashlib
from datetime import datetime
from flask import Flask, request, jsonify, render_template, send_file
import stripe

app = Flask(__name__)
app.secret_key = os.urandom(24).hex()

# Stripe config from env vars
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY', '')
STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY', '')

UPLOAD_FOLDER = "uploads"
RESULTS_FOLDER = "results"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULTS_FOLDER, exist_ok=True)

def process_csv(filepath, operation):
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    results = []
    if operation == "deduplicate":
        seen = set()
        for row in rows:
            key = tuple(row.values())
            if key not in seen:
                seen.add(key)
                results.append(row)
    elif operation == "extract_emails":
        import re
        pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        for row in rows:
            text = ' '.join(str(v) for v in row.values())
            for email in re.findall(pattern, text):
                results.append({"extracted_emails": email})
        if not results:
            results = [{"extracted_emails": "No emails found"}]
    elif operation == "clean_whitespace":
        for row in rows:
            results.append({k: ' '.join(str(v).split()) for k, v in row.items()})
    elif operation == "fill_empty":
        for row in rows:
            for k, v in row.items():
                if not v or str(v).strip() == '':
                    row[k] = 'N/A'
            results.append(row)
    else:
        results = rows
    
    result_id = hashlib.md5(str(datetime.now()).encode()).hexdigest()[:12]
    result_path = os.path.join(RESULTS_FOLDER, f"{result_id}.csv")
    
    if results:
        with open(result_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)
    
    return result_path, len(rows), len(results)

@app.route('/')
def index():
    return render_template('index.html', stripe_key=STRIPE_PUBLISHABLE_KEY)

@app.route('/process', methods=['POST'])
def process_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    file = request.files['file']
    operation = request.form.get('operation', 'deduplicate')
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    file_id = uuid.uuid4().hex[:12]
    upload_path = os.path.join(UPLOAD_FOLDER, f"{file_id}.csv")
    file.save(upload_path)
    
    try:
        result_path, original_count, result_count = process_csv(upload_path, operation)
        os.remove(upload_path)
        return jsonify({
            "success": True,
            "result_id": os.path.basename(result_path).replace('.csv', ''),
            "original_rows": original_count,
            "result_rows": result_count,
            "download_url": f"/download/{os.path.basename(result_path).replace('.csv', '')}"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/download/<result_id>')
def download(result_id):
    result_path = os.path.join(RESULTS_FOLDER, f"{result_id}.csv")
    if os.path.exists(result_path):
        return send_file(result_path, as_attachment=True, download_name=f"cleaned_{result_id}.csv")
    return jsonify({"error": "File not found"}), 404

@app.route('/create-checkout-session', methods=['POST'])
def create_checkout():
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'aud',
                    'product_data': {'name': 'CSV Cleaner Pro - 10 Credits'},
                    'unit_amount': 1990,
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=request.host_url,
            cancel_url=request.host_url,
        )
        return jsonify({'url': session.url})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/create-subscription', methods=['POST'])
def create_subscription():
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'aud',
                    'product_data': {'name': 'CSV Cleaner Pro - Monthly'},
                    'unit_amount': 999,
                    'recurring': {'interval': 'month'},
                },
                'quantity': 1,
            }],
            mode='subscription',
            success_url=request.host_url,
            cancel_url=request.host_url,
        )
        return jsonify({'url': session.url})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
