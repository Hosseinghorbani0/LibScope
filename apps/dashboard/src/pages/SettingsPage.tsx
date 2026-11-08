import React, { useEffect, useState } from 'react';
import { Settings, Shield, Server, Cpu, Database, RefreshCw, CheckCircle2 } from 'lucide-react';
import { api } from '../api';

interface SettingsPageProps {
  onSeedDemo: () => void;
  isSeeding: boolean;
}

export const SettingsPage: React.FC<SettingsPageProps> = ({ onSeedDemo, isSeeding }) => {
  const [versionInfo, setVersionInfo] = useState<any>(null);

  useEffect(() => {
    async function loadVersion() {
      try {
        const v = await api.getVersion();
        setVersionInfo(v);
      } catch (err) {
        console.error('Failed to load version:', err);
      }
    }
    loadVersion();
  }, []);

  return (
    <div className="max-w-3xl mx-auto space-y-8">
      <div>
        <h1 className="text-2xl font-black text-white tracking-tight">System Settings & Providers</h1>
        <p className="text-xs text-slate-400 mt-1">
          Platform configurations, ecosystem adapters, and credential availability.
        </p>
      </div>

      <div className="space-y-4">
        {/* Providers card */}
        <div className="rounded-xl border border-slate-800 bg-[#0d1322] p-5 space-y-3">
          <div className="flex items-center gap-2 text-sm font-bold text-white">
            <Server className="w-4 h-4 text-sky-400" /> Ecosystem Data Providers
          </div>
          <div className="divide-y divide-slate-800/60 text-xs">
            <div className="py-2.5 flex items-center justify-between">
              <div>
                <span className="font-semibold text-slate-200">PyPI Registry & pypistats</span>
                <p className="text-[11px] text-slate-500">Official Python Package Index JSON API and download counts</p>
              </div>
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-950 text-emerald-400 border border-emerald-800">
                ACTIVE
              </span>
            </div>
            <div className="py-2.5 flex items-center justify-between">
              <div>
                <span className="font-semibold text-slate-200">GitHub API v3</span>
                <p className="text-[11px] text-slate-500">
                  {versionInfo?.github_token_configured
                    ? 'Authenticated (5,000 req/hr rate limit)'
                    : 'Unauthenticated public rate limit (60 req/hr)'}
                </p>
              </div>
              <span
                className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                  versionInfo?.github_token_configured
                    ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                    : 'bg-amber-950 text-amber-400 border border-amber-800'
                }`}
              >
                {versionInfo?.github_token_configured ? 'AUTHENTICATED' : 'ANONYMOUS'}
              </span>
            </div>
            <div className="py-2.5 flex items-center justify-between">
              <div>
                <span className="font-semibold text-slate-200">OSV Vulnerability DB</span>
                <p className="text-[11px] text-slate-500">Open Source Vulnerabilities API (CVE & GHSA query)</p>
              </div>
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-950 text-emerald-400 border border-emerald-800">
                ACTIVE
              </span>
            </div>
          </div>
        </div>

        {/* AI Configuration */}
        <div className="rounded-xl border border-slate-800 bg-[#0d1322] p-5 space-y-3">
          <div className="flex items-center gap-2 text-sm font-bold text-white">
            <Cpu className="w-4 h-4 text-indigo-400" /> AI Analyst Configuration
          </div>
          <p className="text-xs text-slate-400">
            LibScope uses an optional AI layer to interpret verified evidence. Deterministic scoring runs independently of AI.
          </p>
          <div className="bg-slate-900/60 border border-slate-800 rounded-lg p-3 text-xs space-y-1.5 font-mono">
            <div className="flex justify-between">
              <span className="text-slate-400 font-sans">Configured Provider:</span>
              <span className="text-slate-200">{versionInfo?.ai_provider || 'openrouter'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400 font-sans">API Key Status:</span>
              <span className={versionInfo?.ai_configured ? 'text-emerald-400 font-sans' : 'text-amber-400 font-sans'}>
                {versionInfo?.ai_configured ? 'Configured & Active' : 'Not Set (Deterministic Fallback Mode)'}
              </span>
            </div>
          </div>
        </div>

        {/* Security & SSRF */}
        <div className="rounded-xl border border-slate-800 bg-[#0d1322] p-5 space-y-3">
          <div className="flex items-center gap-2 text-sm font-bold text-white">
            <Shield className="w-4 h-4 text-emerald-400" /> Security Controls
          </div>
          <div className="text-xs text-slate-300 space-y-2">
            <div className="flex items-center gap-2 text-emerald-400 font-semibold">
              <CheckCircle2 className="w-4 h-4" /> SSRF Network Boundary Guard Enforced
            </div>
            <p className="text-[11px] text-slate-400 leading-relaxed">
              All external HTTP queries validate resolved IP addresses. Requests to private networks (10.0.0.0/8, 192.168.0.0/16, 172.16.0.0/12), loopback (127.0.0.1, ::1), and cloud metadata endpoints (169.254.169.254, metadata.google.internal) are blocked automatically.
            </p>
          </div>
        </div>

        {/* Database & Demo Seed */}
        <div className="rounded-xl border border-slate-800 bg-[#0d1322] p-5 flex items-center justify-between">
          <div>
            <div className="flex items-center gap-2 text-sm font-bold text-white">
              <Database className="w-4 h-4 text-amber-400" /> Database & Demo Data
            </div>
            <p className="text-[11px] text-slate-400 mt-0.5">
              Seed sample benchmark packages for offline exploration.
            </p>
          </div>
          <button
            onClick={onSeedDemo}
            disabled={isSeeding}
            className="px-3.5 py-2 bg-slate-800 hover:bg-slate-700 text-sky-400 font-semibold text-xs border border-slate-700 rounded-lg transition disabled:opacity-50 flex items-center gap-1.5"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isSeeding ? 'animate-spin' : ''}`} />
            {isSeeding ? 'Seeding...' : 'Reload Demo Data'}
          </button>
        </div>
      </div>
    </div>
  );
};

