import React, { useState } from 'react';
import { GitCompare, Trophy, AlertTriangle, ShieldCheck, Download, Star } from 'lucide-react';
import { api } from '../api';
import { Package, CompareResponse } from '../types';

interface ComparePageProps {
  packages: Package[];
}

export const ComparePage: React.FC<ComparePageProps> = ({ packages }) => {
  const [selectedNames, setSelectedNames] = useState<string[]>(
    packages.slice(0, 3).map((p) => p.name)
  );
  const [comparison, setComparison] = useState<CompareResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const togglePackage = (name: string) => {
    if (selectedNames.includes(name)) {
      if (selectedNames.length <= 2) return; // Keep at least 2
      setSelectedNames(selectedNames.filter((n) => n !== name));
    } else {
      setSelectedNames([...selectedNames, name]);
    }
  };

  const handleRunComparison = async () => {
    if (selectedNames.length < 2) return;
    setIsLoading(true);
    setError(null);
    try {
      const res = await api.comparePackages(selectedNames);
      setComparison(res);
    } catch (err: any) {
      setError(err.message || 'Comparison failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-black text-white tracking-tight">Competitor Intelligence</h1>
        <p className="text-xs text-slate-400 mt-1">
          Objective side-by-side comparative analysis across equivalent metrics with fairness indicators.
        </p>
      </div>

      {/* Package Selection */}
      <div className="rounded-xl border border-slate-800 bg-[#0d1322] p-5 space-y-4">
        <label className="block text-xs font-bold text-white uppercase tracking-wider">
          Select Packages to Compare (minimum 2)
        </label>
        <div className="flex flex-wrap gap-2">
          {packages.map((p) => {
            const isSelected = selectedNames.includes(p.name);
            return (
              <button
                key={p.id}
                onClick={() => togglePackage(p.name)}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition ${
                  isSelected
                    ? 'bg-sky-500/15 text-sky-400 border-sky-500/40'
                    : 'bg-slate-900 text-slate-400 border-slate-800 hover:border-slate-700'
                }`}
              >
                {p.name}
              </button>
            );
          })}
        </div>

        <button
          onClick={handleRunComparison}
          disabled={isLoading || selectedNames.length < 2}
          className="px-4 py-2 bg-sky-500 hover:bg-sky-400 text-slate-950 font-bold text-xs rounded-lg transition disabled:opacity-50 flex items-center gap-2"
        >
          <GitCompare className="w-4 h-4" /> Compare Selected Packages
        </button>
      </div>

      {error && (
        <div className="rounded-xl border border-rose-900 bg-rose-950/20 p-4 text-xs text-rose-300">
          {error}
        </div>
      )}

      {/* Comparison Results */}
      {comparison && (
        <div className="space-y-6">
          {/* Summary Box */}
          <div className="rounded-xl border border-sky-900/50 bg-sky-950/20 p-5 flex items-start gap-3">
            <Trophy className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
            <div className="text-xs leading-relaxed text-slate-200">
              <span className="font-bold text-sky-400">Analysis Summary: </span>
              {comparison.summary}
            </div>
          </div>

          {/* Side by side matrix */}
          <div className="overflow-x-auto rounded-xl border border-slate-800 bg-[#0d1322]">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-900 text-slate-400 font-semibold border-b border-slate-800">
                <tr>
                  <th className="py-3 px-4">Metric</th>
                  {comparison.packages.map((p) => (
                    <th key={p.package_name} className="py-3 px-4 font-bold text-white">
                      {p.package_name}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono">
                <tr>
                  <td className="py-3 px-4 text-slate-400 font-sans font-semibold">LibScope Quality Score</td>
                  {comparison.packages.map((p) => (
                    <td key={p.package_name} className="py-3 px-4 font-black text-sky-400 text-sm">
                      {p.overall_score !== null ? `${p.overall_score} / 100` : 'N/A'}
                    </td>
                  ))}
                </tr>
                <tr>
                  <td className="py-3 px-4 text-slate-400 font-sans font-semibold">Monthly Downloads</td>
                  {comparison.packages.map((p) => (
                    <td key={p.package_name} className="py-3 px-4 text-slate-200">
                      {p.monthly_downloads.toLocaleString()}
                    </td>
                  ))}
                </tr>
                <tr>
                  <td className="py-3 px-4 text-slate-400 font-sans font-semibold">GitHub Stars</td>
                  {comparison.packages.map((p) => (
                    <td key={p.package_name} className="py-3 px-4 text-amber-400">
                      {p.stars.toLocaleString()} ★
                    </td>
                  ))}
                </tr>
                <tr>
                  <td className="py-3 px-4 text-slate-400 font-sans font-semibold">Forks</td>
                  {comparison.packages.map((p) => (
                    <td key={p.package_name} className="py-3 px-4 text-slate-300">
                      {p.forks.toLocaleString()} ⑂
                    </td>
                  ))}
                </tr>
                <tr>
                  <td className="py-3 px-4 text-slate-400 font-sans font-semibold">Verified Adoptions</td>
                  {comparison.packages.map((p) => (
                    <td key={p.package_name} className="py-3 px-4 font-bold text-emerald-400">
                      {p.verified_adoptions} independent repos
                    </td>
                  ))}
                </tr>
                <tr>
                  <td className="py-3 px-4 text-slate-400 font-sans font-semibold">Known Vulnerabilities (OSV)</td>
                  {comparison.packages.map((p) => (
                    <td
                      key={p.package_name}
                      className={`py-3 px-4 font-bold ${
                        p.vulnerabilities_count > 0 ? 'text-rose-400' : 'text-emerald-400'
                      }`}
                    >
                      {p.vulnerabilities_count}
                    </td>
                  ))}
                </tr>
                <tr>
                  <td className="py-3 px-4 text-slate-400 font-sans font-semibold">License</td>
                  {comparison.packages.map((p) => (
                    <td key={p.package_name} className="py-3 px-4 font-sans text-slate-300">
                      {p.license || 'Unspecified'}
                    </td>
                  ))}
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};


