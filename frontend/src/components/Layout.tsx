import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

const authRequired = import.meta.env.VITE_AUTH_REQUIRED === "true";

const links = [
  { to: "/", label: "Dashboard" },
  { to: "/predict", label: "Predict" },
  { to: "/graph", label: "Graph" },
];

export function Layout() {
  const auth = useAuth();

  return (
    <div className="min-h-screen bg-slate-950">
      <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4">
          <div className="flex items-center gap-8">
            <div>
              <p className="font-mono text-xs uppercase tracking-[0.2em] text-brand-400">
                Code Impact
              </p>
              <h1 className="text-lg font-semibold text-white">Predictor AI</h1>
            </div>
            <nav className="hidden gap-1 md:flex">
              {links.map((link) => (
                <NavLink
                  key={link.to}
                  to={link.to}
                  end={link.to === "/"}
                  className={({ isActive }) =>
                    `rounded-lg px-3 py-2 text-sm transition ${
                      isActive
                        ? "bg-brand-500/15 text-brand-400"
                        : "text-slate-400 hover:bg-slate-800 hover:text-white"
                    }`
                  }
                >
                  {link.label}
                </NavLink>
              ))}
            </nav>
          </div>
          <div className="flex items-center gap-4">
            {authRequired && auth.user && (
              <span className="hidden text-sm text-slate-400 sm:inline">{auth.user.email}</span>
            )}
            {!authRequired && (
              <span className="hidden text-xs text-slate-500 sm:inline">Auth disabled</span>
            )}
            {authRequired && (
              <button
                type="button"
                onClick={auth.logout}
                className="rounded-lg border border-slate-700 px-3 py-1.5 text-sm text-slate-300 hover:border-slate-500"
              >
                Logout
              </button>
            )}
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-4 py-8">
        <Outlet />
      </main>
    </div>
  );
}
