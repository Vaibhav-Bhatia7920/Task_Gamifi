import { useState } from "react";
import { Navigate, useLocation } from "react-router-dom";
import { loginRequest, signupRequest } from "../api";
import { useAuth } from "../auth";

export default function LoginPage() {
  const { token, login } = useAuth();
  const location = useLocation();
  const [mode, setMode] = useState("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  if (token) {
    const next = location.state?.from?.pathname || "/tasks";
    return <Navigate to={next} replace />;
  }

  async function onSubmit(event) {
    event.preventDefault();
    setError("");
    setBusy(true);
    try {
      if (mode === "signup") {
        await signupRequest(email, password);
      }
      const result = await loginRequest(email, password);
      login(result.access_token, result.user);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="shell auth-shell">
      <div className="panel auth-panel">
        <p className="eyebrow">Task Gamifi</p>
        <h1>Open sky, clear path</h1>
        <p className="lede">
          Sign in to see your paths, or create an account and start a new one.
        </p>
        <div className="tabs">
          <button
            type="button"
            className={mode === "login" ? "tab active" : "tab"}
            onClick={() => setMode("login")}
          >
            Login
          </button>
          <button
            type="button"
            className={mode === "signup" ? "tab active" : "tab"}
            onClick={() => setMode("signup")}
          >
            Sign up
          </button>
        </div>
        <form onSubmit={onSubmit} className="stack">
          <label>
            Email
            <input
              type="email"
              autoComplete="username"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              required
            />
          </label>
          <label>
            Password
            <input
              type="password"
              autoComplete={mode === "signup" ? "new-password" : "current-password"}
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              minLength={8}
              required
            />
          </label>
          {error ? <p className="error">{error}</p> : null}
          <button className="primary" type="submit" disabled={busy}>
            {busy ? "Working..." : mode === "signup" ? "Create account" : "Log in"}
          </button>
        </form>
      </div>
    </div>
  );
}
