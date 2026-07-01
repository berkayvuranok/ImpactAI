export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}

export interface User {
  id: string;
  email: string;
  username: string;
  role: string;
}

export interface Repository {
  id: string;
  name: string;
  url: string;
  default_branch: string;
  provider: string;
  last_synced_at: string | null;
  created_at: string;
}

export interface RepositoryList {
  items: Repository[];
  total: number;
}

export interface AffectedFile {
  file_path: string;
  break_probability: number;
  node_importance: number;
  rank: number;
  explanation?: string | null;
}

export interface SimilarCommit {
  commit_sha: string;
  similarity_score: number;
  message: string;
  is_regression: boolean;
  linked_issue_ids: string[];
}

export interface ReviewerSuggestion {
  user_id: string;
  username: string;
  score: number;
  expertise_areas: string[];
  ownership_files: string[];
  rationale?: string | null;
}

export interface Explanation {
  root_cause: string;
  risk_explanation: string;
  affected_files_explanation: string;
  reviewer_explanation?: string | null;
}

export interface Prediction {
  id: string;
  repository_id: string;
  status: string;
  risk_score: number | null;
  regression_probability: number | null;
  confidence_score: number | null;
  affected_files: AffectedFile[];
  similar_commits: SimilarCommit[];
  suggested_reviewers: ReviewerSuggestion[];
  explanation: Explanation | null;
  error_message: string | null;
  created_at: string;
  completed_at: string | null;
}

export interface PredictAccepted {
  prediction_id: string;
  status: string;
  message: string;
}

export interface GraphNode {
  node_id: string;
  node_type: string;
  name: string;
  file_path: string | null;
  properties: Record<string, unknown>;
}

export interface GraphEdge {
  source_id: string;
  target_id: string;
  edge_type: string;
  weight: number;
}

export interface GraphSnapshot {
  snapshot_id: string;
  commit_sha: string;
  node_count: number;
  edge_count: number;
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface RiskSummary {
  repository_id: string;
  average_risk_score: number;
  high_risk_predictions: number;
  total_predictions: number;
  trend: { prediction_id: string; risk_score: number; created_at: string }[];
}

export interface PredictionHistory {
  items: Prediction[];
  total: number;
  limit: number;
  offset: number;
}

export interface XAIReport {
  prediction_id: string;
  shap_base_value: number;
  shap_output_value: number;
  feature_attributions: {
    feature: string;
    label: string;
    value: number;
    shap_value: number;
  }[];
  node_attentions: {
    node_id: string;
    name: string;
    file_path: string | null;
    attention_score: number;
    rank: number;
  }[];
  edge_attentions: {
    source_id: string;
    target_id: string;
    attention_score: number;
  }[];
  method: string;
  metadata: Record<string, unknown>;
}

export interface HealthResponse {
  status: string;
  version: string;
  environment: string;
}
