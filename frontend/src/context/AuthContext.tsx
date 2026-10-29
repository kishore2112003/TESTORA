import React, { createContext, useContext, useState, useEffect, useRef } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";

import { api } from "@/lib/api";
import { AuthContextType, LoginCredentials, LoginResponse, User } from "@/types/auth";

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const [isInitialColdLoad, setIsInitialColdLoad] = useState(true);
  const mountTimeRef = useRef(Date.now());

  // Query /api/v1/auth/me to check active session
  const {
    data: user,
    isLoading,
    refetch,
  } = useQuery<User | null>({
    queryKey: ["auth", "me"],
    queryFn: async () => {
      try {
        const currentUser = await api.get<User>("/api/v1/auth/me");
        return currentUser;
      } catch {
        return null;
      }
    },
    staleTime: 5 * 60 * 1000,
    retry: false,
    refetchOnWindowFocus: true,
  });

  // Apply ~400ms minimum only on the first cold load
  useEffect(() => {
    if (!isLoading && isInitialColdLoad) {
      const elapsed = Date.now() - mountTimeRef.current;
      const delay = Math.max(0, 400 - elapsed);
      const timer = setTimeout(() => {
        setIsInitialColdLoad(false);
      }, delay);
      return () => clearTimeout(timer);
    }
  }, [isLoading, isInitialColdLoad]);

  const login = async (credentials: LoginCredentials): Promise<User> => {
    const response = await api.post<LoginResponse>(
      "/api/v1/auth/login",
      credentials
    );
    queryClient.setQueryData(["auth", "me"], response.user);
    return response.user;
  };

  const logout = async (): Promise<void> => {
    try {
      await api.post("/api/v1/auth/logout");
    } catch {
      // Proceed even if network request fails
    } finally {
      queryClient.clear();
      navigate("/login", { replace: true });
    }
  };

  const refetchUser = async (): Promise<void> => {
    await refetch();
  };

  return (
    <AuthContext.Provider
      value={{
        user: user ?? null,
        isLoading,
        isInitialColdLoad,
        login,
        logout,
        refetchUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
