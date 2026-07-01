import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

const authRequired = import.meta.env.VITE_AUTH_REQUIRED === "true";

export function ProtectedRoute() {
  const { isAuthenticated } = useAuth();

  if (!authRequired || isAuthenticated) {
    return <Outlet />;
  }

  return <Navigate to="/login" replace />;
}
