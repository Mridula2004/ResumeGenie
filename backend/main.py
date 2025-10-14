from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import io
from parser import extract_text_from_pdf, extract_structure
from matcher import compute_match_score
from database import save_parsed_resume
import json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.post("/analyze/")
async def analyze_resume(file: UploadFile = File(...), job_desc: str = Form(...)):
    import traceback
    filename = file.filename
    try:
        pdf_bytes = await file.read()
        print(f"[INFO] Received file: {filename}, size: {len(pdf_bytes)} bytes")

        # Convert bytes to BytesIO for PyMuPDF
        import io
        import fitz
        text = ""
        try:
            with fitz.open(stream=io.BytesIO(pdf_bytes), filetype="pdf") as doc:
                for page in doc:
                    text += page.get_text()
        except Exception as e:
            print(f"[ERROR] PDF parsing failed: {e}")
            traceback.print_exc()
            return JSONResponse(status_code=500, content={"error": f"PDF parsing failed: {e}"})

        resume_data = extract_structure(text)
        print(f"[INFO] Extracted resume data: {resume_data}")

        # Compute match in a thread-safe way
        try:
            import asyncio
            match_json = await asyncio.to_thread(compute_match_score, resume_data, job_desc)
        except Exception as e:
            print(f"[ERROR] OpenAI matcher failed: {e}")
            traceback.print_exc()
            return JSONResponse(status_code=500, content={"error": f"Matcher failed: {e}"})

        # Ensure JSON
        import json
        if isinstance(match_json, str):
            match_data = json.loads(match_json.replace("'", '"'))
        else:
            match_data = match_json

        # Save to MongoDB
        try:
            save_parsed_resume(
                resume_data,
                filename,
                job_desc,
                match_data.get("score", 0),
                match_data.get("justification", "")
            )
        except Exception as e:
            print(f"[WARNING] MongoDB save failed: {e}")

        return {"resume_data": resume_data, "result": match_data}

    except Exception as e:
        print(f"[CRITICAL] Failed to analyze {filename}: {e}")
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": f"Failed to analyze {filename}: {e}"})
