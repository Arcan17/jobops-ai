"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { Board } from "@/components/Board";
import { SafetyCheck } from "@/components/SafetyCheck";
import { ScoreCard } from "@/components/ScoreCard";
import { api, ApiError, clearToken, getToken } from "@/lib/api";
import type {
  ApplicationState,
  BoardResponse,
  Job,
  Modality,
  Score,
} from "@/lib/types";

const EMPTY_JOB = {
  company: "",
  role_title: "",
  description: "",
  stack: "",
  requirements: "",
  modality: "remote" as Modality,
  country: "",
  salary: "",
};

export default function DashboardPage() {
  const router = useRouter();
  const [jobs, setJobs] = useState<Job[]>([]);
  const [board, setBoard] = useState<BoardResponse>({ columns: [] });
  const [scores, setScores] = useState<Record<string, Score>>({});
  const [form, setForm] = useState({ ...EMPTY_JOB });
  const [busyId, setBusyId] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      const [j, b] = await Promise.all([api.listJobs(), api.board()]);
      setJobs(j);
      setBoard(b);
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        clearToken();
        router.replace("/");
      } else {
        setError(err instanceof Error ? err.message : "Failed to load");
      }
    }
  }, [router]);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/");
      return;
    }
    void refresh();
  }, [router, refresh]);

  async function onCreateJob(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await api.createJob({
        company: form.company,
        role_title: form.role_title,
        description: form.description,
        stack: form.stack
          .split(",")
          .map((s) => s.trim())
          .filter(Boolean),
        requirements: form.requirements,
        modality: form.modality,
        country: form.country || null,
        salary: form.salary ? Number(form.salary) : null,
      });
      setForm({ ...EMPTY_JOB });
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create job");
    }
  }

  async function onScore(jobId: string) {
    setBusyId(jobId);
    setError(null);
    try {
      const score = await api.scoreJob(jobId);
      setScores((prev) => ({ ...prev, [jobId]: score }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to score");
    } finally {
      setBusyId(null);
    }
  }

  async function onAddToBoard(jobId: string) {
    setBusyId(jobId);
    setError(null);
    try {
      if (!scores[jobId]) await api.scoreJob(jobId);
      await api.createApplication(jobId);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to add to board");
    } finally {
      setBusyId(null);
    }
  }

  async function onMove(applicationId: string, to: ApplicationState) {
    setBusyId(applicationId);
    try {
      await api.changeState(applicationId, to);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Invalid transition");
    } finally {
      setBusyId(null);
    }
  }

  async function onGenerateMessage(applicationId: string) {
    setBusyId(applicationId);
    try {
      const msg = await api.generateMessage(applicationId);
      setMessage(msg.content);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to generate");
    } finally {
      setBusyId(null);
    }
  }

  function logout() {
    clearToken();
    router.replace("/");
  }

  return (
    <main className="mx-auto max-w-7xl p-6">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold tracking-tight">JobOps AI</h1>
          <p className="text-sm text-slate-400">
            Score jobs, generate outreach, track applications.
          </p>
        </div>
        <button
          onClick={logout}
          className="rounded-lg border border-[var(--border)] px-3 py-1.5 text-sm text-slate-300 transition hover:border-slate-500"
        >
          Sign out
        </button>
      </header>

      {error && (
        <p className="mt-4 rounded-lg bg-red-500/10 px-3 py-2 text-sm text-red-400">
          {error}
        </p>
      )}

      <div className="mt-6 grid gap-6 lg:grid-cols-[360px_1fr]">
        {/* Left: add a job + jobs list */}
        <section className="space-y-4">
          <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-5">
            <h2 className="text-sm font-medium text-slate-200">Paste a job</h2>
            <form onSubmit={onCreateJob} className="mt-3 space-y-2.5">
              <input
                required
                placeholder="Company"
                value={form.company}
                onChange={(e) => setForm({ ...form, company: e.target.value })}
                className="w-full rounded-lg border border-[var(--border)] bg-[var(--background)] px-3 py-2 text-sm outline-none focus:border-indigo-400"
              />
              <input
                required
                placeholder="Role title"
                value={form.role_title}
                onChange={(e) =>
                  setForm({ ...form, role_title: e.target.value })
                }
                className="w-full rounded-lg border border-[var(--border)] bg-[var(--background)] px-3 py-2 text-sm outline-none focus:border-indigo-400"
              />
              <input
                placeholder="Stack (comma separated)"
                value={form.stack}
                onChange={(e) => setForm({ ...form, stack: e.target.value })}
                className="w-full rounded-lg border border-[var(--border)] bg-[var(--background)] px-3 py-2 text-sm outline-none focus:border-indigo-400"
              />
              <textarea
                placeholder="Requirements"
                value={form.requirements}
                onChange={(e) =>
                  setForm({ ...form, requirements: e.target.value })
                }
                rows={3}
                className="w-full rounded-lg border border-[var(--border)] bg-[var(--background)] px-3 py-2 text-sm outline-none focus:border-indigo-400"
              />
              <div className="flex gap-2">
                <select
                  value={form.modality}
                  onChange={(e) =>
                    setForm({ ...form, modality: e.target.value as Modality })
                  }
                  className="flex-1 rounded-lg border border-[var(--border)] bg-[var(--background)] px-3 py-2 text-sm outline-none focus:border-indigo-400"
                >
                  <option value="remote">Remote</option>
                  <option value="hybrid">Hybrid</option>
                  <option value="onsite">Onsite</option>
                  <option value="unknown">Unknown</option>
                </select>
                <input
                  placeholder="Salary"
                  value={form.salary}
                  onChange={(e) => setForm({ ...form, salary: e.target.value })}
                  className="w-24 rounded-lg border border-[var(--border)] bg-[var(--background)] px-3 py-2 text-sm outline-none focus:border-indigo-400"
                />
              </div>
              <button
                type="submit"
                className="w-full rounded-lg bg-indigo-500 px-3 py-2 text-sm font-medium text-white transition hover:bg-indigo-400"
              >
                Add job
              </button>
            </form>
          </div>

          <SafetyCheck />

          <div className="space-y-3">
            {jobs.map((job) => (
              <div
                key={job.id}
                className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-4"
              >
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-sm font-medium">{job.role_title}</p>
                    <p className="text-xs text-slate-400">{job.company}</p>
                  </div>
                  <div className="flex gap-1.5">
                    <button
                      disabled={busyId === job.id}
                      onClick={() => onScore(job.id)}
                      className="rounded-md border border-[var(--border)] px-2.5 py-1 text-xs text-slate-300 transition hover:border-indigo-400 disabled:opacity-50"
                    >
                      Score
                    </button>
                    <button
                      disabled={busyId === job.id}
                      onClick={() => onAddToBoard(job.id)}
                      className="rounded-md border border-indigo-500/40 bg-indigo-500/10 px-2.5 py-1 text-xs text-indigo-300 transition hover:bg-indigo-500/20 disabled:opacity-50"
                    >
                      + Board
                    </button>
                  </div>
                </div>
                {scores[job.id] && (
                  <div className="mt-3">
                    <ScoreCard score={scores[job.id]} />
                  </div>
                )}
              </div>
            ))}
            {jobs.length === 0 && (
              <p className="px-1 text-sm text-slate-500">
                No jobs yet — paste one above.
              </p>
            )}
          </div>
        </section>

        {/* Right: board */}
        <section>
          <h2 className="mb-3 text-sm font-medium text-slate-200">Board</h2>
          <Board
            columns={board.columns}
            onMove={onMove}
            onGenerateMessage={onGenerateMessage}
            busyId={busyId}
          />
        </section>
      </div>

      {message && (
        <div
          className="fixed inset-0 z-10 flex items-center justify-center bg-black/50 p-6"
          onClick={() => setMessage(null)}
        >
          <div
            className="w-full max-w-lg rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-6"
            onClick={(e) => e.stopPropagation()}
          >
            <h3 className="text-sm font-medium text-slate-200">
              Recruiter message
            </h3>
            <p className="mt-3 whitespace-pre-wrap text-sm text-slate-300">
              {message}
            </p>
            <div className="mt-4 flex justify-end gap-2">
              <button
                onClick={() => navigator.clipboard?.writeText(message)}
                className="rounded-lg border border-[var(--border)] px-3 py-1.5 text-sm text-slate-300 transition hover:border-slate-500"
              >
                Copy
              </button>
              <button
                onClick={() => setMessage(null)}
                className="rounded-lg bg-indigo-500 px-3 py-1.5 text-sm font-medium text-white transition hover:bg-indigo-400"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}
