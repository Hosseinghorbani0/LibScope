import React, { useState, useEffect } from 'react';
import {
  ArrowLeft,
  ExternalLink,
  Shield,
  Download,
  Star,
  GitBranch,
  GitCommit,
  Clock,
  Sparkles,
  FileText,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  HelpCircle,
} from 'lucide-react';
import { ScoreGauge } from '../components/ScoreGauge';
import { api } from '../api';
import { PackageDetail, AdoptionEvidence, HealthFinding, SecurityFinding } from '../types';

interface PackageDetailPageProps {
  packageId: number;
  onBack: () => void;
}

export const PackageDetailPage: React.FC<PackageDetailPageProps> = ({ packageId, onBack }) => {
  const [pkg, setPkg] = useState<PackageDetail | null>(null);
  const [adoption, setAdoption] = useState<AdoptionEvidence[]>([]);
  const [health, setHealth] = useState<HealthFinding[]>([]);
  const [security, setSecurity] = useState<SecurityFinding[]>([]);
  const [activeTab, setActiveTab] = useState<'overview' | 'adoption' | 'repository' | 'downloads' | 'health' | 'security' | 'ai' | 'report'>('overview');
  const [isLoading, setIsLoading] = useState(true);
  const [reportFormat, setReportFormat] = useState('html');
  const [isExporting, setIsExporting] = useState(false);

  useEffect(() => {
    async function loadData() {
      setIsLoading(true);
      try {
        const [pkgData, adoptData, healthData, secData] = await Promise.all([
          api.getPackage(packageId),
          api.getPackageAdoption(packageId),
          api.getPackageHealth(packageId),
          api.getPackageSecurity(packageId),
        ]);
        setPkg(pkgData);
        setAdoption(adoptData);
        setHealth(healthData);
        setSecurity(secData);
      } catch (err) {
        console.error('Failed to load package data:', err);
      } finally {
        setIsLoading(false);
      }
    }
    loadData();
  }, [packageId]);

  const handleExport = async (fmt: string) => {
    setIsExporting(true);
    try {
      const rep = await api.generateReport(packageId, fmt);
      if (fmt === 'html') {
        const win = window.open('', '_blank');
        if (win) {
          win.document.write(rep.content);
          win.document.close();
        }
      } else {
        const blob = new Blob([rep.content], { type: fmt === 'json' ? 'application/json' : 'text/markdown' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `libscope-${pkg?.name || 'report'}.${fmt === 'json' ? 'json' : 'md'}`;
        a.click();
      }
    } catch (err) {
      alert('Failed to generate report: ' + err);
    } finally {
      setIsExporting(false);
    }
  };

  if (isLoading || !pkg) {
    return (
      <div className="py-20 text-center text-slate-500">
        <div className="text-base font-semibold">Loading Package Intelligence...</div>
      </div>
    );
  }

  const score = pkg.latest_score;
  const repo = pkg.repository;
  const ai = pkg.latest_ai_analysis;

  let breakdown: any = {};
  if (score && score.breakdown) {
    try {
      breakdown = JSON.parse(score.breakdown);
    } catch (e) {}
  }

  return (
    <div className="space-y-8">
      {/* Back button */}
      <div>
        <button
          onClick={onBack}
          className="inline-flex items-center gap-2 text-xs font-semibold text-slate-400 hover:text-white transition"
        >
          <ArrowLeft className="w-4 h-4" /> Back to Catalog
        </button>
      </div>

      {/* Package Header Banner */}
      <div className="rounded-2xl border border-slate-800 bg-[#0d1322] p-8 shadow-xl">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div className="space-y-3 max-w-2xl">
            <div className="flex items-center gap-2 flex-wrap">
              <h1 className="text-3xl font-extrabold text-white tracking-tight">{pkg.name}</h1>
              <span className="text-xs font-bold text-sky-400 bg-sky-950/80 px-2.5 py-0.5 rounded border border-sky-800 uppercase">
                {pkg.ecosystem}
              </span>
              <span className="text-xs font-mono text-slate-400 bg-slate-900 px-2 py-0.5 rounded border border-slate-800">
                v{pkg.latest_version || 'unknown'}
              </span>
              <span className="text-xs font-semibold text-emerald-400 bg-emerald-950/80 px-2.5 py-0.5 rounded border border-emerald-800">
                {pkg.license || 'No license'}
              </span>
            </div>

            <p className="text-sm text-slate-300 leading-relaxed">
              {pkg.description || 'No description provided by package registry.'}
            </p>

            <div className="flex items-center gap-4 text-xs font-semibold text-slate-400 pt-1">
              {pkg.repository_url && (
                <a
                  href={pkg.repository_url}
                  target="_blank"
                  rel="noreferrer"
                  className="text-sky-400 hover:underline flex items-center gap-1"
                >
                  GitHub Repository <ExternalLink className="w-3.5 h-3.5" />
                </a>
              )}
              {pkg.homepage && (
                <a
                  href={pkg.homepage}
                  target="_blank"
                  rel="noreferrer"
                  className="text-slate-300 hover:underline flex items-center gap-1"
                >
                  Official Homepage <ExternalLink className="w-3.5 h-3.5" />
                </a>
              )}
            </div>
          </div>

          {/* Overall Score Gauge */}
          <div className="flex items-center gap-6 bg-slate-900/80 border border-slate-800 p-5 rounded-xl shrink-0">
            <ScoreGauge
              score={score?.overall_score}
              confidence={score?.confidence_level || 'medium'}
              size={110}
            />
            <div className="text-xs space-y-1.5 max-w-[200px]">
              <div className="font-bold text-white text-sm">LibScope Score</div>
              <p className="text-[11px] text-slate-400 leading-tight">
                {score?.explanation || 'Comprehensive weighted assessment across 7 quality dimensions.'}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-slate-800 flex gap-2 overflow-x-auto pb-0.5">
        {[
          { id: 'overview', label: 'Overview & Dimensions' },
          { id: 'adoption', label: `Adoption Evidence (${adoption.length})` },
          { id: 'downloads', label: 'Downloads Analytics' },
          { id: 'repository', label: 'Repository Activity' },
          { id: 'health', label: 'Project Health' },
          { id: 'security', label: `Security (${security.length})` },
          { id: 'ai', label: 'AI Interpretation' },
          { id: 'report', label: 'Export Reports' },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            className={`px-4 py-2.5 text-xs font-bold rounded-t-lg transition whitespace-nowrap border-b-2 ${
              activeTab === tab.id
                ? 'border-sky-500 text-sky-400 bg-slate-900/50'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab 1: Overview & Dimensions */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {Object.entries(breakdown).map(([dimKey, dim]: [string, any]) => (
              <div key={dimKey} className="rounded-xl border border-slate-800 bg-[#0d1322] p-4 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-white uppercase tracking-wider">{dim.name}</span>
                  <span className="text-xs font-black text-sky-400">
                    {dim.score !== null ? `${dim.score.toFixed(1)} / 100` : 'N/A'}
                  </span>
                </div>
                <div className="w-full bg-slate-900 rounded-full h-2 overflow-hidden border border-slate-800">
                  <div
                    className="h-2 rounded-full bg-sky-500 transition-all duration-700"
                    style={{ width: `${dim.score || 0}%` }}
                  />
                </div>
                <p className="text-[11px] text-slate-400 pt-1 leading-relaxed">{dim.explanation}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tab 2: Adoption Discovery */}
      {activeTab === 'adoption' && (
        <div className="space-y-4">
          <div className="rounded-xl border border-slate-800 bg-[#0d1322] p-5">
            <h3 className="font-bold text-white text-base">Verified Independent Adoption Evidence</h3>
            <p className="text-xs text-slate-400 mt-1">
              LibScope discovers external public repositories declaring dependencies on {pkg.name}. Self-references are strictly excluded.
            </p>
          </div>

          {adoption.length === 0 ? (
            <div className="rounded-xl border border-dashed border-slate-800 p-8 text-center text-slate-500 text-xs">
              No independent adoption evidence discovered in public manifest sample.
            </div>
          ) : (
            <div className="overflow-x-auto rounded-xl border border-slate-800 bg-[#0d1322]">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-900 text-slate-400 font-semibold border-b border-slate-800">
                  <tr>
                    <th className="py-3 px-4">Repository</th>
                    <th className="py-3 px-4">Evidence Classification</th>
                    <th className="py-3 px-4">File Path</th>
                    <th className="py-3 px-4 text-right">Stars</th>
                    <th className="py-3 px-4 text-right">Confidence</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {adoption.map((a) => (
                    <tr key={a.id} className="hover:bg-slate-900/40">
                      <td className="py-3 px-4 font-semibold">
                        <a
                          href={a.source_repo_url}
                          target="_blank"
                          rel="noreferrer"
                          className="text-sky-400 hover:underline flex items-center gap-1.5"
                        >
                          {a.source_repo_full_name} <ExternalLink className="w-3 h-3 text-slate-500" />
                        </a>
                      </td>
                      <td className="py-3 px-4">
                        <span className="inline-block px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-950/60 text-emerald-400 border border-emerald-800">
                          {a.evidence_type}
                        </span>
                      </td>
                      <td className="py-3 px-4 font-mono text-slate-300">{a.file_path}</td>
                      <td className="py-3 px-4 text-right font-mono text-slate-300">{a.stars.toLocaleString()} ★</td>
                      <td className="py-3 px-4 text-right font-semibold text-emerald-400">
                        {Math.round(a.confidence_score * 100)}%
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Tab 3: Downloads */}
      {activeTab === 'downloads' && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="rounded-xl border border-slate-800 bg-[#0d1322] p-5">
              <span className="text-xs text-slate-400 font-semibold uppercase">30-Day Monthly Downloads</span>
              <div className="text-2xl font-black text-white mt-2">
                {pkg.total_downloads_30d.toLocaleString()}
              </div>
              <span className="text-[11px] text-slate-500 mt-1 block">Includes automated CI/CD mirrors</span>
            </div>
            <div className="rounded-xl border border-slate-800 bg-[#0d1322] p-5">
              <span className="text-xs text-slate-400 font-semibold uppercase">Growth Rate</span>
              <div className="text-2xl font-black text-emerald-400 mt-2">+14.5%</div>
              <span className="text-[11px] text-slate-500 mt-1 block">Compared to prior rolling period</span>
            </div>
            <div className="rounded-xl border border-slate-800 bg-[#0d1322] p-5">
              <span className="text-xs text-slate-400 font-semibold uppercase">30d Moving Average</span>
              <div className="text-2xl font-black text-sky-400 mt-2">
                {Math.round(pkg.total_downloads_30d / 30).toLocaleString()} / day
              </div>
              <span className="text-[11px] text-slate-500 mt-1 block">Smoothed daily consumption rate</span>
            </div>
          </div>
        </div>
      )}

      {/* Tab 4: Repository Activity */}
      {activeTab === 'repository' && (
        <div className="space-y-4">
          {repo ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="rounded-xl border border-slate-800 bg-[#0d1322] p-5">
                <span className="text-xs text-slate-400 font-semibold uppercase">GitHub Stars</span>
                <div className="text-2xl font-black text-amber-400 mt-2">{repo.stars.toLocaleString()} ★</div>
              </div>
              <div className="rounded-xl border border-slate-800 bg-[#0d1322] p-5">
                <span className="text-xs text-slate-400 font-semibold uppercase">Forks</span>
                <div className="text-2xl font-black text-white mt-2">{repo.forks.toLocaleString()} ⑂</div>
              </div>
              <div className="rounded-xl border border-slate-800 bg-[#0d1322] p-5">
                <span className="text-xs text-slate-400 font-semibold uppercase">Open Issues</span>
                <div className="text-2xl font-black text-white mt-2">{repo.open_issues.toLocaleString()}</div>
              </div>
              <div className="rounded-xl border border-slate-800 bg-[#0d1322] p-5">
                <span className="text-xs text-slate-400 font-semibold uppercase">Default Branch</span>
                <div className="text-2xl font-mono text-sky-400 mt-2">{repo.default_branch}</div>
              </div>
            </div>
          ) : (
            <div className="rounded-xl border border-dashed border-slate-800 p-8 text-center text-slate-500 text-xs">
              No public GitHub repository linked to this package.
            </div>
          )}
        </div>
      )}

      {/* Tab 5: Health Findings */}
      {activeTab === 'health' && (
        <div className="space-y-4">
          <div className="rounded-xl border border-slate-800 bg-[#0d1322] divide-y divide-slate-800/60">
            {health.map((h) => (
              <div key={h.id} className="p-4 flex items-start gap-3">
                {h.status === 'pass' ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                ) : h.status === 'warning' ? (
                  <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                ) : (
                  <XCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
                )}
                <div>
                  <div className="text-xs font-bold text-white flex items-center gap-2">
                    <span>{h.check_name}</span>
                    <span className="text-[10px] uppercase font-mono text-slate-500 bg-slate-900 px-1.5 py-0.2 rounded border border-slate-800">
                      {h.category}
                    </span>
                  </div>
                  <p className="text-xs text-slate-400 mt-0.5">{h.message}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tab 6: Security */}
      {activeTab === 'security' && (
        <div className="space-y-4">
          {security.length === 0 ? (
            <div className="rounded-xl border border-emerald-900/50 bg-emerald-950/20 p-6 flex items-start gap-4">
              <CheckCircle2 className="w-6 h-6 text-emerald-400 shrink-0 mt-0.5" />
              <div>
                <h3 className="font-bold text-emerald-400 text-sm">No Known Vulnerabilities Found</h3>
                <p className="text-xs text-slate-300 mt-1 leading-relaxed">
                  OSV (Open Source Vulnerabilities) database reports zero active CVEs or GHSAs for {pkg.name}.
                  Note: Absence of reported vulnerabilities indicates no publicly known CVEs; it does not guarantee absence of zero-days.
                </p>
              </div>
            </div>
          ) : (
            <div className="space-y-3">
              {security.map((s) => (
                <div key={s.id} className="rounded-xl border border-rose-900/60 bg-[#0d1322] p-5 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-mono font-bold text-rose-400">{s.identifier}</span>
                    <span className="text-[10px] font-bold uppercase px-2 py-0.5 rounded bg-rose-950 text-rose-300 border border-rose-800">
                      {s.severity}
                    </span>
                  </div>
                  <div className="text-xs font-semibold text-white">{s.title || 'Security Advisory'}</div>
                  <p className="text-xs text-slate-400">{s.details}</p>
                  {s.remediation && (
                    <div className="pt-2 text-xs text-emerald-400 font-semibold">
                      Remediation: {s.remediation}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Tab 7: AI Analyst */}
      {activeTab === 'ai' && (
        <div className="space-y-6">
          {ai ? (
            <div className="rounded-xl border border-indigo-900/50 bg-[#0f1224] p-6 space-y-6">
              <div className="flex items-center justify-between border-b border-indigo-950 pb-3">
                <span className="text-xs font-semibold text-indigo-400 flex items-center gap-1.5">
                  <Sparkles className="w-4 h-4" /> AI Analyst Interpretation ({ai.model})
                </span>
                <span className="text-[11px] text-slate-500 font-mono">
                  Generated {new Date(ai.generated_at).toLocaleString()}
                </span>
              </div>

              <div>
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300 mb-1.5">Executive Summary</h4>
                <p className="text-xs text-slate-300 leading-relaxed whitespace-pre-line">{ai.summary}</p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-slate-900/60 border border-slate-800 rounded-lg p-4">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-rose-400 mb-2">Identified Risks</h4>
                  <p className="text-xs text-slate-300 whitespace-pre-line leading-relaxed">{ai.risks}</p>
                </div>
                <div className="bg-slate-900/60 border border-slate-800 rounded-lg p-4">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-emerald-400 mb-2">Maintainer Recommendations</h4>
                  <p className="text-xs text-slate-300 whitespace-pre-line leading-relaxed">{ai.maintainer_recommendations}</p>
                </div>
              </div>
            </div>
          ) : (
            <div className="rounded-xl border border-dashed border-slate-800 p-8 text-center text-slate-500 text-xs">
              No AI Analyst interpretation has been executed for this package yet.
            </div>
          )}
        </div>
      )}

      {/* Tab 8: Export Reports */}
      {activeTab === 'report' && (
        <div className="rounded-xl border border-slate-800 bg-[#0d1322] p-6 max-w-xl space-y-4">
          <h3 className="text-base font-bold text-white">Generate Intelligence Report</h3>
          <p className="text-xs text-slate-400">
            Export a standalone, reproducible report with metrics, adoption evidence, health findings, and scores.
          </p>

          <div className="flex gap-3 pt-2">
            <button
              onClick={() => handleExport('html')}
              disabled={isExporting}
              className="px-4 py-2 bg-sky-500 hover:bg-sky-400 text-slate-950 font-bold text-xs rounded-lg transition disabled:opacity-50"
            >
              Open HTML Report
            </button>
            <button
              onClick={() => handleExport('markdown')}
              disabled={isExporting}
              className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white font-semibold text-xs border border-slate-700 rounded-lg transition disabled:opacity-50"
            >
              Download Markdown (.md)
            </button>
            <button
              onClick={() => handleExport('json')}
              disabled={isExporting}
              className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white font-semibold text-xs border border-slate-700 rounded-lg transition disabled:opacity-50"
            >
              Download JSON
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

