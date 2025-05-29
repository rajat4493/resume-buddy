# backend/main.py

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import fitz  # PyMuPDF to extract text from PDF
from sentence_transformers import SentenceTransformer, util

app = FastAPI()

# Allow frontend to access backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

model = SentenceTransformer('all-MiniLM-L6-v2')

class JobInput(BaseModel):
    resume_text: str
    job_description: str

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    contents = await file.read()
    doc = fitz.open(stream=contents, filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return {"extracted_text": text}


@app.post("/analyze")
async def analyze(job: JobInput):
    resume_embedding = model.encode(job.resume_text, convert_to_tensor=True)
    job_embedding = model.encode(job.job_description, convert_to_tensor=True)
    similarity = util.cos_sim(resume_embedding, job_embedding).item()

    # Placeholder for generated content
    tailored_resume = f"Tailored version of: {job.resume_text[:200]}..."
    cover_letter = f"Dear Hiring Manager,\n\nBased on your job description: {job.job_description[:200]}..."

    return {
        "match_score": round(similarity * 100, 2),
        "tailored_resume": tailored_resume,
        "cover_letter": cover_letter
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

