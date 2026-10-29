import React, { createContext, useContext, useState, useCallback, useEffect } from "react";

interface LoadingContextType {
  isLoading: boolean;
  startLoading: () => void;
  stopLoading: () => void;
}

const LoadingContext = createContext<LoadingContextType | undefined>(undefined);

export function LoadingProvider({ children }: { children: React.ReactNode }) {
  const [loadingCount, setLoadingCount] = useState(0);

  const startLoading = useCallback(() => {
    setLoadingCount((c) => c + 1);
  }, []);

  const stopLoading = useCallback(() => {
    setLoadingCount((c) => Math.max(0, c - 1));
  }, []);

  const isLoading = loadingCount > 0;

  return (
    <LoadingContext.Provider value={{ isLoading, startLoading, stopLoading }}>
      {children}
    </LoadingContext.Provider>
  );
}

export function useRouteLoading() {
  const context = useContext(LoadingContext);
  if (!context) {
    throw new Error("useRouteLoading must be used within LoadingProvider");
  }
  return context;
}

/**
 * RouteSuspenseFallback mounts while a lazy component is fetching chunks.
 * On mount it increments the loading count; on unmount it decrements it.
 */
export function RouteSuspenseFallback() {
  const { startLoading, stopLoading } = useRouteLoading();

  useEffect(() => {
    startLoading();
    return () => {
      stopLoading();
    };
  }, [startLoading, stopLoading]);

  return (
    <div className="w-full py-8 space-y-6 animate-in fade-in duration-150">
      <div className="h-8 w-48 rounded-control bg-muted/50" />
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="h-28 rounded-card bg-muted/40 border border-border/50" />
        ))}
      </div>
    </div>
  );
}
