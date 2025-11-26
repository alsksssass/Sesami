/**
 * 인증 컨텍스트
 * 전역 인증 상태 관리
 */
import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
} from "react";
import type { ReactNode } from "react";
import api from "../services/api";

interface User {
  id: string | number;
  github_id: string;
  username: string;
  nickname?: string;
  repo_count?: number;
  email?: string;
  avatar_url?: string;
  created_at: string;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (token: string, userData: User) => void;
  logout: () => void;
  refreshUser: () => Promise<void>;
  optimisticUpdateRepoCount: (count: number) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isInitialized, setIsInitialized] = useState(false);

  const isAuthenticated = !!user;

  // 앱 시작시 토큰 확인 및 사용자 정보 로드
  useEffect(() => {
    if (isInitialized) return; // 이미 초기화되었으면 실행하지 않음

    const initAuth = async () => {
      const token = localStorage.getItem("access_token");
      if (token) {
        try {
          const userData = await api.auth.getCurrentUser();
          setUser(userData);
        } catch (error) {
          console.error("Failed to load user:", error);
          localStorage.removeItem("access_token");
        }
      }
      setIsLoading(false);
      setIsInitialized(true);
    };

    initAuth();
  }, [isInitialized]);

  const login = useCallback((token: string, userData: User) => {
    localStorage.setItem("access_token", token);
    setUser(userData);
    setIsLoading(false);
    setIsInitialized(true); // 로그인 시 초기화 완료로 표시
  }, []);

  const logout = async () => {
    try {
      await api.auth.logout();
    } catch (error) {
      console.error("Logout error:", error);
    } finally {
      localStorage.removeItem("access_token");
      setUser(null);
    }
  };

  const refreshUser = async () => {
    try {
      const userData = await api.auth.getCurrentUser();
      setUser(userData);
    } catch (error) {
      console.error("Failed to refresh user:", error);
      logout();
    }
  };

  const optimisticUpdateRepoCount = useCallback((count: number) => {
    setUser((prevUser) => {
      if (!prevUser) return null;
      return {
        ...prevUser,
        repo_count: count,
      };
    });
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated,
        isLoading,
        login,
        logout,
        refreshUser,
        optimisticUpdateRepoCount,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
