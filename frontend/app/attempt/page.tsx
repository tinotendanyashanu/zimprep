"use client";

import { useState } from "react";

export default function AttemptPage() {
  const [questionText, setQuestionText] = useState("Describe the process of photosynthesis.");
  const [studentAnswer, setStudentAnswer] = useState("Photosynthesis is the process by which green plants use sunlight to synthesize nutrients from carbon dioxide and water.");
  const [maxScore, setMaxScore] = useState(5);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    setResult(null);

    try {
      const response = await fetch("http://localhost:8000/attempt", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question_text: questionText,
          student_answer: studentAnswer,
          max_score: maxScore,
        }),
      });

      if (!response.ok) {
        throw new Error(`Server error: ${response.statusText}`);
      }

      const data = await response.json();
      setResult(data);
    } catch (err: any) {
      setError(err.message || "Something went wrong.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center py-10 px-4">
      <div className="max-w-3xl w-full bg-white rounded-2xl shadow-sm border border-gray-100 p-8">
        <h1 className="text-3xl font-bold tracking-tight text-gray-900 mb-6">Test Exam Engine</h1>
        
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Question Text</label>
            <input
              type="text"
              value={questionText}
              onChange={(e) => setQuestionText(e.target.value)}
              className="w-full rounded-md border border-gray-300 px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Maximum Score</label>
            <input
              type="number"
              value={maxScore}
              onChange={(e) => setMaxScore(Number(e.target.value))}
              className="w-full md:w-1/3 rounded-md border border-gray-300 px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
              min={1}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Student Answer</label>
            <textarea
              value={studentAnswer}
              onChange={(e) => setStudentAnswer(e.target.value)}
              className="w-full rounded-md border border-gray-300 px-4 py-3 text-sm h-32 focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 px-4 rounded-md transition-colors focus:ring-2 focus:ring-blue-500 focus:outline-none focus:ring-offset-2 disabled:bg-blue-400 disabled:cursor-not-allowed"
          >
            {loading ? "Marking Answer..." : "Submit Attempt"}
          </button>
        </form>

        {error && (
          <div className="mt-8 p-4 bg-red-50 text-red-700 rounded-md border border-red-100">
            {error}
            <p className="text-xs mt-2 text-red-500">Ensure the backend is running and the OpenAI key is active.</p>
          </div>
        )}

        {result && !error && (
          <div className="mt-10 pt-8 border-t border-gray-100 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Marking Result</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
              <div className="bg-blue-50 rounded-xl p-6 border border-blue-100 flex flex-col items-center justify-center">
                <span className="text-sm font-medium text-blue-800 uppercase tracking-wider mb-2">Score Awarded</span>
                <div className="flex items-baseline space-x-1">
                  <span className="text-5xl font-extrabold text-blue-600">{result.score}</span>
                  <span className="text-xl font-medium text-blue-400">/ {result.max_score}</span>
                </div>
              </div>
              <div className="bg-gray-50 rounded-xl p-6 border border-gray-200">
                <span className="text-sm font-medium text-gray-500 uppercase tracking-wider mb-2 block">Attempt ID</span>
                <p className="text-sm font-mono text-gray-800 break-all">{result.attempt_id}</p>
              </div>
            </div>
            
            <div className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm">
              <span className="text-sm font-medium text-gray-500 uppercase tracking-wider mb-3 block">Examiner Feedback</span>
              <p className="text-gray-700 leading-relaxed">{result.feedback}</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
