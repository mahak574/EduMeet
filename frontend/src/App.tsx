import React, { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore } from './stores/authStore';
import { Layout } from './components/layout/Layout';
import { ProtectedRoute } from './components/auth/ProtectedRoute';
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
          {/* Public Overview (unauthenticated) or Summary Dashboard (authenticated) */}
          <Route index element={<DashboardOverview />} />

          {/* Strictly Protected Authenticated Tabs */}
          <Route
            path="profile"
            element={
              <ProtectedRoute>
                <ProfilePage />
              </ProtectedRoute>
            }
          />
          <Route
            path="diagnostic"
            element={
              <ProtectedRoute>
                <DiagnosticHubPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="matching"
            element={
              <ProtectedRoute>
                <MatchingHubPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="sessions"
            element={
              <ProtectedRoute>
                <SessionsHubPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="mistakes"
            element={
              <ProtectedRoute>
                <MistakeJournalView />
              </ProtectedRoute>
            }
          />

          {/* Public Portfolio */}
          <Route path="portfolio/:slug" element={<PublicPortfolioView />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>

        {/* Protected Live Interactive Session Workspace */}
        <Route
          path="/session/:sessionId"
          element={
            <ProtectedRoute>
              <LiveSessionRoom />
            </ProtectedRoute>
          }
        />
        <Route path="/p/:slug" element={<PublicPortfolioView />} />
      </Routes>
    </BrowserRouter>
  );
};

export default App;
