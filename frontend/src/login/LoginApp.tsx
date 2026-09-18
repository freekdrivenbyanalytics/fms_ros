import { useState, type FormEvent } from "react";
import { login, signup } from "../api";

function nextTarget(): string | null {
  const params = new URLSearchParams(window.location.search);
  return params.get("next");
}

function defaultTarget(isAdmin: boolean): string {
  return isAdmin ? "/index.html" : "/customer-portal.html";
}

export function LoginApp() {
  const [mode, setMode] = useState<"login" | "signup">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [signedUp, setSignedUp] = useState(false);

  function redirectAfterLogin(isAdmin: boolean) {
    window.location.href = nextTarget() ?? defaultTarget(isAdmin);
  }

  async function handleLogin(event: FormEvent) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const user = await login({ email, password });
      if (user === null) {
        setError("Incorrect email or password");
        return;
      }
      redirectAfterLogin(user.is_admin);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to log in");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleSignup(event: FormEvent) {
    event.preventDefault();
    setError(null);
    if (password !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }
    setSubmitting(true);
    try {
      await signup({ email, password });
      setSignedUp(true);
      setMode("login");
      setPassword("");
      setConfirmPassword("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to sign up");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
      <div className="w-full max-w-sm bg-white rounded-lg border border-slate-200 p-6">
        <h1 className="text-lg font-semibold text-slate-900 mb-4">
          {mode === "login" ? "Log In" : "Create Account"}
        </h1>

        {signedUp && mode === "login" && (
          <p className="text-sm text-emerald-700 mb-3">
            Account created. You can log in now, but you won't see any data until an
            admin grants you access.
          </p>
        )}

        <form onSubmit={mode === "login" ? handleLogin : handleSignup} className="space-y-3">
          <input
            type="text"
            required
            placeholder="Email or username"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            className="w-full text-sm border border-slate-300 rounded-md px-3 py-2"
          />
          <input
            type="password"
            required
            placeholder="Password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            className="w-full text-sm border border-slate-300 rounded-md px-3 py-2"
          />
          {mode === "signup" && (
            <input
              type="password"
              required
              placeholder="Confirm password"
              value={confirmPassword}
              onChange={(event) => setConfirmPassword(event.target.value)}
              className="w-full text-sm border border-slate-300 rounded-md px-3 py-2"
            />
          )}

          {error && <p className="text-sm text-red-600">{error}</p>}

          <button
            type="submit"
            disabled={submitting}
            className="w-full rounded-md bg-slate-900 px-3 py-2 text-sm font-medium text-white disabled:opacity-50"
          >
            {submitting
              ? mode === "login"
                ? "Logging in…"
                : "Creating account…"
              : mode === "login"
                ? "Log In"
                : "Create Account"}
          </button>
        </form>

        <button
          type="button"
          onClick={() => {
            setMode(mode === "login" ? "signup" : "login");
            setError(null);
          }}
          className="mt-4 text-sm text-slate-500 hover:text-slate-800 underline"
        >
          {mode === "login" ? "Create an account" : "Back to log in"}
        </button>
      </div>
    </div>
  );
}
