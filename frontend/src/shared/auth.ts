import { useEffect, useState } from "react";
import { getCurrentUser } from "../api";
import type { CurrentUser } from "../types";

export type RequiredRole = "admin" | "any";

function redirectToLogin(): void {
  const next = encodeURIComponent(window.location.pathname + window.location.search);
  window.location.href = `/login.html?next=${next}`;
}

function satisfiesRole(user: CurrentUser, role: RequiredRole): boolean {
  if (user === null) return false;
  if (role === "admin") return user.is_admin;
  return true;
}

/**
 * Calls GET /auth/me on mount and redirects to the login page when the
 * session doesn't satisfy the required role. While the check is pending,
 * `user` is null and `loading` is true — callers should render nothing (or a
 * spinner) rather than their real content, so a soon-to-redirect visitor
 * never sees a flash of a protected page (the actual enforcement is
 * server-side regardless; this is just to avoid the flash).
 */
export function useRequireRole(role: RequiredRole): { user: CurrentUser; loading: boolean } {
  const [user, setUser] = useState<CurrentUser>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    getCurrentUser()
      .then((current) => {
        if (cancelled) return;
        if (!satisfiesRole(current, role)) {
          redirectToLogin();
          return;
        }
        setUser(current);
        setLoading(false);
      })
      .catch(() => {
        if (cancelled) return;
        redirectToLogin();
      });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return { user, loading };
}
