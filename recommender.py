import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer, util
from collections import Counter
import spacy

# Load SpaCy NLP model
nlp = spacy.load("en_core_web_sm")

# Paths
CSV_PATH = "data/career_data_processed.csv"
EMB_PATH = "data/career_embeddings.npy"

# Load data and embeddings
df = pd.read_csv(CSV_PATH)
embeddings = np.load(EMB_PATH)

# Load model
model = SentenceTransformer("all-MiniLM-L6-v2")

# ==========================================
# AUTO BUILD MULTI-WORD SKILL DICTIONARY
# ==========================================

def generate_phrases(text):
    words = text.lower().split()
    phrases = []

    # bigrams and trigrams
    for i in range(len(words) - 1):
        phrases.append(words[i] + " " + words[i+1])
    for i in range(len(words) - 2):
        phrases.append(words[i] + " " + words[i+1] + " " + words[i+2])

    return phrases

phrase_counts = Counter()

for s in df["Skills_required"]:
    if isinstance(s, str):
        phrase_counts.update(generate_phrases(s))

# Only keep common phrases appearing multiple times
MASTER_PHRASES = {p for p, c in phrase_counts.items() if c >= 3}

print(f"Loaded Multi-word phrases: {len(MASTER_PHRASES)}")

# ==========================================
# PARSE USER INPUT USING SpaCy + phrase_dict
# ==========================================
def parse_user_skills(text):
    text = text.lower()
    detected = []

    # SpaCy noun chunk detection
    doc = nlp(text)
    for chunk in doc.noun_chunks:
        phrase = chunk.text.strip().lower()
        if phrase in MASTER_PHRASES:
            detected.append(phrase)
            text = text.replace(phrase, "")

    # Check dictionary multi-words manually
    for phrase in MASTER_PHRASES:
        if phrase in text:
            detected.append(phrase)
            text = text.replace(phrase, "")

    # Remaining words after removing big phrases
    for w in text.replace(",", " ").split():
        if len(w) > 2 and w not in detected:
            detected.append(w)

    return list(dict.fromkeys(detected))


# ==========================================
# MAIN RECOMMEND FUNCTION
# ==========================================
def recommend(skills="", interests="", top_k=5):
    """Recommend careers + skill gap calculation"""
    query = (skills + " " + interests).strip()
    if not query:
        return [{"error": "No input provided"}]

    # Encode query
    query_embedding = model.encode(query, convert_to_tensor=True)

    # Cosine similarity
    cosine_scores = util.cos_sim(query_embedding, embeddings)[0]
    top_results = np.argsort(-cosine_scores.cpu())[:top_k]

    # Parse user skill text using new extractor
    user_skill_list = parse_user_skills(skills)

    recommendations = []

    for idx in top_results:
        i = int(idx)
        job = df.iloc[i]

        job_title = job.get("job_title", "Unknown Career")
        description = job.get("Short_description", "No description available")[:150] + "..."
        pay = job.get("Pay_grade", "Not specified")

        # dataset skill list (space separated)
        raw_text = job.get("Skills_required", "").lower()
        required = parse_user_skills(raw_text) 
        # Missing skill detection
        missing = [s for s in required if s not in user_skill_list]

        recommendations.append({
            "career_opportunity": job_title,
            "pay_scale": pay,
            "description": description,
            "matched_skills": [s for s in required if s in user_skill_list],
            "skill_gap": missing[:5] if missing else ["No major gaps 🟢"],
            "similarity": float(cosine_scores[i])
        })

    return recommendations
