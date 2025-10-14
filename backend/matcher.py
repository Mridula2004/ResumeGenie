import os, json
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def compute_match_score(resume_data, job_desc):
    prompt = f"""
Compare the following resume and job description and rate the candidate fit from 1 to 10.

Resume:
Skills: {resume_data['skills']}
Summary: {resume_data['experience']}

Job Description:
{job_desc}

Return **only JSON** like:
{{
  "score": <number between 0-100>,
  "justification": "<short reason>"
}}

Respond strictly in JSON format.
"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    output_text = response.choices[0].message.content.strip()

    # Ensure valid JSON
    try:
        match_data = json.loads(output_text.replace("'", '"'))
    except Exception:
        # Fallback to simple scoring based on number of matching skills
        skills = resume_data.get("skills", [])
        score = min(len(skills) * 20, 100)  # 20 points per skill as fallback
        justification = f"Fallback scoring: matched {len(skills)} skill(s)."
        match_data = {"score": score, "justification": justification}

    return match_data
