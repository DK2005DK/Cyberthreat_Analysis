from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import joblib  # For loading the ML model
import re
import os

app = Flask(__name__)
app.secret_key = "your_secret_key"

# Database setup
DATABASE = "users.db"

def create_database():
    """Creates user and analysis databases if not exists"""
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        
        # User Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        """)

        # URL Analysis Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS url_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                url TEXT,
                result TEXT
            )
        """)
        
        conn.commit()

create_database()  # Ensure database exists on startup

# Load pre-trained ML model and vectorizer
MODEL_PATH = "model.pkl"
VECTORIZER_PATH = "vectorizer.pkl"

if os.path.exists(MODEL_PATH) and os.path.exists(VECTORIZER_PATH):
    model = joblib.load(MODEL_PATH)
    vectorizer = joblib.load(VECTORIZER_PATH)
else:
    model, vectorizer = None, None
    print("❌ Model or vectorizer not found! Train the model first.")

# Function to validate URL format
def is_valid_url(url):
    url_regex = re.compile(
        r"^(https?|ftp)://[^\s/$.?#].[^\s]*$",
        re.IGNORECASE
    )
    return re.match(url_regex, url) is not None

# Home Page
@app.route("/")
def home():
    return render_template("index.html")

# Login Page
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
            user = cursor.fetchone()

        if user and check_password_hash(user[3], password):  # Check hashed password
            session["user"] = username
            flash("Login successful!", "success")
            return redirect(url_for("analyze_url"))
        else:
            flash("Invalid username or password", "danger")

    return render_template("login.html")

# Register Page
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        hashed_password = generate_password_hash(password, method="pbkdf2:sha256")

        try:
            with sqlite3.connect(DATABASE) as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)", 
                               (username, email, hashed_password))
                conn.commit()
            flash("Registration successful! Please login.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Username or Email already exists!", "danger")

    return render_template("register.html")

# Check Login Status (AJAX call)
@app.route("/check_login")
def check_login():
    return jsonify({"logged_in": "user" in session})

# Analyze URL Page (only for logged-in users)
@app.route("/analyze_url")
def analyze_url():
    if "user" in session:
        return render_template("analysis_url.html")
    flash("You need to log in first!", "warning")
    return redirect(url_for("login"))

# Analyze URL API
@app.route("/analyze", methods=["POST"])
def analyze():
    if "user" not in session:
        return jsonify({"result": "Unauthorized! Please log in."}), 401

    data = request.get_json()
    url = data.get("url")

    if not url or not is_valid_url(url):
        return jsonify({"result": "Invalid URL format!"}), 400

    if model and vectorizer:
        try:
            # Transform URL using vectorizer
            url_vectorized = vectorizer.transform([url])
            prediction = model.predict(url_vectorized)[0]  # Predict

            result = "Malicious" if prediction == 1 else "Safe"
        except Exception as e:
            return jsonify({"result": f"Model error: {str(e)}"}), 500
    else:
        return jsonify({"result": "Model or vectorizer not loaded! Please train & upload."}), 500

    # Save analysis result in database
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO url_analysis (username, url, result) VALUES (?, ?, ?)", 
                       (session["user"], url, result))
        conn.commit()

    return jsonify({"result": result})

# Logout
@app.route("/logout")
def logout():
    session.pop("user", None)
    flash("Logged out successfully.", "info")
    return redirect(url_for("home"))

if __name__ == "__main__":
    app.run(debug=True)
