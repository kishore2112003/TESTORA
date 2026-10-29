import React, { Suspense } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { LazyMotion, MotionConfig } from "framer-motion";

import { ProtectedRoute } from "@/components/ProtectedRoute";
import { Toaster } from "@/components/ui/sonner";
import { LoadingProvider, RouteSuspenseFallback } from "@/context/LoadingContext";
import { AppLayout } from "@/layouts/AppLayout";
import { loadFeatures } from "@/lib/motion";

// Lazy-loaded page components for real Suspense progress and minimal initial bundle
const LoginPage = React.lazy(() =>
  import("@/pages/LoginPage").then((m) => ({ default: m.LoginPage }))
);
const DashboardPage = React.lazy(() =>
  import("@/pages/DashboardPage").then((m) => ({ default: m.DashboardPage }))
);
const NewSessionPage = React.lazy(() =>
  import("@/pages/NewSessionPage").then((m) => ({ default: m.NewSessionPage }))
);
const ViewSessionsPage = React.lazy(() =>
  import("@/pages/ViewSessionsPage").then((m) => ({ default: m.ViewSessionsPage }))
);
const ExportPage = React.lazy(() =>
  import("@/pages/ExportPage").then((m) => ({ default: m.ExportPage }))
);
const SettingsPage = React.lazy(() =>
  import("@/pages/SettingsPage").then((m) => ({ default: m.SettingsPage }))
);
const NotFoundPage = React.lazy(() =>
  import("@/pages/NotFoundPage").then((m) => ({ default: m.NotFoundPage }))
);

export function App() {
  return (
    <MotionConfig reducedMotion="user">
      <LazyMotion features={loadFeatures}>
        <LoadingProvider>
          <Suspense fallback={<RouteSuspenseFallback />}>
            <Routes>
              {/* Public Routes */}
              <Route path="/login" element={<LoginPage />} />

              {/* Protected Application Shell */}
              <Route
                element={
                  <ProtectedRoute>
                    <AppLayout />
                  </ProtectedRoute>
                }
              >
                <Route path="/" element={<Navigate to="/dashboard" replace />} />
                <Route path="/dashboard" element={<DashboardPage />} />
                <Route path="/sessions/new" element={<NewSessionPage />} />
                <Route path="/sessions" element={<ViewSessionsPage />} />
                <Route path="/export" element={<ExportPage />} />
                <Route path="/settings" element={<SettingsPage />} />
              </Route>

              {/* 404 Not Found Catch-All */}
              <Route path="*" element={<NotFoundPage />} />
            </Routes>
          </Suspense>

          {/* Global Notification Toasts */}
          <Toaster position="top-right" closeButton richColors />
        </LoadingProvider>
      </LazyMotion>
    </MotionConfig>
  );
}

export default App;
