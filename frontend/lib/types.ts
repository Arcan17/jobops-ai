export type Recommendation = "apply" | "apply_if_quick" | "skip";

export type Modality = "remote" | "hybrid" | "onsite" | "unknown";

export type ApplicationState =
  | "nueva"
  | "evaluando"
  | "postulado"
  | "seguimiento"
  | "entrevista"
  | "rechazado"
  | "oferta";

export interface ScoreComponent {
  factor: string;
  weight: number;
  sub_score: number;
  weighted: number;
}

export interface ScoreNarrative {
  risks: string[];
  missing_requirements: string[];
  projects_to_highlight: string[];
  rationale: string;
}

export interface Score {
  id: string;
  job_opportunity_id: string;
  value: number;
  recommendation: Recommendation;
  breakdown: ScoreComponent[];
  narrative: ScoreNarrative;
}

export interface Job {
  id: string;
  link: string | null;
  company: string;
  role_title: string;
  description: string;
  stack: string[];
  requirements: string;
  modality: Modality;
  country: string | null;
  salary: number | null;
}

export interface BoardCard {
  id: string;
  company: string;
  role_title: string;
  score_value: number | null;
  state: ApplicationState;
  next_action: string | null;
}

export interface BoardColumn {
  state: ApplicationState;
  cards: BoardCard[];
}

export interface BoardResponse {
  columns: BoardColumn[];
}

export interface GeneratedMessage {
  id: string;
  application_id: string;
  type: string;
  tone: string | null;
  content: string;
}
