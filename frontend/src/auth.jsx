import { createContext, useContext, useMemo, useState } from "react";
import { Navigate, useLocation } from "react-router-dom";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem("tg_token") || "");
  const [user, setUser] = useState(() => {
    const raw = localStorage.getItem("tg_user");
    return raw ? JSON.parse(raw) : null;
  });

  const value = useMemo(
    () => ({
      token,
      user,
      login(nextToken, nextUser) {
        localStorage.setItem("tg_token", nextToken);
        localStorage.setItem("tg_user", JSON.stringify(nextUser));
        setToken(nextToken);
        setUser(nextUser);
      },
      logout() {
        localStorage.removeItem("tg_token");
        localStorage.removeItem("tg_user");
        setToken("");
        setUser(null);
      },
    }),
    [token, user],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  return useContext(AuthContext);
}

export function RequireAuth({ children }) {
  const { token } = useAuth();
  const location = useLocation();
  if (!token) {
    return <Navigate to="/" replace state={{ from: location }} />;
  }
  return children;
}
