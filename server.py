from flask import Flask, request, jsonify
import mysql.connector
import joblib
import smtplib
import os

app = Flask(__name__)  # ✅ Corrected Flask initialization

# ✅ Check if the AI model file exists before loading
MODEL_PATH = "donor_match_model.pkl"

if os.path.exists(MODEL_PATH):
    model = joblib.load(MODEL_PATH)
    print("✅ Model loaded successfully!")
else:
    print("❌ Model file not found! Train and save donor_match_model.pkl first.")
    model = None  # Avoid breaking the app

# ✅ Connect to MySQL Database with error handling
try:
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",  # Make sure your MySQL password is correct
        database="food_donation"
    )
    cursor = conn.cursor()
    print("✅ Connected to MySQL Database!")
except mysql.connector.Error as err:
    print(f"❌ MySQL Connection Error: {err}")
    cursor = None

# ✅ SMTP Email Configuration (Replace with actual credentials)
EMAIL_USER = "your_email@gmail.com"
EMAIL_PASS = "your_password"

def send_email(to_email, subject, message):
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)
        server.sendmail(EMAIL_USER, to_email, f"Subject: {subject}\n\n{message}")
        server.quit()
        print(f"✅ Email sent to {to_email}")
    except Exception as e:
        print(f"❌ Email sending failed: {e}")

# ✅ Match donor using AI model
@app.route("/match-donor", methods=["POST"])
def match_donor():
    if model is None:
        return jsonify({"error": "❌ AI Model not loaded. Train and save donor_match_model.pkl!"}), 500

    if cursor is None:
        return jsonify({"error": "❌ Database connection failed!"}), 500

    data = request.json
    food_needed, quantity = data.get("food_needed"), data.get("quantity")

    cursor.execute("SELECT id, food, quantity, email FROM suppliers WHERE status='Available'")
    donors = cursor.fetchall()
    
    if not donors:
        return jsonify({"message": "❌ No donors available!"})

    try:
        # ✅ AI Model Prediction (Handle unexpected inputs safely)
        donor_index = model.kneighbors([[food_needed, quantity]], return_distance=False)[0][0]
        donor_id, donor_food, donor_quantity, donor_email = donors[donor_index]
        
        # ✅ Update requester status in database
        cursor.execute("UPDATE requesters SET status='Matched' WHERE email=%s", (data["email"],))
        conn.commit()

        # ✅ Notify donor via email
        send_email(donor_email, "Food Donation Request", f"A requester needs {food_needed}. Please contact them.")

        return jsonify({"message": "✅ Donor matched and notified!"})
    
    except Exception as e:
        return jsonify({"error": f"❌ AI Model error: {str(e)}"}), 500

# ✅ Check food expiry and notify donors
@app.route("/check-expiry", methods=["GET"])
def check_expiry():
    if cursor is None:
        return jsonify({"error": "❌ Database connection failed!"}), 500

    cursor.execute("SELECT email, food, expiry_date FROM suppliers WHERE expiry_date <= CURDATE() + INTERVAL 2 DAY")
    expiring_food = cursor.fetchall()

    for email, food, expiry_date in expiring_food:
        send_email(email, "Food Expiry Alert", f"Your food '{food}' is expiring on {expiry_date}. Please donate it soon.")

    return jsonify({"message": "✅ Expiry alerts sent!"})

# ✅ Start Flask Server
if __name__ == "__main__":
    app.run(debug=True)