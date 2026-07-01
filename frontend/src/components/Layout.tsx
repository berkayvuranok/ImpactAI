import { NavLink, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

const authRequired = import.meta.env.VITE_AUTH_REQUIRED === "true";

const links = [
  { to: "/", label: "Dashboard", num: "01" },
  { to: "/predict", label: "Predict", num: "02" },
  { to: "/graph", label: "Graph", num: "03" },
  { to: "/evaluate", label: "Evaluate", num: "04" },
];

export function Layout() {
  const auth = useAuth();
  const location = useLocation();

  return (
    <div className="grain min-h-screen bg-ink">
      <header className="sticky top-0 z-40 border-b border-ink-300/60 bg-ink/80 backdrop-blur-xl">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-5 py-4">
          <NavLink to="/" className="group flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-full border border-ink-400 font-heading text-sm font-bold text-ink-900 transition group-hover:bg-ink-900 group-hover:text-ink">
              CI
            </div>
            <div className="hidden sm:block">
              <p className="font-heading text-sm font-semibold text-ink-900">Code Impact</p>
              <p className="font-mono text-[10px] uppercase tracking-widest text-ink-500">
                Predictor AI
              </p>
            </div>
          </NavLink>

          <nav className="hidden items-center gap-1 md:flex">
            {links.map((link) => (
              <NavLink
                key={link.to}
                to={link.to}
                end={link.to === "/"}
                className={({ isActive }) =>
                  `group relative rounded-full px-4 py-2 text-sm transition ${
                    isActive ? "text-ink-900" : "text-ink-500 hover:text-ink-700"
                  }`
                }
              >
                {({ isActive }) => (
                  <>
                    <span className="font-mono text-[10px] text-ink-400">{link.num}</span>
                    <span className="ml-2 font-medium">{link.label}</span>
                    {isActive && (
                      <span className="absolute inset-x-3 -bottom-px h-px bg-ink-900 animate-pulse-line" />
                    )}
                  </>
                )}
              </NavLink>
            ))}
          </nav>

          <div className="flex items-center gap-3">
            {authRequired && auth.user && (
              <span className="hidden max-w-[140px] truncate font-mono text-xs text-ink-500 lg:inline">
                {auth.user.email}
              </span>
            )}
            {!authRequired && (
              <span className="hidden rounded-full border border-ink-300 px-3 py-1 font-mono text-[10px] uppercase tracking-wider text-ink-500 sm:inline">
                Dev mode
              </span>
            )}
            {authRequired && (
              <button type="button" onClick={auth.logout} className="btn-ghost !px-4 !py-1.5 !text-xs">
                Logout
              </button>
            )}
          </div>
        </div>

        {/* Mobile nav */}
        <nav className="flex border-t border-ink-300/40 md:hidden">
          {links.map((link) => {
            const active =
              link.to === "/"
                ? location.pathname === "/"
                : location.pathname.startsWith(link.to);
            return (
              <NavLink
                key={link.to}
                to={link.to}
                end={link.to === "/"}
                className={`flex-1 py-3 text-center text-xs font-medium transition ${
                  active ? "bg-ink-100 text-ink-900" : "text-ink-500"
                }`}
              >
                {link.label}
              </NavLink>
            );
          })}
        </nav>
      </header>

      <main className="mx-auto max-w-7xl px-5 pb-24">
        <Outlet />
      </main>
    </div>
  );
}
