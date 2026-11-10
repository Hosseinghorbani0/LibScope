import React, { useState, useEffect } from 'react';
import { GitBranch, ExternalLink, Filter, Search } from 'lucide-react';
import { api } from '../api';
import { Package, AdoptionEvidence } from '../types';

interface AdoptionPageProps {
  packages: Package[];
}

export const AdoptionPage: React.FC<AdoptionPageProps> = ({ packages }) => {
  const [selectedPkgId, setSelectedPkgId] = useState<number | ''>('');
  const [evidenceList, setEvidenceList] = useState<AdoptionEvidence[]>([]);
  const [filterType, setFilterType] = useState('all');
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (packages.length > 0 && selectedPkgId === '') {
      setSelectedPkgId(packages[0].id);
    }
  }, [packages]);

  useEffect(() => {
    async function loadAdoption() {
      if (!selectedPkgId) return;
      setIsLoading(true);
      try {
        const data = await api.getPackageAdoption(Number(selectedPkgId));
        setEvidenceList(data);
      } catch (err) {
        console.error('Failed to load adoption:', err);
      } finally {
        setIsLoading(false);
      }
    }
    loadAdoption();
  }, [selectedPkgId]);

  const filtered = evidenceList.filter((e) => {
    if (filterType === 'all') return true;
    return e.evidence_type.toLowerCase().includes(filterType.toLowerCase());
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-white tracking-tight">Adoption Discovery Engine</h1>
          <p className="text-xs text-slate-400 mt-1">
            Verified evidence of independent projects importing or depending on software packages.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <select
            value={selectedPkgId}
            onChange={(e) => setSelectedPkgId(Number(e.target.value))}
            className="rounded-lg border border-slate-800 bg-[#0d1322] px-3.5 py-2 text-xs font-semibold text-slate-200 focus:border-sky-500 focus:outline-none"
          >
            {packages.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name} ({p.ecosystem})
              </option>
            ))}
          </select>

          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="rounded-lg border border-slate-800 bg-[#0d1322] px-3.5 py-2 text-xs font-semibold text-slate-200 focus:border-sky-500 focus:outline-none"
          >
            <option value="all">All Classifications</option>
            <option value="dependency">Confirmed Dependency</option>
            <option value="source-code">Confirmed Source Usage</option>
            <option value="possible">Possible Usage</option>
            <option value="mention">Mention Only</option>
          </select>
        </div>
      </div>

      {isLoading ? (
        <div className="py-16 text-center text-slate-500 text-xs">Loading adoption records...</div>
      ) : filtered.length === 0 ? (
        <div className="rounded-xl border border-dashed border-slate-800 p-12 text-center text-slate-500 text-xs">
          No adoption records found for this package with the selected filter.
        </div>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-slate-800 bg-[#0d1322] shadow-xl">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-900 text-slate-400 font-semibold border-b border-slate-800">
              <tr>
                <th className="py-3 px-4">Independent Repository</th>
                <th className="py-3 px-4">Evidence Classification</th>
                <th className="py-3 px-4">Manifest Path</th>
                <th className="py-3 px-4 text-right">Stars</th>
                <th className="py-3 px-4 text-right">Confidence</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {filtered.map((item) => (
                <tr key={item.id} className="hover:bg-slate-900/40">
                  <td className="py-3 px-4 font-semibold">
                    <a
                      href={item.source_repo_url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-sky-400 hover:underline flex items-center gap-1.5"
                    >
                      {item.source_repo_full_name} <ExternalLink className="w-3 h-3 text-slate-500" />
                    </a>
                  </td>
                  <td className="py-3 px-4">
                    <span className="inline-block px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-950/60 text-emerald-400 border border-emerald-800">
                      {item.evidence_type}
                    </span>
                  </td>
                  <td className="py-3 px-4 font-mono text-slate-300">{item.file_path}</td>
                  <td className="py-3 px-4 text-right font-mono text-slate-300">{item.stars.toLocaleString()} ★</td>
                  <td className="py-3 px-4 text-right font-semibold text-emerald-400">
                    {Math.round(item.confidence_score * 100)}%
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};


