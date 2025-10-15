import streamlit as st
import httpx
import asyncio
import nest_asyncio
import pandas as pd
import base64
from pymongo import MongoClient
import os
from datetime import datetime
from dotenv import load_dotenv

# ---------- MongoDB Setup ----------
load_dotenv()
MONGO_URI = os.getenv(
    "MONGO_URI",
    "mongodb+srv://mridulaprasad2022_db_user:Mridula@cluster0.nz4hkib.mongodb.net/resume_db?retryWrites=true&w=majority"
)
client = MongoClient(MONGO_URI)
db = client["Resume"]
parsed_resumes = db["RES"]

# ---------- Patch asyncio for Streamlit ----------
nest_asyncio.apply()

# ---------- Page Config ----------
st.set_page_config(
    page_title="Smart Resume Screener",
    layout="wide",
    page_icon="📝"
)

# ---------- Header ----------
img_data = base64.b64encode(open("genie.png", "rb").read()).decode()
st.markdown(
    f"""
    <style>
    @keyframes floatGenie {{
        0% {{ transform: translateY(0px); }}
        50% {{ transform: translateY(-10px); }}
        100% {{ transform: translateY(0px); }}
    }}
    @keyframes fadeUp {{
        from {{ opacity: 0; transform: translateY(25px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}
    .title-container {{
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 15px;
        margin-top: 10px;
        animation: fadeUp 1.2s ease-out;
    }}
    .genie-img {{
        width: 70px;
        height: auto;
        animation: floatGenie 3s ease-in-out infinite;
    }}
    .title-text {{
        background: linear-gradient(90deg, #6A1B9A, #8E24AA);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-family: 'Poppins', sans-serif;
        font-size: 44px;
        font-weight: 700;
        letter-spacing: -0.4px;
    }}
    .subtitle {{
        text-align: center;
        font-family: 'Inter', sans-serif;
        color: #7B7B7B;
        font-size: 18px;
        margin-top: -6px;
        animation: fadeUp 1.5s ease-out;
    }}
    </style>
    <div class="title-container">
        <div class="title-text">Resume Genie</div>
        <img src="data:image/png;base64,{img_data}" class="genie-img">
    </div>
    <div class="subtitle">Your magic for smarter hiring decisions ✨</div>
    """,
    unsafe_allow_html=True
)

st.markdown("---")

# ---------- Tabs ----------
tab1, tab2, tab3 = st.tabs(["Analyze New Resumes", "Stored Resumes", "Shortlisted Candidates"])

