import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { api } from "../api/client";
import type { User } from "../api/types";

interface AuthContextValue {
  user: User | null;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, username: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

function loadUser(): User | null {
  const raw = localStorage.getItem("user");
  return raw ? (JSON.parse(raw) as User) : null;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(loadUser);

  const persist = useCallback((auth: { access_token: string; refresh_token: string; user: User }) => {
    localStorage.setItem("access_token", auth.access_token);
    localStorage.setItem("refresh_token", auth.refresh_token);
    localStorage.setItem("user", JSON.stringify(auth.user));
    setUser(auth.user);
  }, []);

  const login = useCallback(
    async (email: string, password: string) => {
      const auth = await api.login(email, password);
      persist(auth);
    },
    [persist],
  );

  const register = useCallback(
    async (email: string, username: string, password: string) => {
      const auth = await api.register(email, username, password);
      persist(auth);
    },
    [persist],
  );

  const logout = useCallback(() => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    localStorage.removeItem("user");
    setUser(null);
  }, []);

  useEffect(() => {
    if (!localStorage.getItem("access_token")) {
      setUser(null);
    }
  }, []);

  const value = useMemo(
    () => ({
      user,
      isAuthenticated: Boolean(user && localStorage.getItem("access_token")),
      login,
      register,
      logout,
    }),
    [user, login, register, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
