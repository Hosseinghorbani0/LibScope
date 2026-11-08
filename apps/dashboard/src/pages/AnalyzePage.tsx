import React, { useState, useEffect } from 'react';
import { Search, Sparkles, Loader2, CheckCircle2, AlertCircle, ArrowRight } from 'lucide-react';
import { api } from '../api';
import { AnalysisJob } from '../types';

interface AnalyzePageProps {
  onAnalysisCompleted: (packageId: number) => void;
}

export const AnalyzePage: React.FC<AnalyzePageProps> = ({ onAnalysisCompleted }) => {
  const [packageName, setPackageName] = useState('');
  const [ecosystem, setEcosystem] = useState('pypi');
  const [enableAi, setEnableAi] = useState(false);
  const [currentJob, setCurrentJob] = useState<AnalysisJob | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Poll active job
  useEffect(() => {
    let interval: any = null;
    if (currentJob && (currentJob.status === 'queued' || currentJob.status === 'running')) {
      interval = setInterval(async () => {
        try {
          const updated = await api.getJob(currentJob.id);
          setCurrentJob(updated);
          if (updated.status === 'completed' && updated.package_id) {
            clearInterval(interval);
          } else if (updated.status === 'failed') {
            setError(updated.error_message || 'Analysis encountered an unhandled error.');
            clearInterval(interval);
          }
        } catch (err: any) {
          console.error('Job polling error:', err);
        }
      }, 1000);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [currentJob]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!packageName.trim()) return;

    setError(null);
    setIsSubmitting(true);
    try {
      const job = await api.triggerAnalysis(packageName.trim(), ecosystem, enableAi);
      setCurrentJob(job);
    } catch (err: any) {
      setError(err.message || 'Failed to submit analysis job.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-8">
      <div>
        <h1 className="text-2xl font-black text-white tracking-tight sm:text-3xl">Analyze Package</h1>
        <p className="text-sm text-slate-400 mt-1">
          Perform a multi-dimensional intelligence analysis across registry metrics, repository activity, independent adoption, and security.
        </p>
      </div>

      {/* Form Card */}
      <div className="rounded-xl border border-slate-800 bg-[#0d1322] p-6 shadow-xl">
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
              Package Name or Repository
            </label>
            <div className="relative">
              <Search className="absolute left-3.5 top-3 h-4 w-4 text-slate-500" />
              <input
                type="text"
                required
                value={packageName}
                onChange={(e) => setPackageName(e.target.value)}
                placeholder={ecosystem === 'pypi' ? 'e.g. pydantic, httpx, flask, askai-python' : 'e.g. fastapi/fastapi, psf/requests'}
                className="w-full rounded-lg border border-slate-800 bg-slate-900/90 pl-10 pr-4 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:border-sky-500 focus:outline-none focus:ring-1 focus:ring-sky-500"
              />
            </div>
            <p className="text-[11px] text-slate-500 mt-1.5">
              Enter canonical name from registry. LibScope automatically resolves linked GitHub repositories and public manifest usages.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                Ecosystem Provider
              </label>
              <select
                value={ecosystem}
                onChange={(e) => setEcosystem(e.target.value)}
                className="w-full rounded-lg border border-slate-800 bg-slate-900/90 px-3.5 py-2.5 text-sm text-slate-100 focus:border-sky-500 focus:outline-none focus:ring-1 focus:ring-sky-500"
              >
                <option value="pypi">PyPI (Python Package Index)</option>
                <option value="github">GitHub Public Repository</option>
              </select>
            </div>

            <div className="flex flex-col justify-end">
              <div className="rounded-lg border border-slate-800 bg-slate-900/50 p-3 flex items-center justify-between">
                <div>
                  <div className="text-xs font-semibold text-slate-200 flex items-center gap-1.5">
                    <Sparkles className="w-3.5 h-3.5 text-indigo-400" /> AI Analyst Synthesis
                  </div>
                  <div className="text-[10px] text-slate-500">Structured interpretation of evidence</div>
                </div>
                <input
                  type="checkbox"
                  checked={enableAi}
                  onChange={(e) => setEnableAi(e.target.checked)}
                  className="w-4 h-4 rounded border-slate-700 bg-slate-800 text-sky-500 focus:ring-sky-500"
                />
              </div>
            </div>
          </div>

          <div className="pt-2">
            <button
              type="submit"
              disabled={isSubmitting || (currentJob !== null && currentJob.status === 'running')}
              className="w-full py-3 bg-sky-500 hover:bg-sky-400 text-slate-950 font-bold text-sm rounded-lg shadow-lg shadow-sky-500/20 transition flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" /> Starting Job...
                </>
              ) : (
                'Run Intelligence Analysis'
              )}
            </button>
          </div>
        </form>
      </div>

      {/* Error state */}
      {error && (
        <div className="rounded-xl border border-rose-900/50 bg-rose-950/20 p-4 flex items-start gap-3 text-rose-300">
          <AlertCircle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
          <div className="text-xs">
            <div className="font-bold">Analysis Error</div>
            <div className="mt-0.5 text-slate-400">{error}</div>
          </div>
        </div>
      )}

      {/* Progress & Live Job State */}
      {currentJob && (
        <div className="rounded-xl border border-slate-800 bg-[#0d1322] p-6 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <span className="text-xs font-mono uppercase text-slate-400">Job #{currentJob.id.slice(0, 8)}</span>
              <h3 className="font-bold text-white text-base mt-0.5">
                Analyzing {currentJob.package_name} ({currentJob.ecosystem})
              </h3>
            </div>
            <div>
              {currentJob.status === 'completed' ? (
                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-emerald-950 text-emerald-400 border border-emerald-800">
                  <CheckCircle2 className="w-3.5 h-3.5" /> Completed
                </span>
              ) : currentJob.status === 'failed' ? (
                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-rose-950 text-rose-400 border border-rose-800">
                  <AlertCircle className="w-3.5 h-3.5" /> Failed
                </span>
              ) : (
                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-sky-950 text-sky-400 border border-sky-800">
                  <Loader2 className="w-3.5 h-3.5 animate-spin" /> In Progress ({currentJob.progress}%)
                </span>
              )}
            </div>
          </div>

          {/* Progress Bar */}
          <div className="w-full bg-slate-900 rounded-full h-2.5 overflow-hidden border border-slate-800">
            <div
              className={`h-2.5 rounded-full transition-all duration-500 ${
                currentJob.status === 'completed'
                  ? 'bg-emerald-500'
                  : currentJob.status === 'failed'
                  ? 'bg-rose-500'
                  : 'bg-sky-500'
              }`}
              style={{ width: `${currentJob.progress}%` }}
            />
          </div>

          <p className="text-xs font-mono text-slate-400">{currentJob.step_message}</p>

          {currentJob.status === 'completed' && currentJob.package_id && (
            <div className="pt-2">
              <button
                onClick={() => onAnalysisCompleted(currentJob.package_id!)}
                className="w-full py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs rounded-lg transition flex items-center justify-center gap-2"
              >
                View Full Intelligence Report <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

