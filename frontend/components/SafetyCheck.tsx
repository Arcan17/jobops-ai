"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import type { RiskLevel, SafetyResult } from "@/lib/types";

const RISK_STYLE: Record<RiskLevel, string> = {
  green: "bg-emerald-500/15 text-emerald-300 border-emerald-500/30",
  yellow: "bg-amber-500/15 text-amber-300 border-amber-500/30",
  orange: "bg-orange-500/15 text-orange-300 border-orange-500/30",
  red: "bg-rose-500/15 text-rose-300 border-rose-500/30",
};

const RISK_LABEL: Record<RiskLevel, string> = {
  green: "Low risk",
  yellow: "Some signals",
  orange: "Several signals",
  red: "High risk",
};

export function SafetyCheck() {
  const [message, setMessage] = useState("");
  const [result, setResult] = useState<SafetyResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onCheck(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const res = await api.safetyCheck({ message });
      setResult(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Check failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-5">
      <h2 className="text-sm font-medium text-slate-200">
        Recruiter safety check
      </h2>
      <p className="mt-1 text-xs text-slate-500">
        Paste a recruiter message to scan for risk signals (rule-based, not a verdict).
      </p>

      <form onSubmit={onCheck} className="mt-3 space-y-2.5">
        <textarea
          required
          placeholder="Paste the recruiter's message…"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          rows={4}
          className="w-full rounded-lg border border-[var(--border)] bg-[var(--background)] px-3 py-2 text-sm outline-none focus:border-indigo-400"
        />
        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-lg bg-indigo-500 px-3 py-2 text-sm font-medium text-white transition hover:bg-indigo-400 disabled:opacity-50"
        >
          {loading ? "Scanning…" : "Scan message"}
        </button>
      </form>

      {error && (
        <p className="mt-3 rounded-lg bg-red-500/10 px-3 py-2 text-sm text-red-400">
          {error}
        </p>
      )}

      {result && (
        <div className="mt-4 space-y-3">
          <div className="flex items-center justify-between">
            <span
              className={`rounded-full border px-3 py-1 text-xs font-medium ${RISK_STYLE[result.risk]}`}
            >
              {RISK_LABEL[result.risk]}
            </span>
            <span className="text-xs text-slate-500">
              {result.signals.length} signal
              {result.signals.length === 1 ? "" : "s"} · score {result.score}
            </span>
          </div>

          <ul className="space-y-1.5">
            {result.signals.map((s) => (
              <li
                key={s.code}
                className="rounded-lg border border-[var(--border)] bg-[var(--background)] px-3 py-2"
              >
                <p className="text-xs font-medium text-slate-200">{s.label}</p>
                <p className="text-[11px] text-slate-500">{s.detail}</p>
              </li>
            ))}
            {result.signals.length === 0 && (
              <li className="text-xs text-slate-500">
                No risk signals detected.
              </li>
            )}
          </ul>

          <p className="rounded-lg bg-indigo-500/10 px-3 py-2 text-xs text-indigo-200">
            {result.recommendation}
          </p>
        </div>
      )}
    </div>
  );
}
