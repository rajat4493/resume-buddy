'use client';

import { useState } from "react";

export default function Home() {
  const [resume, setResume] = useState("");
  const [job, setJob] = useState("");
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

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
  
      if (!res.ok) {
        const err = await res.text(); // fallback to plain text
        console.error("Upload failed response:", err);
        alert("File upload failed: " + err);
        return;
      }
  
      const data = await res.json();
      setResume(data.extracted_text || "");
    } catch (error: any) {
      console.error("Upload error:", error);
      alert("File upload failed: " + error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyze = async () => {
    if (!resume || !job) return alert("Paste resume and job description.");
    setLoading(true);
    try {
      const res = await fetch("http://localhost:8000/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ resume_text: resume, job_description: job }),
      });
      const data = await res.json();
      setResult(data);
    } catch (e) {
      alert("Analysis failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-zinc-950 text-white px-6 py-12 flex flex-col items-center font-sans">
      {/* Hero Header */}
      <header className="mb-16 text-center">
        <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight">
          Resume Match & Tailor AI
        </h1>
        <p className="text-zinc-400 mt-4 max-w-xl mx-auto text-lg">
          Upload or paste your resume, enter a job description, and get a tailored resume + cover letter with a match score — powered by AI.
        </p>
      </header>

      {/* Upload + Textareas */}
      <section className="w-full max-w-3xl space-y-6 bg-zinc-900 p-8 rounded-xl shadow-lg border border-zinc-700">
        <input
          type="file"
          accept="application/pdf"
          onChange={handleFileChange}
          className="w-full bg-zinc-800 text-white border border-zinc-600 rounded p-3 file:bg-zinc-700 file:text-white"
        />

        <textarea
          value={resume}
          onChange={(e) => setResume(e.target.value)}
          rows={6}
          placeholder="Paste your resume text"
          className="w-full bg-zinc-800 text-white border border-zinc-600 rounded p-3 placeholder-zinc-400"
        />

        <textarea
          value={job}
          onChange={(e) => setJob(e.target.value)}
          rows={6}
          placeholder="Paste job description"
          className="w-full bg-zinc-800 text-white border border-zinc-600 rounded p-3 placeholder-zinc-400"
        />

        <button
          onClick={handleAnalyze}
          disabled={loading}
          className="w-full py-3 bg-white text-black font-semibold rounded hover:bg-gray-100 transition"
        >
          {loading ? "Analyzing..." : "Analyze"}
        </button>
      </section>

      {/* Results Section */}
      {result && (
        <section className="w-full max-w-4xl mt-12 space-y-8 bg-zinc-900 p-8 rounded-xl border border-zinc-700 shadow-md">
          <h2 className="text-2xl font-semibold text-green-400">
            Match Score: {result.match_score}%
          </h2>

          <div>
            <h3 className="text-lg font-bold mb-2">Tailored Resume</h3>
            <pre className="whitespace-pre-wrap text-sm text-zinc-300">
              {result.tailored_resume}
            </pre>
          </div>

          <div>
            <h3 className="text-lg font-bold mb-2">Cover Letter</h3>
            <pre className="whitespace-pre-wrap text-sm text-zinc-300">
              {result.cover_letter}
            </pre>
          </div>
        </section>
      )}
    </main>
  );
}
