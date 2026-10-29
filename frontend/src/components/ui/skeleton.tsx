import * as React from "react";
import { cn } from "@/lib/utils";

interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
  shimmer?: boolean;
}

function Skeleton({ className, shimmer = false, ...props }: SkeletonProps) {
  return (
    <div
      className={cn(
        "rounded-control bg-muted/60",
        shimmer ? "animate-pulse" : "opacity-60",
        className
      )}
      {...props}
    />
  );
}

function SkeletonCard({ className, shimmer = false }: { className?: string; shimmer?: boolean }) {
  return (
    <div
      className={cn(
        "rounded-card border border-border bg-card p-5 space-y-3",
        shimmer ? "animate-pulse" : "opacity-65",
        className
      )}
    >
      <div className="flex items-center justify-between">
        <Skeleton shimmer={shimmer} className="h-4 w-28" />
        <Skeleton shimmer={shimmer} className="h-7 w-7 rounded-full" />
      </div>
      <Skeleton shimmer={shimmer} className="h-8 w-20" />
      <Skeleton shimmer={shimmer} className="h-3 w-36" />
    </div>
  );
}

function SkeletonTable({ rows = 4, shimmer = false }: { rows?: number; shimmer?: boolean }) {
  return (
    <div
      className={cn(
        "rounded-card border border-border bg-card overflow-hidden",
        shimmer ? "animate-pulse" : "opacity-65"
      )}
    >
      <div className="border-b border-border bg-muted/30 px-6 py-3 flex gap-4">
        <Skeleton shimmer={shimmer} className="h-4 w-24" />
        <Skeleton shimmer={shimmer} className="h-4 w-48" />
        <Skeleton shimmer={shimmer} className="h-4 w-20 ml-auto" />
      </div>
      <div className="divide-y divide-border">
        {Array.from({ length: rows }).map((_, i) => (
          <div key={i} className="px-6 py-4 flex items-center gap-4">
            <Skeleton shimmer={shimmer} className="h-4 w-20" />
            <Skeleton shimmer={shimmer} className="h-4 w-64" />
            <Skeleton shimmer={shimmer} className="h-6 w-16 rounded-full ml-auto" />
          </div>
        ))}
      </div>
    </div>
  );
}

export { Skeleton, SkeletonCard, SkeletonTable };
