# backend/main.py

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import fitz  # PyMuPDF for PDF text extraction
from sentence_transformers import SentenceTransformer, util
import subprocess
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)

app = FastAPI()

# CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

OLLAMA_MODEL = "mistral"  # Use 'llama3' if needed later

# Load model once
model = SentenceTransformer('all-MiniLM-L6-v2')

# Request schema
class JobInput(BaseModel):
    resume_text: str
    job_description: str


# Helper to generate content using Ollama (LLaMA3)
def generate_with_ollama(resume: str, job_desc: str) -> tuple[str, str]:
    prompt = f"""
You are an expert resume writer and career coach.

Given the following resume and job description:
1. Tailor the resume to emphasize relevant skills and achievements.
2. Write a personalized cover letter.

RESUME:
{resume[:3000]}

JOB DESCRIPTION:
{job_desc[:2000]}

Return in this format:

TAILORED RESUME:
[...your resume here...]

COVER LETTER:
[...your letter here...]
""".strip()

    try:
        result = subprocess.run(
            ["ollama", "run", OLLAMA_MODEL],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=120
        )

        logging.info("====== Ollama STDOUT (first 500 chars) ======")
        logging.info(result.stdout[:500])
        logging.info("====== Ollama STDERR ======")
        logging.info(result.stderr.strip())

        if result.returncode != 0:
            raise RuntimeError(f"Ollama error: {result.stderr or 'Unknown error'}")

        output = result.stdout.strip()

        tailored_resume = "Could not extract tailored resume."
        cover_letter = "Could not extract cover letter."

        if "COVER LETTER:" in output:
            resume_part, cover_letter = output.split("COVER LETTER:", 1)
            if "TAILORED RESUME:" in resume_part:
                tailored_resume = resume_part.split("TAILORED RESUME:", 1)[1].strip()
            else:
                tailored_resume = resume_part.strip()
            cover_letter = cover_letter.strip()
        else:
            tailored_resume = output

        return tailored_resume, cover_letter

    except Exception as e:
        logging.error(f"Ollama call failed: {str(e)}")
        raise RuntimeError(f"AI generation failed: {e}")


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


# Main analyze route
@app.post("/analyze")
async def analyze(job: JobInput):
    try:
        resume_embedding = model.encode(job.resume_text)
        job_embedding = model.encode(job.job_description)
        similarity = util.cos_sim(resume_embedding, job_embedding).item()

        tailored_resume, cover_letter = generate_with_ollama(
            job.resume_text, job.job_description
        )

        return {
            "match_score": round(similarity * 100, 2),
            "tailored_resume": tailored_resume,
            "cover_letter": cover_letter,
        }

    except Exception as e:
        logging.error(f"/analyze failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Optional debug route
@app.post("/test")
async def test(job: JobInput):
    return {
        "resume": job.resume_text[:100],
        "job_desc": job.job_description[:100],
        "message": "Received input correctly."
    }


# Run server
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
