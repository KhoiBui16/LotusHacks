import { createContext, useContext, useEffect, useState, ReactNode } from "react";

export interface User {
  id?: string;
  name: string;
  email: string;
  avatar?: string;
}

interface AuthContextType {
  user: User | null;
  accessToken: string | null;
  setAuth: (payload: { accessToken: string; user: User }) => void;
  signIn: (user: User) => void;
  signOut: () => void;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  accessToken: null,
  setAuth: () => {},
  signIn: () => {},
  signOut: () => {},
});

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [accessToken, setAccessToken] = useState<string | null>(null);

  useEffect(() => {
    const storedAuth = localStorage.getItem("vetc_auth");
    if (storedAuth) {
      try {
        const parsed = JSON.parse(storedAuth) as { accessToken?: string; user?: User };
        if (parsed.user) setUser(parsed.user);
        if (parsed.accessToken) setAccessToken(parsed.accessToken);
        return;
      } catch {
        void 0;
      }
    }

    const storedUser = localStorage.getItem("vetc_user");
    if (storedUser) {
      try {
        setUser(JSON.parse(storedUser));
      } catch {
        void 0;
      }
    }
  }, []);

  const setAuth = (payload: { accessToken: string; user: User }) => {
    setUser(payload.user);
    setAccessToken(payload.accessToken);
    localStorage.setItem("vetc_auth", JSON.stringify(payload));
    localStorage.setItem("vetc_user", JSON.stringify(payload.user));
  };

  const signIn = (u: User) => {
    setUser(u);
    localStorage.setItem("vetc_user", JSON.stringify(u));
  };

  const signOut = () => {
    setUser(null);
    setAccessToken(null);
    localStorage.removeItem("vetc_auth");
    localStorage.removeItem("vetc_user");
  };

  return (
    <AuthContext.Provider value={{ user, accessToken, setAuth, signIn, signOut }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
