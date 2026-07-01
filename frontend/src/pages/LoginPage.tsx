import { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ApiError } from "../api/client";
import { useAuth } from "../auth/AuthContext";

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await login(email, password);
      navigate("/");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="grain flex min-h-screen items-center justify-center bg-ink px-5">
      <div className="w-full max-w-md">
        <div className="mb-10 text-center">
          <div className="mx-auto mb-6 flex h-14 w-14 items-center justify-center rounded-full border border-ink-400 font-heading text-lg font-bold">
            CI
          </div>
          <p className="section-label">Sign In</p>
          <h1 className="mt-3 font-heading text-3xl font-bold text-ink-900">Welcome back</h1>
        </div>

        <form onSubmit={handleSubmit} className="panel space-y-5 p-8">
          <label className="block">
            <span className="section-label">Email</span>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="input-field mt-2"
            />
          </label>
          <label className="block">
            <span className="section-label">Password</span>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="input-field mt-2"
            />
          </label>
          {error && <p className="font-mono text-sm text-ink-600">{error}</p>}
          <button type="submit" disabled={loading} className="btn-primary w-full">
            {loading ? "Signing in…" : "Sign in →"}
          </button>
        </form>

        <p className="mt-8 text-center font-mono text-xs text-ink-500">
          No account?{" "}
          <Link to="/register" className="text-ink-800 underline underline-offset-4 hover:text-ink-900">
            Register
          </Link>
        </p>
      </div>
    </div>
  );
}
