import type { Recommendation, Score } from "@/lib/types";

const RECOMMEND_LABEL: Record<Recommendation, string> = {
  apply: "Apply",
  apply_if_quick: "Apply if quick",
  skip: "Skip",
};

const RECOMMEND_STYLE: Record<Recommendation, string> = {
  apply: "bg-emerald-500/15 text-emerald-300 border-emerald-500/30",
  apply_if_quick: "bg-amber-500/15 text-amber-300 border-amber-500/30",
  skip: "bg-rose-500/15 text-rose-300 border-rose-500/30",
};

const FACTOR_LABEL: Record<string, string> = {
  stack_match: "Stack match",
  seniority_match: "Seniority",
  modality_location: "Modality / location",
  projects_match: "Projects",
  salary_interest: "Salary / interest",
  risk_penalty: "Risk (retention)",
};

function scoreColor(value: number): string {
  if (value >= 7) return "text-emerald-400";
  if (value >= 5) return "text-amber-400";
  return "text-rose-400";
}

export function ScoreCard({ score }: { score: Score }) {
  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--background)] p-4">
      <div className="flex items-center justify-between">
        <div className="flex items-baseline gap-2">
          <span className={`text-3xl font-bold ${scoreColor(score.value)}`}>
            {score.value.toFixed(1)}
          </span>
          <span className="text-sm text-slate-500">/ 10</span>
        </div>
        <span
          className={`rounded-full border px-3 py-1 text-xs font-medium ${RECOMMEND_STYLE[score.recommendation]}`}
        >
          {RECOMMEND_LABEL[score.recommendation]}
        </span>
      </div>

      <div className="mt-4 space-y-2">
        {score.breakdown.map((c) => (
          <div key={c.factor}>
            <div className="flex justify-between text-xs text-slate-400">
              <span>
                {FACTOR_LABEL[c.factor] ?? c.factor}{" "}
                <span className="text-slate-600">· w{c.weight}</span>
              </span>
              <span className="tabular-nums text-slate-300">
                {(c.sub_score * 100).toFixed(0)}%
              </span>
            </div>
            <div className="mt-1 h-1.5 w-full overflow-hidden rounded-full bg-slate-700/50">
              <div
                className="h-full rounded-full bg-indigo-400"
                style={{ width: `${Math.round(c.sub_score * 100)}%` }}
              />
            </div>
          </div>
        ))}
      </div>

      {score.narrative.projects_to_highlight.length > 0 && (
        <div className="mt-4 text-xs text-slate-400">
          <span className="font-medium text-slate-300">Highlight:</span>{" "}
          {score.narrative.projects_to_highlight.join(", ")}
        </div>
      )}
      {score.narrative.risks.length > 0 && (
        <div className="mt-1 text-xs text-amber-300/80">
          <span className="font-medium">Risks:</span>{" "}
          {score.narrative.risks.join(", ")}
        </div>
      )}
    </div>
  );
}
