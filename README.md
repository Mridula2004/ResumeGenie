Smart Resume Screener (Resume Genie) is an intelligent resume analysis system that automates the candidate shortlisting process.
It parses resumes, extracts structured information (skills, experience, education), and evaluates how well each candidate matches a given job description using Large Language Models (LLMs).

The system outputs a match score (1–10), a list of key relevant skills, and a textual justification for each candidate’s fit.
It also stores all analyzed data in a MongoDB database, and includes an optional Streamlit dashboard for visualization.

Objectives
1. Parse and extract data (skills, education, experience) from PDF or text resumes.
2. Compare candidate profiles with job descriptions semantically.
3. Generate a match score and justification.
4. Store all parsed resumes and scores in MongoDB for persistence.
5. Optionally visualize candidate rankings and confidence levels in a dashboard.

System Scope

| Component               | Description                                     |
| ----------------------- | ----------------------------------------------- |
| **Input**               | PDF/Text resumes and job description text       |
| **Processing**          | Parsing → Skill Extraction → LLM Scoring        |
| **Output**              | Match score, skills, justification, and storage |
| **Database**            | MongoDB Atlas                                   |
| **Frontend (Optional)** | Streamlit web dashboard                         |
| **Backend API**         | FastAPI-based REST interface                    |
