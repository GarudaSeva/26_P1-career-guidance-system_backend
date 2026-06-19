from flask import Flask, request, jsonify
from flask_cors import CORS
from recommender import recommend
from basic_recommender import predict_basic
import json
import os
import hashlib
from pathlib import Path

app = Flask(__name__)
cors_origins = os.environ.get("CORS_ORIGINS", "*")
if cors_origins != "*":
    cors_origins = [origin.strip() for origin in cors_origins.split(",") if origin.strip()]

CORS(app, resources={r"/*": {"origins": cors_origins}}, supports_credentials=True)

BASE_DIR = Path(__file__).resolve().parent
USERS_FILE = BASE_DIR / "users.json"

# ---------------- UTILITY FUNCTIONS ----------------
def load_users():
    """Load all users from JSON file."""
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w") as f:
            json.dump([], f)
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def save_users(users):
    """Save users back to JSON file."""
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)

def hash_password(password):
    """Simple password hashing using SHA256."""
    return hashlib.sha256(password.encode()).hexdigest()

# ---------------- HEALTH CHECK ----------------
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})

# ---------------- SIGNUP ROUTE ----------------
@app.route("/signup", methods=["POST"])
def signup():
    """
    Example Input:
    {
      "fullname": "John Doe",
      "email": "john@example.com",
      "password": "12345"
    }
    """
    try:
        data = request.get_json(force=True)
        fullname = data.get("fullname")
        email = data.get("email")
        password = data.get("password")

        if not fullname or not email or not password:
            return jsonify({"error": "All fields (fullname, email, password) are required"}), 400

        users = load_users()

        # Check if user already exists
        if any(u["email"].lower() == email.lower() for u in users):
            return jsonify({"error": "User with this email already exists"}), 400

        hashed_pwd = hash_password(password)
        new_user = {
            "fullname": fullname,
            "email": email.lower(),
            "password": hashed_pwd
        }
        users.append(new_user)
        save_users(users)

        return jsonify({"message": "Signup successful"}), 201
    except Exception as e:
        print("❌ Error in /signup:", e)
        return jsonify({"error": str(e)}), 500

# ---------------- LOGIN ROUTE ----------------
@app.route("/login", methods=["POST"])
def login():
    """
    Example Input:
    {
      "email": "john@example.com",
      "password": "12345"
    }
    """
    try:
        data = request.get_json(force=True)
        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            return jsonify({"error": "Email and password are required"}), 400

        users = load_users()
        hashed_pwd = hash_password(password)

        user = next((u for u in users if u["email"].lower() == email.lower() and u["password"] == hashed_pwd), None)

        if not user:
            return jsonify({"error": "Invalid email or password"}), 401

        return jsonify({
            "message": "Login successful",
            "user": {"fullname": user["fullname"], "email": user["email"]}
        }), 200
    except Exception as e:
        print("❌ Error in /login:", e)
        return jsonify({"error": str(e)}), 500


# ---------------- BASIC (school) route ----------------
@app.route("/basic", methods=["POST"])
def basic_endpoint():
    """
    Receives data dynamically from the frontend (school students)
    """
    try:
        data = request.get_json(force=True)
        print("📩 Received /basic data:", data)

        result = predict_basic(data)
        print("📤 Sending response:", result)
        return jsonify(result)
    except Exception as e:
        print("❌ Error in /basic:", e)
        return jsonify({"error": str(e)}), 500


# ---------------- ADVANCED (college/professional) route ----------------
@app.route("/recommend", methods=["POST"])
def recommend_endpoint():
    """
    Receives data dynamically from the frontend (college/professional)
    """
    try:
        data = request.get_json(force=True)
        print("📩 Received /recommend data:", data)

        skills = data.get("skills", "")
        interests = data.get("interests", "")
        top_k = int(data.get("top_k", 5))

        if not skills and not interests:
            return jsonify({"error": "Please provide at least 'skills' or 'interests'"}), 400

        recommendations = recommend(skills, interests, top_k)
        print("📤 Sending recommendations:", recommendations)
        return jsonify({"recommendations": recommendations})
    except Exception as e:
        print("❌ Error in /recommend:", e)
        return jsonify({"error": str(e)}), 500


# ---------------- SAVE PROFILE + STORE RESULTS ----------------
@app.route("/save-profile", methods=["POST"])
def save_profile():
    try:
        data = request.get_json(force=True)
        email = data.get("email")

        if not email:
            return jsonify({"error": "Email is required"}), 400

        users = load_users()
        user = next((u for u in users if u["email"].lower() == email.lower()), None)

        if not user:
            return jsonify({"error": "User not found"}), 404

        age = int(data.get("age", 0))

        # ================== BASIC STUDENT (<=17) ===================
        if age <= 17:
            gender = 1 if data.get("gender", "").lower() == "male" else 0
            part_time_job = 1 if data.get("partTimeJob") == "1" else 0
            extracurricular = 1 if data.get("extracurricularActivities") == "1" else 0

            clean_data = {
                "gender": gender,
                "part_time_job": part_time_job,
                "absence_days": int(data.get("absenceDays", 0)),
                "extracurricular_activities": extracurricular,
                "weekly_self_study_hours": int(data.get("weeklyStudyHours", 0)),
                "math_score": int(data.get("mathScore", 0)),
                "history_score": int(data.get("historyScore", 0)),
                "physics_score": int(data.get("physicsScore", 0)),
                "chemistry_score": int(data.get("chemistryScore", 0)),
                "biology_score": int(data.get("biologyScore", 0)),
                "english_score": int(data.get("englishScore", 0)),
                "geography_score": int(data.get("geographyScore", 0)),
            }

            # IMPORTANT: call with clean_data not raw data
            result = predict_basic(clean_data)

        # ================== ADVANCED MODEL (>18) ===================
        else:
            skills = data.get("skills", "")
            interests = data.get("interests", "")
            top_k = 5
            result = recommend(skills, interests, top_k)

        # Save profile & recommendations
        user["profile"] = data
        user["recommendations"] = result
        save_users(users)

        return jsonify({
            "message": "Profile and recommendations saved successfully",
            "result": result
        }), 200

    except Exception as e:
        print("❌ Error in /save-profile:", e)
        return jsonify({"error": str(e)}), 500


# ---------------- DASHBOARD ROUTE ----------------
@app.route("/dashboard", methods=["GET"])
def dashboard():
    email = request.args.get("email")
    users = load_users()

    user = next((u for u in users if u["email"].lower() == email.lower()), None)
    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify({
        "fullname": user["fullname"],
        "profile": user.get("profile", {}),
        "recommendations": user.get("recommendations", [])
    })


@app.route("/get-user", methods=["POST"])
def get_user():
    try:
        data = request.get_json(force=True)
        email = data.get("email")

        users = load_users()
        user = next((u for u in users if u["email"].lower() == email.lower()), None)

        if not user:
            return jsonify({"error": "User not found"}), 404

        return jsonify({"profile": user.get("profile"), "recommendations": user.get("recommendations")}), 200

    except Exception as e:
        print("❌ Error in /get-user:", e)
        return jsonify({"error": str(e)}), 500



if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)
