import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer, util

# Paths
CSV_PATH = "data/career_data_processed.csv"
EMB_PATH = "data/career_embeddings.npy"

# Load data and embeddings
df = pd.read_csv(CSV_PATH)
embeddings = np.load(EMB_PATH)

# Load model
model = SentenceTransformer("all-MiniLM-L6-v2")

def recommend(skills="", interests="", top_k=5):
    """Recommend careers based on user skills and interests, showing skill gap and pay scale."""
    query = (skills + " " + interests).strip()
    if not query:
        return [{"error": "No input provided"}]

    # Encode user query
    query_embedding = model.encode(query, convert_to_tensor=True)

    # Compute cosine similarity
    cosine_scores = util.cos_sim(query_embedding, embeddings)[0]

    # Get top-k results
    top_results = np.argsort(-cosine_scores.cpu())[:top_k]

    recommendations = []
    user_skill_list = [s.lower().strip() for s in skills.split()]

    for idx in top_results:
        i = int(idx)
        job = df.iloc[i]

        # Extract details
        job_title = job.get("job_title", "Unknown Career")
        description = job.get("Short_description", "No description available")[:150] + "..."
        pay_grade = job.get("Pay_grade", "Not specified")

        # Extract and compute missing skills (skill gap)
        required_skills = str(job.get("Skills_required", "")).lower().replace(",", " ").split()
        missing_skills = [s for s in required_skills if s not in user_skill_list]

        recommendations.append({
            "career_opportunity": job_title,
            "pay_scale": pay_grade,
            "description": description,
            "skill_gap": missing_skills[:5] if missing_skills else ["No major gaps ✅"],
            "similarity": float(cosine_scores[i])
        })

    return recommendations
