import {
  Package,
  PackageDetail,
  AnalysisJob,
  MetricSnapshot,
  HealthFinding,
  AdoptionEvidence,
  SecurityFinding,
  CompareResponse,
} from './types';

const API_BASE = '/api/v1';

export const api = {
  async getVersion(): Promise<any> {
    const res = await fetch(`${API_BASE}/version`);
    if (!res.ok) throw new Error('Failed to fetch version');
    return res.json();
  },

  async listPackages(search?: string, ecosystem?: string): Promise<Package[]> {
    const params = new URLSearchParams();
    if (search) params.append('search', search);
    if (ecosystem) params.append('ecosystem', ecosystem);
    const res = await fetch(`${API_BASE}/packages?${params.toString()}`);
    if (!res.ok) throw new Error('Failed to fetch packages');
    return res.json();
  },

  async getPackage(id: number): Promise<PackageDetail> {
    const res = await fetch(`${API_BASE}/packages/${id}`);
    if (!res.ok) throw new Error('Failed to fetch package details');
    return res.json();
  },

  async getPackageAnalytics(id: number): Promise<MetricSnapshot[]> {
    const res = await fetch(`${API_BASE}/packages/${id}/analytics`);
    if (!res.ok) throw new Error('Failed to fetch analytics');
    return res.json();
  },

  async getPackageHealth(id: number): Promise<HealthFinding[]> {
    const res = await fetch(`${API_BASE}/packages/${id}/health`);
    if (!res.ok) throw new Error('Failed to fetch health');
    return res.json();
  },

  async getPackageAdoption(id: number): Promise<AdoptionEvidence[]> {
    const res = await fetch(`${API_BASE}/packages/${id}/adoption`);
    if (!res.ok) throw new Error('Failed to fetch adoption evidence');
    return res.json();
  },

  async getPackageSecurity(id: number): Promise<SecurityFinding[]> {
    const res = await fetch(`${API_BASE}/packages/${id}/security`);
    if (!res.ok) throw new Error('Failed to fetch security');
    return res.json();
  },

  async triggerAnalysis(packageName: string, ecosystem = 'pypi', enableAi = false): Promise<AnalysisJob> {
    const res = await fetch(`${API_BASE}/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        package_name: packageName,
        ecosystem,
        enable_ai: enableAi,
      }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to start analysis' }));
      throw new Error(err.detail || 'Failed to start analysis');
    }
    return res.json();
  },

  async getJob(jobId: string): Promise<AnalysisJob> {
    const res = await fetch(`${API_BASE}/jobs/${jobId}`);
    if (!res.ok) throw new Error('Failed to poll job status');
    return res.json();
  },

  async comparePackages(packageNames: string[]): Promise<CompareResponse> {
    const res = await fetch(`${API_BASE}/compare`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ package_names: packageNames }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Comparison failed' }));
      throw new Error(err.detail || 'Comparison failed');
    }
    return res.json();
  },

  async generateReport(packageId: number, format = 'html'): Promise<any> {
    const res = await fetch(`${API_BASE}/reports/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ package_id: packageId, format }),
    });
    if (!res.ok) throw new Error('Failed to generate report');
    return res.json();
  },

  async seedDemo(): Promise<any> {
    const res = await fetch(`${API_BASE}/demo/seed`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to seed demo data');
    return res.json();
  },
};

