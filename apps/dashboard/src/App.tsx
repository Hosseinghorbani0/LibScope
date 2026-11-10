import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { OverviewPage } from './pages/OverviewPage';
import { AnalyzePage } from './pages/AnalyzePage';
import { PackageDetailPage } from './pages/PackageDetailPage';
import { AdoptionPage } from './pages/AdoptionPage';
import { ComparePage } from './pages/ComparePage';
import { SettingsPage } from './pages/SettingsPage';
import { api } from './api';
import { Package } from './types';

export function App() {
  const [currentTab, setCurrentTab] = useState('overview');
  const [selectedPackageId, setSelectedPackageId] = useState<number | null>(null);
  const [packages, setPackages] = useState<Package[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isSeeding, setIsSeeding] = useState(false);

  const loadPackages = async () => {
    setIsLoading(true);
    try {
      const data = await api.listPackages();
      setPackages(data);
    } catch (err) {
      console.error('Failed to load packages:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadPackages();
  }, []);

  const handleSeedDemo = async () => {
    setIsSeeding(true);
    try {
      await api.seedDemo();
      await loadPackages();
    } catch (err) {
      console.error('Failed to seed demo:', err);
    } finally {
      setIsSeeding(false);
    }
  };

  const handleSelectPackage = (id: number) => {
    setSelectedPackageId(id);
    setCurrentTab('package-detail');
  };

  const handleAnalysisCompleted = (pkgId: number) => {
    loadPackages();
    setSelectedPackageId(pkgId);
    setCurrentTab('package-detail');
  };

  return (
    <div className="flex min-h-screen bg-[#090d16] text-slate-100">
      {/* Sidebar Navigation */}
      <Navbar
        currentTab={currentTab}
        onSelectTab={(tab) => {
          setCurrentTab(tab);
          if (tab !== 'package-detail') {
            setSelectedPackageId(null);
          }
        }}
        onSeedDemo={handleSeedDemo}
        isSeeding={isSeeding}
      />

      {/* Main Content View */}
      <main className="flex-1 p-8 lg:p-10 max-w-7xl mx-auto overflow-y-auto">
        {currentTab === 'overview' && (
          <OverviewPage
            packages={packages}
            onSelectPackage={handleSelectPackage}
            onNavigateToAnalyze={() => setCurrentTab('analyze')}
            onSeedDemo={handleSeedDemo}
            isLoading={isLoading}
          />
        )}

        {currentTab === 'analyze' && (
          <AnalyzePage onAnalysisCompleted={handleAnalysisCompleted} />
        )}

        {currentTab === 'package-detail' && selectedPackageId && (
          <PackageDetailPage
            packageId={selectedPackageId}
            onBack={() => {
              setSelectedPackageId(null);
              setCurrentTab('overview');
            }}
          />
        )}

        {currentTab === 'adoption' && <AdoptionPage packages={packages} />}

        {currentTab === 'compare' && <ComparePage packages={packages} />}

        {currentTab === 'settings' && (
          <SettingsPage onSeedDemo={handleSeedDemo} isSeeding={isSeeding} />
        )}
      </main>
    </div>
  );
}

export default App;


