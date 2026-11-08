export interface Package {
  id: number;
  name: string;
  ecosystem: string;
  description?: string;
  homepage?: string;
  repository_url?: string;
  license?: string;
  latest_version?: string;
  created_at: string;
  updated_at: string;
}

export interface Score {
  id: number;
  package_id: number;
  version: string;
  calculated_at: string;
  overall_score?: number;
  confidence_level: 'high' | 'medium' | 'low';
  popularity_score?: number;
  growth_score?: number;
  adoption_score?: number;
  maintenance_score?: number;
  documentation_score?: number;
  quality_score?: number;
  security_score?: number;
  breakdown?: string;
  explanation?: string;
}

export interface Repository {
  id: number;
  package_id: number;
  owner: string;
  repo_name: string;
  full_name: string;
  url: string;
  stars: number;
  forks: number;
  open_issues: number;
  closed_issues: number;
  watchers: number;
  default_branch: string;
  is_archived: boolean;
  is_fork: boolean;
  license?: string;
  last_commit_at?: string;
  last_release_at?: string;
}

export interface MetricSnapshot {
  id: number;
  package_id: number;
  recorded_at: string;
  period: string;
  downloads_count: number;
  growth_rate?: number;
  stars_count?: number;
  forks_count?: number;
  issues_count?: number;
  raw_data?: string;
}

export interface AdoptionEvidence {
  id: number;
  package_id: number;
  source_repo_url: string;
  source_repo_full_name: string;
  file_path: string;
  evidence_type: string;
  raw_match?: string;
  discovered_at: string;
  stars: number;
  confidence_score: number;
}

export interface HealthFinding {
  id: number;
  package_id: number;
  category: string;
  check_name: string;
  status: 'pass' | 'warning' | 'fail' | 'missing';
  message: string;
  details?: string;
  detected_at: string;
}

export interface SecurityFinding {
  id: number;
  package_id: number;
  identifier: string;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  affected_range?: string;
  fixed_in?: string;
  source: string;
  reference_url?: string;
  title?: string;
  details?: string;
  remediation?: string;
  detected_at: string;
}

export interface AIAnalysis {
  id: number;
  package_id: number;
  provider: string;
  model: string;
  summary?: string;
  risks?: string;
  opportunities?: string;
  maintainer_recommendations?: string;
  competitive_position?: string;
  generated_at: string;
}

export interface PackageDetail extends Package {
  repository?: Repository;
  latest_score?: Score;
  latest_ai_analysis?: AIAnalysis;
  recent_releases_count: number;
  total_downloads_30d: number;
  adoption_count: number;
  vulnerabilities_count: number;
}

export interface AnalysisJob {
  id: string;
  package_id?: number;
  package_name: string;
  ecosystem: string;
  status: 'queued' | 'running' | 'completed' | 'failed' | 'cancelled';
  progress: number;
  step_message: string;
  error_message?: string;
  created_at: string;
  started_at?: string;
  completed_at?: string;
}

export interface CompareMetric {
  package_name: string;
  ecosystem: string;
  overall_score?: number;
  confidence: string;
  monthly_downloads: number;
  stars: number;
  forks: number;
  open_issues: number;
  latest_version?: string;
  last_release_age_days?: number;
  verified_adoptions: number;
  vulnerabilities_count: number;
  license?: string;
  comparability_notes: string[];
}

export interface CompareResponse {
  compared_at: string;
  packages: CompareMetric[];
  summary: string;
}

