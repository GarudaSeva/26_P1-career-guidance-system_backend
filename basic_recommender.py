import pandas as pd
import joblib
import json
import os

# Paths
MODEL_PATH = "bramha/career_recommendation_xgb_model.pkl"
ENCODER_PATH = "bramha/label_encoders.pkl"
CAREER_JSON_PATH = "bramha/career_recommendations.json"  # <-- path to your JSON file

# Load model and encoders
xgb_model = joblib.load(MODEL_PATH)
label_encoders = joblib.load(ENCODER_PATH)

# Load career data JSON
if os.path.exists(CAREER_JSON_PATH):
    with open(CAREER_JSON_PATH, "r") as f:
        career_data = json.load(f)
else:
    career_data = []


def predict_basic(user_data: dict):
    """Predict career path and return detailed info using XGBoost."""
    # Convert user input into DataFrame
    user_df = pd.DataFrame([user_data])

    # Predict encoded class
    predicted_class = xgb_model.predict(user_df)[0]

    # Decode class name
    career_label = label_encoders["career_aspiration"].inverse_transform([predicted_class])[0]

    # Find detailed info from JSON
    details = next(
        (item for item in career_data if item["career_opportunity"].lower() == career_label.lower()), 
        None
    )

    # If not found, return just the label
    if not details:
        return {"recommended_career": career_label, "details": "No detailed info available"}

    # Return structured data
    return {
        "recommended_career": career_label,
            "description": details["description"],
            "pay_scale": details["pay_scale"],
            "skills_required": details.get("skill_required", [])
    }
