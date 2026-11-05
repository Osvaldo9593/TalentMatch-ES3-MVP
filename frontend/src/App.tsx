import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Header } from './components/Header';
import { DashboardPage } from './pages/DashboardPage';
import { JobOfferListPage } from './pages/JobOfferListPage';
import { JobOfferCreatePage } from './pages/JobOfferCreatePage';
import { JobOfferDetailPage } from './pages/JobOfferDetailPage';
import { JobOfferEditPage } from './pages/JobOfferEditPage';
import { SystemStatusPage } from './pages/SystemStatusPage';
import { apiService } from './services/api';
import { AuthProvider } from './context/AuthContext';
import { ProtectedRoute } from './components/ProtectedRoute';
import { LoginPage } from './pages/LoginPage';

export function App() {
  return (
    <AuthProvider>
    <BrowserRouter>
      <div className="min-h-screen bg-[#FBFBFA] flex flex-col justify-between text-[#111111] selection:bg-[#111111] selection:text-white">
        {/* Navigation Header */}
        <Header apiUrl={apiService.getBaseUrl()} />

        {/* Main Routed Content */}
        <main className="flex-grow flex flex-col">
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route element={<ProtectedRoute />}>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/job-offers" element={<JobOfferListPage />} />
            <Route path="/job-offers/new" element={<JobOfferCreatePage />} />
            <Route path="/job-offers/:id" element={<JobOfferDetailPage />} />
            <Route path="/job-offers/:id/edit" element={<JobOfferEditPage />} />
            <Route path="/system-status" element={<SystemStatusPage />} />
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
            </Route>
          </Routes>
        </main>

        {/* Global Footer */}
        <footer className="w-full border-t border-[#EAEAEA] py-6 bg-white">
          <div className="max-w-5xl mx-auto px-6 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-[#787774]">
            <div className="flex items-center gap-2">
              <span className="font-semibold text-[#111111]">TalentMatch</span>
              <span>· Sistema de Clasificación de CVs con IA</span>
            </div>
            <div className="font-mono text-[11px]">
              FastAPI · SQLAlchemy · Alembic · PostgreSQL · React
            </div>
          </div>
        </footer>
      </div>
    </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
