import React from 'react';
import {
  Compass,
  Search,
  BarChart3,
  GitBranch,
  ShieldAlert,
  GitCompare,
  FileText,
  Settings,
  Sparkles,
} from 'lucide-react';

interface NavbarProps {
  currentTab: string;
  onSelectTab: (tab: string) => void;
  onSeedDemo: () => void;
  isSeeding: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({
  currentTab,
  onSelectTab,
  onSeedDemo,
  isSeeding,
}) => {
  const navItems = [
    { id: 'overview', label: 'Overview', icon: Compass },
    { id: 'analyze', label: 'Analyze Package', icon: Search },
    { id: 'adoption', label: 'Adoption Discovery', icon: GitBranch },
    { id: 'compare', label: 'Competitor Comparison', icon: GitCompare },
    { id: 'settings', label: 'Settings & Providers', icon: Settings },
  ];

  return (
    <aside className="w-64 bg-[#0d1322] border-r border-slate-800/80 flex flex-col justify-between shrink-0 h-screen sticky top-0">
      <div>
        {/* Brand header */}
        <div className="p-6 border-b border-slate-800/60 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-gradient-to-tr from-brand-600 to-sky-400 flex items-center justify-center shadow-lg shadow-sky-500/20">
              <Compass className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="font-extrabold text-lg text-white tracking-tight flex items-center gap-1.5">
                LibScope
                <span className="text-[10px] bg-sky-950 text-sky-400 font-semibold px-1.5 py-0.2 rounded border border-sky-800">
                  OSS
                </span>
              </div>
              <p className="text-[11px] text-slate-400 font-medium">Beyond Downloads</p>
            </div>
          </div>
        </div>

        {/* Navigation list */}
        <nav className="p-4 space-y-1.5">
          {navItems.map((item) => {
            const Icon = item.icon;
            const active = currentTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onSelectTab(item.id)}
                className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-sm font-semibold transition-all ${
                  active
                    ? 'bg-sky-500/15 text-sky-400 border border-sky-500/30 shadow-sm'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40 border border-transparent'
                }`}
              >
                <Icon className={`w-4 h-4 ${active ? 'text-sky-400' : 'text-slate-500'}`} />
                {item.label}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Footer / Demo mode */}
      <div className="p-4 border-t border-slate-800/60 space-y-3">
        <div className="bg-slate-900/80 border border-slate-800 rounded-lg p-3">
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-amber-400" /> Demo Dataset
            </span>
            <span className="text-[10px] text-slate-500 font-mono">Offline-ready</span>
          </div>
          <p className="text-[11px] text-slate-400 mb-2 leading-relaxed">
            Load verified sample benchmark packages (FastAPI, Requests, AskAI).
          </p>
          <button
            onClick={onSeedDemo}
            disabled={isSeeding}
            className="w-full text-xs font-semibold py-1.5 px-3 bg-slate-800 hover:bg-slate-700 text-sky-400 border border-slate-700 rounded transition disabled:opacity-50"
          >
            {isSeeding ? 'Seeding...' : 'Load Sample Data'}
          </button>
        </div>

        <div className="text-[11px] text-slate-500 text-center">
          LibScope v0.1.0 • Apache-2.0
        </div>
      </div>
    </aside>
  );
};


