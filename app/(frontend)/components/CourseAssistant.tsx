"use client";

import { type FormEvent, useState } from "react";

type RetrievedCourse = {
  document_id: string;
  source_type: string;
  source_id: string;
  document_text: string;
  metadata: {
    course_code?: string;
    course_title?: string;
    department?: string;
    course_level?: number;
    credits?: number;
  };
  similarity_score: number;
};

type RagAnswer = {
  answer: string;
  citations: string[];
  results: RetrievedCourse[];
};

const apiBaseUrl = (process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000").replace(/\/$/, "");

export function CourseAssistant() {
  const [open, setOpen] = useState(false);
  const [question, setQuestion] = useState("");
  const [department, setDepartment] = useState("");
  const [courseLevel, setCourseLevel] = useState("");
  const [answer, setAnswer] = useState<RagAnswer | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmedQuestion = question.trim();
    if (!trimmedQuestion) return;

    const parsedLevel = courseLevel ? Number(courseLevel) : undefined;
    if (parsedLevel !== undefined && (!Number.isInteger(parsedLevel) || parsedLevel < 100 || parsedLevel > 599)) {
      setError("Course level must be a whole number from 100 through 599.");
      return;
    }

    setLoading(true);
    setError(null);
    setAnswer(null);
    try {
      const response = await fetch(`${apiBaseUrl}/api/v1/rag/answer`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question: trimmedQuestion,
          top_k: 5,
          department_filter: department.trim().toUpperCase() || null,
          course_level_filter: parsedLevel ?? null,
        }),
      });
      const body = await response.json().catch(() => null);
      if (!response.ok) {
        throw new Error(body?.detail || "Unable to answer your course question.");
      }
      setAnswer(body as RagAnswer);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Unable to reach the course service.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="absolute right-4 top-24 z-20 w-[min(25rem,calc(100vw-2rem))]">
      <button
        type="button"
        onClick={() => setOpen((current) => !current)}
        aria-expanded={open}
        className="ml-auto flex rounded-xl bg-uic-blue px-4 py-3 text-sm font-semibold text-white shadow-lg"
      >
        {open ? "Close course Q&A" : "Ask about courses"}
      </button>

      {open && (
        <div className="mt-2 max-h-[calc(100dvh-8rem)] overflow-y-auto rounded-2xl bg-white p-4 shadow-xl">
          <h2 className="text-lg font-bold text-uic-blue">Course Q&A</h2>
          <p className="mt-1 text-sm text-slate-600">Answers are grounded in retrieved UIC course records.</p>
          <form className="mt-4 space-y-3" onSubmit={submit}>
            <label className="block text-sm font-medium text-slate-700">
              Question
              <textarea
                value={question}
                onChange={(event) => setQuestion(event.target.value)}
                placeholder="What are the prerequisites for CS 361?"
                maxLength={1000}
                required
                rows={3}
                className="mt-1 w-full resize-y rounded-lg border border-slate-300 px-3 py-2 text-slate-900 outline-none focus:border-uic-blue focus:ring-2 focus:ring-blue-100"
              />
            </label>
            <div className="grid grid-cols-2 gap-3">
              <label className="text-sm font-medium text-slate-700">
                Department <span className="font-normal text-slate-400">optional</span>
                <input
                  value={department}
                  onChange={(event) => setDepartment(event.target.value)}
                  placeholder="CS"
                  maxLength={20}
                  className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 uppercase text-slate-900 outline-none focus:border-uic-blue focus:ring-2 focus:ring-blue-100"
                />
              </label>
              <label className="text-sm font-medium text-slate-700">
                Course level <span className="font-normal text-slate-400">optional</span>
                <input
                  value={courseLevel}
                  onChange={(event) => setCourseLevel(event.target.value)}
                  placeholder="300"
                  inputMode="numeric"
                  className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-slate-900 outline-none focus:border-uic-blue focus:ring-2 focus:ring-blue-100"
                />
              </label>
            </div>
            <button
              type="submit"
              disabled={loading || !question.trim()}
              className="w-full rounded-lg bg-uic-flame px-4 py-2.5 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-60"
            >
              {loading ? "Finding course information…" : "Get answer"}
            </button>
          </form>

          {error && <p role="alert" className="mt-3 rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</p>}

          {answer && (
            <div className="mt-4 space-y-3">
              <div className="rounded-xl bg-blue-50 p-3 text-sm leading-6 text-slate-800 whitespace-pre-wrap">
                {answer.answer}
              </div>
              {answer.citations.length > 0 && (
                <div aria-label="Course citations" className="flex flex-wrap gap-2">
                  {answer.citations.map((citation) => (
                    <span key={citation} className="rounded-full bg-uic-blue px-2.5 py-1 text-xs font-semibold text-white">{citation}</span>
                  ))}
                </div>
              )}
              <details className="rounded-xl border border-slate-200 p-3">
                <summary className="cursor-pointer text-sm font-semibold text-uic-blue">
                  Retrieved course details ({answer.results.length})
                </summary>
                <div className="mt-3 space-y-3">
                  {answer.results.map((course) => (
                    <article key={course.document_id} className="rounded-lg bg-slate-50 p-3 text-sm text-slate-700">
                      <p className="font-semibold text-slate-900">
                        {course.metadata.course_code ?? "Course"}{course.metadata.course_title ? ` — ${course.metadata.course_title}` : ""}
                      </p>
                      <p className="mt-1 text-xs text-slate-500">Match: {Math.round(course.similarity_score * 100)}%</p>
                      <p className="mt-2 whitespace-pre-wrap">{course.document_text}</p>
                    </article>
                  ))}
                </div>
              </details>
            </div>
          )}
        </div>
      )}
    </section>
  );
}