# ---------- Tab 1: Analyze New Resumes ----------
with tab1:
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Job Description")
        job_desc = st.text_area("Paste the job description here", height=250)

    with col2:
        st.subheader("Upload Resume(s)")
        uploaded_files = st.file_uploader(
            "Choose PDF files", type=["pdf"], accept_multiple_files=True
        )

    # ---------- Async Resume Analysis ----------
    async def analyze_resume(file, job_desc):
        async with httpx.AsyncClient(timeout=120.0) as client:
            files = {"file": (file.name, file.getvalue(), "application/pdf")}
            data = {"job_desc": job_desc}
            try:
                resp = await client.post("https://resumegenie-qofk.onrender.com/analyze/", files=files, data=data)
                resp.raise_for_status()
                return resp.json(), file.name
            except Exception as e:
                return {"error": str(e)}, file.name

    async def analyze_all(uploaded_files, job_desc):
        tasks = [analyze_resume(f, job_desc) for f in uploaded_files]
        return await asyncio.gather(*tasks)

    if st.button("Analyze Resumes"):
        if not uploaded_files or job_desc.strip() == "":
            st.warning("Please upload at least one resume and paste a job description!")
        else:
            status_placeholder = st.empty()
            status_placeholder.info("Analyzing resumes... this may take a few seconds.")
            results = asyncio.get_event_loop().run_until_complete(analyze_all(uploaded_files, job_desc))
            status_placeholder.empty()

            processed_results = []
            for r, name in results:
                if "error" in r:
                    processed_results.append({"name": name, "error": r["error"]})
                else:
                    processed_results.append({
                        "name": r["resume_data"].get("name", name),
                        "score": r["result"].get("score", 0),
                        "justification": r["result"].get("justification", ""),
                        "skills": r["resume_data"].get("skills", [])
                    })

            processed_results.sort(key=lambda x: x.get("score", -1), reverse=True)

            for r in processed_results:
                if "error" in r:
                    st.error(f"Error analyzing {r['name']}: {r['error']}")
                else:
                    score = r["score"]
                    bar_color = "#F44336" if score <= 30 else "#FFC107" if score <= 70 else "#4CAF50"

                    st.markdown(
                        f"""
                        <div style='background:#f5f5f5;padding:20px;margin-bottom:15px;border-radius:15px;
                                    box-shadow:2px 2px 12px #aaa;'>
                            <h3 style='color:#6A1B9A;'>📄 {r['name']}</h3>
                            <p><strong>Skills:</strong> {', '.join(r['skills']) if r['skills'] else 'N/A'}</p>
                            <p><strong>Match Score:</strong> {score} / 100</p>
                            <div style='background:#eee;border-radius:10px;height:20px;overflow:hidden;'>
                                <div style='width:{score}%;
                                            background:{bar_color};
                                            height:100%;
                                            border-radius:10px;
                                            text-align:center;
                                            color:white;
                                            font-weight:bold;
                                            font-size:12px;
                                            line-height:20px;'>{score}%</div>
                            </div>
                            <details style='margin-top:10px;'>
                                <summary>Justification</summary>
                                <p>{r['justification']}</p>
                            </details>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

            # ---------- Download CSV ----------
            if processed_results:
                df = pd.DataFrame([
                    {
                        "Resume Name": r["name"],
                        "Skills": ", ".join(r.get("skills", [])),
                        "Match Score": r.get("score", ""),
                        "Justification": r.get("justification", "")
                    }
                    for r in processed_results if "error" not in r
                ])
                csv = df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Analysis as CSV",
                    data=csv,
                    file_name="resume_analysis.csv",
                    mime="text/csv"
                )

# ---------- Tab 2: Stored Resumes ----------
with tab2:
    st.subheader("Stored Resumes in Database")
    try:
        resumes_cursor = parsed_resumes.find().sort("timestamp", -1)
        resumes_list = list(resumes_cursor)

        if not resumes_list:
            st.info("No resumes found in the database yet.")
        else:
            df = pd.DataFrame([
                {
                    "Candidate Name": r.get("candidate_name", "N/A"),
                    "Filename": r.get("filename", "N/A"),
                    "Skills": ", ".join(r.get("skills", [])),
                    "Match Score": r.get("match_score", "N/A"),
                    "Job Description": r.get("job_description", "")[:50] + ("..." if len(r.get("job_description", "")) > 50 else ""),
                    "Justification": r.get("justification", "")[:50] + ("..." if len(r.get("justification", "")) > 50 else ""),
                    "Timestamp": r.get("timestamp", "")
                }
                for r in resumes_list
            ])
            st.dataframe(df, use_container_width=True)

            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Download Stored Resumes as CSV",
                data=csv,
                file_name="stored_resumes.csv",
                mime="text/csv"
            )
    except Exception as e:
        st.error(f"Error fetching resumes: {str(e)}")

# ---------- Tab 3: Shortlisted Candidates ----------
with tab3:
    st.subheader("Shortlisted Candidates")
    try:
        job_descs = parsed_resumes.distinct("job_description")
        if not job_descs:
            st.info("No resumes found in the database yet.")
        else:
            selected_job = st.selectbox("Select Job Description", job_descs)

            candidates_cursor = parsed_resumes.find({"job_description": selected_job}).sort("match_score", -1)
            candidates = list(candidates_cursor)

            if not candidates:
                st.info("No candidates found for this role.")
            else:
                best = candidates[0]
                st.markdown(
                    f"""
                    <div style='background:#E3F2FD;padding:20px;margin-bottom:15px;border-radius:15px;
                                box-shadow:2px 2px 12px #aaa;'>
                        <h2 style='color:#1E88E5;'>🏆 Best Candidate: {best.get('candidate_name', 'N/A')}</h2>
                        <p><strong>Filename:</strong> {best.get('filename', '')}</p>
                        <p><strong>Skills:</strong> {', '.join(best.get('skills', []))}</p>
                        <p><strong>Match Score:</strong> {best.get('match_score', '')} / 100</p>
                        <details>
                            <summary>Justification</summary>
                            <p>{best.get('justification', '')}</p>
                        </details>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                df_all = pd.DataFrame([
                    {
                        "Candidate Name": c.get("candidate_name", "N/A"),
                        "Filename": c.get("filename", ""),
                        "Skills": ", ".join(c.get("skills", [])),
                        "Match Score": c.get("match_score", ""),
                        "Justification": c.get("justification", "")
                    }
                    for c in candidates
                ])
                st.subheader("All Candidates for this Role")
                st.dataframe(df_all, use_container_width=True)

                csv_all = df_all.to_csv(index=False)
                st.download_button(
                    label="📥 Download Candidates CSV",
                    data=csv_all,
                    file_name="candidates_for_job.csv",
                    mime="text/csv"
                )

    except Exception as e:
        st.error(f"Error fetching shortlisted candidates: {str(e)}")

# ---------- Footer ----------
st.markdown("---")
st.markdown(
    "<p style='text-align:center;color:#999;'>Smart Resume Screener by Mridula Prasad</p>",
    unsafe_allow_html=True,
)
