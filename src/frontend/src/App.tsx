import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import Login from './pages/Login';
import AuthCallback from './pages/AuthCallback';
import Home from './pages/Home';
import Repositories from './pages/Repositories';
import NewAnalysis from './pages/analysis/NewAnalysis';
import AnalysisStatus from './pages/analysis/AnalysisStatus';
import AnalysisResult from './pages/analysis/AnalysisResult';
import AnalysisHistory from './pages/analysis/AnalysisHistory';

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/auth/callback" element={<AuthCallback />} />
          <Route path="/" element={<Home />} />
          <Route path="/repositories" element={<Repositories />} />
          <Route path="/analysis/new" element={<NewAnalysis />} />
          <Route path="/analysis/history" element={<AnalysisHistory />} />
          <Route path="/analysis/:analysisId" element={<AnalysisStatus />} />
          <Route path="/analysis/:analysisId/result" element={<AnalysisResult />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
