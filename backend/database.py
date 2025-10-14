from pymongo import MongoClient
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Make sure to replace <password> with your actual password or use environment variable
MONGO_URI = os.getenv(
    "MONGO_URI",
    "mongodb+srv://mridulaprasad2022_db_user:Mridula@cluster0.nz4hkib.mongodb.net/resume_db?retryWrites=true&w=majority"
)
client = MongoClient(MONGO_URI)

db = client["Resume"]
parsed_resumes = db["RES"]

def save_parsed_resume(resume_data, filename, job_desc, score, justification):
    doc = {
        "candidate_name": resume_data.get("name", filename),
        "filename": filename,
        "skills": resume_data.get("skills", []),
        "experience_summary": resume_data.get("experience", ""),
        "job_description": job_desc,
        "match_score": score,
        "justification": justification,
        "timestamp": datetime.utcnow()
    }
    result = parsed_resumes.insert_one(doc)
    print(f"[INFO] Saved resume '{filename}' with _id: {result.inserted_id}")
