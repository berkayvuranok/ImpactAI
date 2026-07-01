import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider } from "./auth/AuthContext";
import { ProtectedRoute } from "./auth/ProtectedRoute";
import { Layout } from "./components/Layout";
import { DashboardPage } from "./pages/DashboardPage";
import { GraphPage } from "./pages/GraphPage";
import { LoginPage } from "./pages/LoginPage";
import { PredictPage } from "./pages/PredictPage";
import { PredictionDetailPage } from "./pages/PredictionDetailPage";
import { RegisterPage } from "./pages/RegisterPage";

const authRequired = import.meta.env.VITE_AUTH_REQUIRED === "true";

export function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={authRequired ? <LoginPage /> : <Navigate to="/" replace />} />
          <Route
            path="/register"
            element={authRequired ? <RegisterPage /> : <Navigate to="/" replace />}
          />
          <Route element={<ProtectedRoute />}>
            <Route element={<Layout />}>
              <Route path="/" element={<DashboardPage />} />
              <Route path="/predict" element={<PredictPage />} />
              <Route path="/prediction/:id" element={<PredictionDetailPage />} />
              <Route path="/graph" element={<GraphPage />} />
            </Route>
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
