import React, { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore } from './stores/authStore';
import { Layout } from './components/layout/Layout';
import { DashboardOverview } from './features/dashboard/DashboardOverview';
import { ProfilePage } from './features/profile/ProfilePage';
import { DiagnosticHubPage } from './features/quiz/DiagnosticHubPage';
import { MatchingHubPage } from './features/matching/MatchingHubPage';
import { SessionsHubPage } from './features/session/SessionsHubPage';
import { LiveSessionRoom } from './features/session/LiveSessionRoom';
import { MistakeJournalView } from './features/reviews/MistakeJournalView';
import { PublicPortfolioView } from './features/portfolio/PublicPortfolioView';

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
          <Route path="diagnostic" element={<DiagnosticHubPage />} />
          <Route path="matching" element={<MatchingHubPage />} />
          <Route path="sessions" element={<SessionsHubPage />} />
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
