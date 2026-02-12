from flask import Flask, request, jsonify, send_from_directory, abort
import hashlib
import os

app = Flask(__name__)

# ================= CONFIG =================
SECRET_KEY = "instamart_secure_key_2026"

# Folder where PDFs are stored
INVOICE_FOLDER = "invoices"

# In-memory DB (⚠ resets on restart)
ORDERS_DB = {}

# Ensure invoice folder exists
if not os.path.exists(INVOICE_FOLDER):
    os.makedirs(INVOICE_FOLDER)


# ================= HOME =================
@app.route("/")
def home():
    return "Instamart Verification Server Running ✅"


# ================= STORE ORDER =================
@app.route("/store-order", methods=["POST"])
def store_order():
    data = request.json
    order_id = str(data.get("order_id", "")).strip()

    if not order_id:
        return jsonify({"error": "Missing order_id"}), 400

    if "total" in data:
        data["total"] = format(float(data["total"]), ".2f")

    ORDERS_DB[order_id] = data

    return jsonify({
        "status": "Order stored successfully",
        "stored_order_id": order_id
    })


# ================= SERVE INVOICE PDF =================
@app.route("/invoices/<order_id>.pdf")
def serve_invoice(order_id):

    filename = f"{order_id}.pdf"
    file_path = os.path.join(INVOICE_FOLDER, filename)

    if not os.path.exists(file_path):
        return abort(404, "Invoice not found ❌")

    return send_from_directory(
        INVOICE_FOLDER,
        filename,
        mimetype="application/pdf",
        as_attachment=False  # IMPORTANT → opens in browser, no auto download
    )


# ================= VERIFY INVOICE =================
@app.route("/invoice")
def verify_invoice():

    order_id = request.args.get("id")
    total_from_url = request.args.get("total")
    hash_value = request.args.get("hash")

    if not order_id or not total_from_url or not hash_value:
        return "Invalid request", 400

    order = ORDERS_DB.get(order_id)

    if not order:
        return """
        <h2 style='text-align:center;margin-top:50px;'>
        Order not found ❌<br>
        <small>Server may have restarted. Please place new order.</small>
        </h2>
        """

    stored_total = format(float(order.get("total", "0")), ".2f")

    raw = f"{order_id}{stored_total}{SECRET_KEY}"
    valid_hash = hashlib.sha256(raw.encode()).hexdigest()

    if hash_value != valid_hash:
        return """
        <h2 style='color:red;text-align:center;margin-top:50px;'>
        Invoice Tampered ❌
        </h2>
        """

    # Build items HTML
    items_html = ""
    for item in order.get("items", []):
        items_html += f"""
        <div class="item-row">
            <span>{item['name']}</span>
            <span>x{item['qty']}</span>
        </div>
        """

    return f"""
    <html>
    <head>
        <title>Instamart Invoice Verification</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">

        <style>
        body {{
            font-family: Arial, sans-serif;
            background:#f5f6fa;
            padding:20px;
        }}

        .card {{
            max-width:520px;
            margin:auto;
            background:white;
            border-radius:16px;
            box-shadow:0 6px 18px rgba(0,0,0,0.08);
            overflow:hidden;
        }}

        .header {{
            background:#2656d9;
            padding:18px;
            text-align:center;
            color:white;
        }}

        .header-content {{
            display:flex;
            align-items:center;
            justify-content:center;
            gap:10px;
            font-size:18px;
            font-weight:bold;
        }}

        .logo {{
            height:32px;
            object-fit:contain;
        }}

        .section {{
            padding:20px;
            font-size:14px;
        }}

        .row {{
            margin:6px 0;
        }}

        .label {{
            font-weight:bold;
            color:#333;
        }}

        hr {{
            border:none;
            border-top:1px solid #eee;
            margin:14px 0;
        }}

        .verified-pill {{
            display:inline-block;
            background:#e9f7ef;
            color:#1b7f3a;
            padding:6px 16px;
            border-radius:50px;
            font-weight:bold;
            font-size:13px;
            margin-bottom:16px;
            border:1px solid #2ecc71;
        }}

        .items-box {{
            background:#fafafa;
            padding:12px;
            border-radius:8px;
            margin-top:8px;
        }}

        .item-row {{
            display:flex;
            justify-content:space-between;
            padding:4px 0;
        }}

        .total {{
            font-size:18px;
            color:#2656d9;
            font-weight:bold;
            margin-top:14px;
        }}
        </style>
    </head>

    <body>
        <div class="card">

            <div class="header">
                <div class="header-content">
                     
                    <span>Instamart Invoice</span>
                </div>
            </div>

            <div class="section">

                <div class="verified-pill">
                    ✔ VERIFIED
                </div>

                <div class="row">
                    <span class="label">Order ID:</span> #{order_id}
                </div>

                <div class="row">
                    <span class="label">Order Date:</span> {order.get('order_date','-')}
                </div>

                <div class="row">
                    <span class="label">Order Time:</span> {order.get('order_time','-')}
                </div>

                <div class="row">
                    <span class="label">Estimated Delivery:</span> {order.get('delivery_time','-')}
                </div>

                <hr>

                <div class="row">
                    <span class="label">Customer:</span> {order.get('customer_name','-')}
                </div>

                <div class="row">
                    <span class="label">Mobile:</span> {order.get('mobile','-')}
                </div>

                <div class="row">
                    <span class="label">Address:</span> {order.get('address','-')}
                </div>

                <hr>

                <div class="row">
                    <span class="label">Payment Mode:</span> {order.get('payment_mode','-')}
                </div>

                <div class="row">
                    <span class="label">Payment App / Bank:</span> {order.get('payment_app','-')}
                </div>

                <div class="row">
                    <span class="label">Platform:</span> {order.get('platform','-')}
                </div>

                <hr>

                <div class="label">Items Ordered:</div>

                <div class="items-box">
                    {items_html}
                </div>

                <hr>

                <div class="row">
                    <span class="label">Coupon Applied:</span> {order.get('coupon','N/A')}
                </div>

                <div class="total">
                    Total Paid: ₹{stored_total}
                </div>

            </div>
        </div>
    </body>
    </html>
    """


# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True)
