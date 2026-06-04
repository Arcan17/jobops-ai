import type { ApplicationState, BoardColumn } from "@/lib/types";

const STATE_LABEL: Record<ApplicationState, string> = {
  nueva: "Nueva",
  evaluando: "Evaluando",
  postulado: "Postulado",
  seguimiento: "Seguimiento",
  entrevista: "Entrevista",
  rechazado: "Rechazado",
  oferta: "Oferta",
};

// Mirror of the backend state machine (app/models/application.py).
export const ALLOWED_TRANSITIONS: Record<ApplicationState, ApplicationState[]> = {
  nueva: ["evaluando", "postulado", "rechazado"],
  evaluando: ["postulado", "rechazado"],
  postulado: ["seguimiento", "entrevista", "rechazado"],
  seguimiento: ["entrevista", "rechazado"],
  entrevista: ["oferta", "rechazado"],
  rechazado: [],
  oferta: [],
};

function scoreBadge(value: number | null): string {
  if (value === null) return "text-slate-500";
  if (value >= 7) return "text-emerald-400";
  if (value >= 5) return "text-amber-400";
  return "text-rose-400";
}

export function Board({
  columns,
  onMove,
  onGenerateMessage,
  busyId,
}: {
  columns: BoardColumn[];
  onMove: (applicationId: string, to: ApplicationState) => void;
  onGenerateMessage: (applicationId: string) => void;
  busyId: string | null;
}) {
  return (
    <div className="flex gap-4 overflow-x-auto pb-4">
      {columns.map((col) => (
        <div key={col.state} className="w-64 shrink-0">
          <div className="mb-2 flex items-center justify-between px-1">
            <h3 className="text-sm font-medium text-slate-300">
              {STATE_LABEL[col.state]}
            </h3>
            <span className="text-xs text-slate-500">{col.cards.length}</span>
          </div>

          <div className="space-y-2">
            {col.cards.length === 0 && (
              <div className="rounded-lg border border-dashed border-[var(--border)] px-3 py-6 text-center text-xs text-slate-600">
                Empty
              </div>
            )}
            {col.cards.map((card) => (
              <div
                key={card.id}
                className="rounded-lg border border-[var(--border)] bg-[var(--surface)] p-3"
              >
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <p className="text-sm font-medium leading-tight">
                      {card.role_title}
                    </p>
                    <p className="text-xs text-slate-400">{card.company}</p>
                  </div>
                  <span
                    className={`text-sm font-semibold tabular-nums ${scoreBadge(card.score_value)}`}
                  >
                    {card.score_value !== null
                      ? card.score_value.toFixed(1)
                      : "—"}
                  </span>
                </div>

                <div className="mt-3 flex flex-wrap gap-1">
                  {ALLOWED_TRANSITIONS[card.state].map((to) => (
                    <button
                      key={to}
                      disabled={busyId === card.id}
                      onClick={() => onMove(card.id, to)}
                      className="rounded-md border border-[var(--border)] px-2 py-1 text-[11px] text-slate-300 transition hover:border-indigo-400 hover:text-indigo-300 disabled:opacity-50"
                    >
                      → {STATE_LABEL[to]}
                    </button>
                  ))}
                  <button
                    disabled={busyId === card.id}
                    onClick={() => onGenerateMessage(card.id)}
                    className="rounded-md border border-indigo-500/40 bg-indigo-500/10 px-2 py-1 text-[11px] text-indigo-300 transition hover:bg-indigo-500/20 disabled:opacity-50"
                  >
                    ✉ Message
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
