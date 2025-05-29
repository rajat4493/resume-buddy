"use client";

import { useState } from "react";

export default function Home() {
  const [resume, setResume] = useState("");
  const [job, setJob] = useState("");
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  // Handle PDF file upload and extract text from backend
  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setLoading(true);
    try {
      const formData = new FormData();
      formData.append("file", file);

      const res = await fetch("http://localhost:8000/upload", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) throw new Error("Upload failed");

      const data = await res.json();
      setResume(data.extracted_text || "");
    } catch (error) {
      alert("Failed to upload file: " + error);
    } finally {
      setLoading(false);
    }
  };

  // Send resume text + job description to backend for analysis
  const handleSubmit = async () => {
    if (!resume || !job) {
      alert("Please provide both resume text and job description.");
      return;
    }
    setLoading(true);

    try {
      const res = await fetch("http://localhost:8000/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ resume_text: resume, job_description: job }),
      });

      if (!res.ok) throw new Error("Analysis failed");

      const data = await res.json();
      setResult(data);
    } catch (error) {
      alert("Failed to analyze: " + error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="p-4 max-w-xl mx-auto space-y-6">
      <h1 className="text-3xl font-bold">AI Resume Matcher</h1>

      <label className="block font-semibold">
        Upload Resume PDF (optional)
        <input
          type="file"
          accept="application/pdf"
          onChange={handleFileChange}
          className="block mt-2"
          disabled={loading}
        />
      </label>

      <label className="block font-semibold">
        Or Paste Your Resume Text
        <textarea
          placeholder="Paste your resume here..."
          className="w-full border rounded p-2 mt-1"
          rows={6}
          value={resume}
          onChange={(e) => setResume(e.target.value)}
          disabled={loading}
        />
      </label>

      <label className="block font-semibold">
        Paste Job Description
        <textarea
          placeholder="Paste the job description here..."
          className="w-full border rounded p-2 mt-1"
          rows={6}
          value={job}
          onChange={(e) => setJob(e.target.value)}
          disabled={loading}
        />
      </label>

      <button
        onClick={handleSubmit}
        disabled={loading}
        className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded disabled:opacity-50"
      >
        {loading ? "Processing..." : "Analyze"}
      </button>

      {result && (
        <section className="mt-6 space-y-4 p-4 border rounded bg-gray-50">
          <p>
            <strong>Match Score:</strong> {result.match_score}%
          </p>
          <div>
            <strong>Tailored Resume:</strong>
            <p className="whitespace-pre-wrap mt-1">{result.tailored_resume}</p>
          </div>
          <div>
            <strong>Cover Letter:</strong>
            <p className="whitespace-pre-wrap mt-1">{result.cover_letter}</p>
          </div>
        </section>
      )}
    </main>
  );
}

