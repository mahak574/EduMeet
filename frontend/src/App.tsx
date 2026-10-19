import React, { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore } from './stores/authStore';
import { Layout } from './components/layout/Layout';
import { DashboardOverview } from './features/dashboard/DashboardOverview';
import { ProfilePage } from './features/profile/ProfilePage';
import { LiveSessionRoom } from './features/session/LiveSessionRoom';
import { MistakeJournalView } from './features/reviews/MistakeJournalView';
import { PublicPortfolioView } from './features/portfolio/PublicPortfolioView';

// Placeholder views for subsequent phases
const PhasePlaceholder: React.FC<{ title: string; phase: string; description: string }> = ({
  title,
  phase,
  description,
}) => (
  <div className="glass-panel p-8 rounded-2xl border border-white/10 text-center max-w-xl mx-auto my-12 space-y-4 animate-in fade-in">
    <span className="px-3 py-1 rounded-full bg-brand-500/20 text-brand-300 border border-brand-500/30 text-xs font-semibold uppercase">
      {phase}
    </span>
    <h2 className="text-2xl font-bold text-white font-sans">{title}</h2>
    <p className="text-slate-400 text-sm leading-relaxed">{description}</p>
  </div>
);

export const App: React.FC = () => {
  const { initAuth } = useAuthStore();

  useEffect(() => {
    initAuth();
  }, [initAuth]);

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<DashboardOverview />} />
          <Route path="profile" element={<ProfilePage />} />
          <Route
            path="diagnostic"
            element={
              <PhasePlaceholder
                title="Diagnostic Quiz Engine"
                phase="Phase 2"
                description="Server-enforced single question delivery with anti-cheat deterrence, 7-day attempt intervals, and topic-level Bayesian skill profiling."
              />
            }
          />
          <Route
            path="matching"
            element={
              <PhasePlaceholder
                title="Reciprocal Matching Engine"
                phase="Phase 3"
                description="Graph-based maximum weight matching (NetworkX) computing optimal complementary topic pairs with availability and language hard constraints."
              />
            }
          />
          <Route
            path="sessions"
            element={
              <PhasePlaceholder
                title="Live Session Room"
                phase="Phase 4"
                description="Server-synchronized 60-minute session room with automated 25/25 role switching, Jitsi Meet iframe, Monaco editor + Yjs collaboration, and SQLite WASM."
              />
            }
          />
          <Route path="mistakes" element={<MistakeJournalView />} />
          <Route path="portfolio/:slug" element={<PublicPortfolioView />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
        <Route path="/session/:sessionId" element={<LiveSessionRoom />} />
        <Route path="/p/:slug" element={<PublicPortfolioView />} />
      </Routes>
    </BrowserRouter>
  );
};

export default App;
