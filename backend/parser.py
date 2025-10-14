import fitz

def extract_text_from_pdf(pdf_bytes):
    """
    pdf_bytes: raw bytes from uploaded file
    """
    text = ""
    # Tell fitz it's a PDF stream
    with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
        for page in doc:
            page_text = page.get_text()
            if page_text:
                text += page_text + "\n"
    return text

import re

def extract_name(text):
    # Very naive approach: assume the first line has the name
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    if lines:
        return lines[0]  # first non-empty line as candidate name
    return "Unknown"



def extract_skills(text):
    skills_db = ["Python", "Machine Learning", "Java", "AWS", "SQL", "TensorFlow"]
    found = [s for s in skills_db if s.lower() in text.lower()]
    return list(set(found))

def extract_structure(text):
    return {
        "name": extract_name(text),
        "skills": extract_skills(text),
        "experience": " ".join(text.split()[:100]),  # rough summary
    }
