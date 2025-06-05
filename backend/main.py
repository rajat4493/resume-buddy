# backend/main.py

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import fitz  # PyMuPDF for PDF text extraction
from sentence_transformers import SentenceTransformer, util

app = FastAPI()

# CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load model once
model = SentenceTransformer('all-MiniLM-L6-v2')

# Request schema
class JobInput(BaseModel):
    resume_text: str
    job_description: str

# Upload PDF and extract text
@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")

    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Empty file uploaded.")

    try:
        doc = fitz.open(stream=contents, filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text().strip() + "\n\n"
        if not text.strip():
            raise HTTPException(status_code=400, detail="No text found in PDF.")
        return {"extracted_text": text.strip()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to extract text: {e}")

# Analyze and generate match score + placeholder tailored content
@app.post("/analyze")
async def analyze(job: JobInput):
    try:
        resume_embedding = model.encode(job.resume_text, convert_to_tensor=True)
        job_embedding = model.encode(job.job_description, convert_to_tensor=True)
        similarity = util.cos_sim(resume_embedding, job_embedding).item()

        tailored_resume = f"[Tailored Resume Sample]\n{job.resume_text[:300]}..."
        cover_letter = f"Dear Hiring Manager,\n\nBased on the job description: {job.job_description[:300]}...\n\n[Generated cover letter content here]"

        return {
            "match_score": round(similarity * 100, 2),
            "tailored_resume": tailored_resume,
            "cover_letter": cover_letter,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze: {e}")

# Run server
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
