import React, { useState } from 'react';
import { Package, Search, ArrowUpRight, ShieldCheck, Download, Star, GitBranch, Sparkles } from 'lucide-react';
import { ScoreGauge } from '../components/ScoreGauge';
import { Package as PackageType } from '../types';

interface OverviewPageProps {
  packages: PackageType[];
  onSelectPackage: (pkgId: number) => void;
  onNavigateToAnalyze: () => void;
  onSeedDemo: () => void;
  isLoading: boolean;
}

export const OverviewPage: React.FC<OverviewPageProps> = ({
  packages,
  onSelectPackage,
  onNavigateToAnalyze,
  onSeedDemo,
  isLoading,
}) => {
  const [searchTerm, setSearchTerm] = useState('');

  const filtered = packages.filter(
    (p) =>
      p.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (p.description && p.description.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  return (
    <div className="space-y-8">
      {/* Header Banner */}
      <div className="relative overflow-hidden rounded-2xl border border-slate-800 bg-gradient-to-r from-slate-900 via-sky-950/30 to-slate-900 p-8 shadow-2xl">
        <div className="relative z-10 max-w-2xl space-y-3">
          <div className="inline-flex items-center gap-2 rounded-full border border-sky-500/30 bg-sky-500/10 px-3 py-1 text-xs font-semibold text-sky-400">
            <Sparkles className="w-3.5 h-3.5" /> Open-Source Software Intelligence
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight text-white sm:text-4xl">
            Beyond Downloads. Evidence-Based Package Health.
          </h1>
          <p className="text-sm text-slate-300 leading-relaxed">
            Distinguish real-world independent production adoption from automated CI/CD mirrors.
            LibScope discovers verified dependency declarations, tracks commit discipline, and reports security risks without guessing.
          </p>
          <div className="pt-2 flex flex-wrap gap-3">
            <button
              onClick={onNavigateToAnalyze}
              className="px-4 py-2 bg-sky-500 hover:bg-sky-400 text-slate-950 text-sm font-bold rounded-lg shadow-lg shadow-sky-500/20 transition flex items-center gap-2"
            >
              Analyze New Package <ArrowUpRight className="w-4 h-4" />
            </button>
            {packages.length === 0 && (
              <button
                onClick={onSeedDemo}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-sm font-semibold rounded-lg transition"
              >
                Load Demo Benchmark Set
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Global Stat Metrics */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-xl border border-slate-800 bg-[#0d1322] p-5">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-semibold uppercase tracking-wider">Analyzed Packages</span>
            <Package className="w-4 h-4 text-sky-400" />
          </div>
          <div className="mt-3 text-3xl font-extrabold text-white">{packages.length}</div>
          <div className="mt-1 text-xs text-slate-500">Registered in local SQLite/PostgreSQL</div>
        </div>

        <div className="rounded-xl border border-slate-800 bg-[#0d1322] p-5">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-semibold uppercase tracking-wider">Adoption Engine</span>
            <GitBranch className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="mt-3 text-3xl font-extrabold text-emerald-400">5 Tiers</div>
          <div className="mt-1 text-xs text-slate-500">Manifest declarations to source usage</div>
        </div>

        <div className="rounded-xl border border-slate-800 bg-[#0d1322] p-5">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-semibold uppercase tracking-wider">Vulnerability DB</span>
            <ShieldCheck className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="mt-3 text-3xl font-extrabold text-white">Live OSV</div>
          <div className="mt-1 text-xs text-slate-500">Open Source Vulnerabilities API integration</div>
        </div>

        <div className="rounded-xl border border-slate-800 bg-[#0d1322] p-5">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-semibold uppercase tracking-wider">Scoring Model</span>
            <Sparkles className="w-4 h-4 text-amber-400" />
          </div>
          <div className="mt-3 text-3xl font-extrabold text-amber-400">v1.0.0</div>
          <div className="mt-1 text-xs text-slate-500">Explainable, 7-dimension weighted model</div>
        </div>
      </div>

      {/* Package List / Catalog */}
      <div className="space-y-4">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="text-xl font-bold text-white tracking-tight">Ecosystem Intelligence Library</h2>
            <p className="text-xs text-slate-400">Select any package to inspect deep analytics and adoption evidence</p>
          </div>
          <div className="relative w-full sm:w-72">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-500" />
            <input
              type="text"
              placeholder="Filter analyzed packages..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full rounded-lg border border-slate-800 bg-slate-900/90 pl-9 pr-4 py-2 text-xs text-slate-200 placeholder-slate-500 focus:border-sky-500 focus:outline-none focus:ring-1 focus:ring-sky-500"
            />
          </div>
        </div>

        {isLoading ? (
          <div className="p-12 text-center text-slate-500">Loading intelligence data...</div>
        ) : filtered.length === 0 ? (
          <div className="rounded-xl border border-dashed border-slate-800 p-12 text-center">
            <Package className="mx-auto h-12 w-12 text-slate-600 mb-3" />
            <h3 className="text-base font-semibold text-slate-300">No packages found</h3>
            <p className="mt-1 text-xs text-slate-500 max-w-sm mx-auto">
              {packages.length === 0
                ? "No packages have been analyzed yet. Start your first analysis or load the demo benchmark dataset."
                : "No packages match your search filter."}
            </p>
            <div className="mt-4 flex justify-center gap-3">
              <button
                onClick={onNavigateToAnalyze}
                className="px-3.5 py-1.5 bg-sky-500 text-slate-950 font-bold text-xs rounded-lg hover:bg-sky-400 transition"
              >
                Analyze a Package
              </button>
              {packages.length === 0 && (
                <button
                  onClick={onSeedDemo}
                  className="px-3.5 py-1.5 bg-slate-800 text-slate-300 border border-slate-700 font-semibold text-xs rounded-lg hover:bg-slate-700 transition"
                >
                  Load Demo Data
                </button>
              )}
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
            {filtered.map((pkg) => (
              <div
                key={pkg.id}
                onClick={() => onSelectPackage(pkg.id)}
                className="group cursor-pointer rounded-xl border border-slate-800/90 bg-[#0d1322] p-5 transition-all hover:border-sky-500/50 hover:bg-slate-900/60 hover:shadow-xl hover:shadow-sky-950/20 flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="font-bold text-white group-hover:text-sky-400 transition text-base">
                          {pkg.name}
                        </h3>
                        <span className="text-[10px] font-semibold text-sky-400 bg-sky-950/80 px-2 py-0.5 rounded border border-sky-800 uppercase">
                          {pkg.ecosystem}
                        </span>
                      </div>
                      <span className="text-[11px] text-slate-400 font-mono mt-0.5 block">
                        v{pkg.latest_version || 'unknown'} • {pkg.license || 'No license'}
                      </span>
                    </div>
                  </div>
                  <p className="mt-3 text-xs text-slate-400 line-clamp-2 leading-relaxed">
                    {pkg.description || 'No description provided by registry.'}
                  </p>
                </div>

                <div className="mt-5 pt-3 border-t border-slate-800/60 flex items-center justify-between text-xs text-slate-400">
                  <span className="text-[11px]">Updated {new Date(pkg.updated_at).toLocaleDateString()}</span>
                  <span className="text-sky-400 font-semibold flex items-center gap-1 group-hover:translate-x-0.5 transition">
                    Inspect Report <ArrowUpRight className="w-3.5 h-3.5" />
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

