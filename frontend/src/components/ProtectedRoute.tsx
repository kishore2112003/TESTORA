import React from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { StartupLoader } from "@/components/StartupLoader";

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, isInitialColdLoad } = useAuth();
  const location = useLocation();

  if (isInitialColdLoad) {
    return <StartupLoader />;
  }

  if (!user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <>{children}</>;
}
