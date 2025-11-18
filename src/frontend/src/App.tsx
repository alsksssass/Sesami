import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "./contexts/AuthContext";
import { Header } from "./components/Header";
import Login from "./pages/Login";
import AuthCallback from "./pages/AuthCallback";
import Home from "./pages/Home";
import Profile from "./pages/Profile";
import Repositories from "./pages/Repositories";
import NewAnalysis from "./pages/analysis/NewAnalysis";
import AnalysisStatus from "./pages/analysis/AnalysisStatus";
import AnalysisResult from "./pages/analysis/AnalysisResult";
import AnalysisHistory from "./pages/analysis/AnalysisHistory";
import EvaluateChart from "./pages/EvaluateChart";

function App() {
  return (
    <div className="fixed inset-0 overflow-auto bg-gray-50">
      <BrowserRouter>
        <AuthProvider>
          <Header />
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/auth/callback" element={<AuthCallback />} />
            <Route path="/" element={<Home />} />
            <Route path="/profile" element={<Profile />} />
            <Route path="/repositories" element={<Repositories />} />
            <Route path="/analysis/new" element={<NewAnalysis />} />
            <Route path="/analysis/history" element={<AnalysisHistory />} />
            <Route path="/analysis/:analysisId" element={<AnalysisStatus />} />
            <Route
              path="/analysis/:analysisId/result"
              element={<AnalysisResult />}
            />
            <Route path="/evaluatechart" element={<EvaluateChart />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </AuthProvider>
      </BrowserRouter>
    </div>
  );
}

export default App;
