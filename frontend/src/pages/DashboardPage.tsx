import { LayoutDashboard } from "lucide-react";
import { PageHeader } from "@/components/PageHeader";
import { Badge, StatusBadge } from "@/components/ui/badge";
import { Skeleton, SkeletonCard, SkeletonTable } from "@/components/ui/skeleton";

export function DashboardPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Dashboard"
        description="Real-time test session metrics, ticket coverage, and QA health."
        badge={
          <Badge variant="outline" className="border-brand-500/30 text-brand-700 dark:text-brand-300 bg-brand-50/50 dark:bg-brand-900/20 font-semibold">
            Phase 6
          </Badge>
        }
      />

      {/* Relative container with static dimmed skeleton behind prominent message */}
      <div className="relative">
        {/* Prominent Overlay Card */}
        <div className="absolute inset-0 z-10 flex items-center justify-center p-4">
          <div className="max-w-md w-full rounded-card border border-border bg-surface/95 backdrop-blur-md p-6 sm:p-8 text-center elevation-lg space-y-4">
            <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-primary/15 text-primary elevation-xs">
              <LayoutDashboard className="h-7 w-7" />
            </div>
            <div className="space-y-2">
              <h2 className="text-xl font-bold tracking-tight text-foreground">
                Coming in Phase 6
              </h2>
              <p className="text-sm text-muted-foreground leading-relaxed">
                The full executive dashboard with session pass/fail trends, ticket coverage analytics, and quick execution widgets will arrive in Phase 6.
              </p>
            </div>
            <div className="pt-2 flex flex-wrap items-center justify-center gap-2">
              <StatusBadge status="pass" label="Pass" />
              <StatusBadge status="fail" label="Fail" />
              <StatusBadge status="blocked" label="Blocked" />
              <StatusBadge status="skipped" label="Skipped" />
            </div>
          </div>
        </div>

        {/* Static Dimmed Skeleton Layout (No shimmer) */}
        <div className="space-y-6 opacity-40 select-none pointer-events-none filter blur-[0.5px]">
          {/* Stat Cards Row */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <SkeletonCard />
            <SkeletonCard />
            <SkeletonCard />
            <SkeletonCard />
          </div>

          {/* Grid: Chart & Recent Table */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 rounded-card border border-border bg-card p-6 space-y-4">
              <div className="flex items-center justify-between">
                <Skeleton className="h-5 w-40" />
                <Skeleton className="h-4 w-24" />
              </div>
              <div className="h-64 flex items-end gap-3 pt-6">
                {[45, 60, 30, 80, 65, 90, 75, 85, 95, 70, 80, 100].map((h, i) => (
                  <div key={i} className="flex-1 flex flex-col items-center gap-2 h-full justify-end">
                    <Skeleton className="w-full rounded-t-sm" style={{ height: `${h}%` }} />
                    <Skeleton className="h-3 w-4" />
                  </div>
                ))}
              </div>
            </div>

            <div className="rounded-card border border-border bg-card p-6 space-y-4">
              <Skeleton className="h-5 w-32" />
              <div className="space-y-3">
                {Array.from({ length: 4 }).map((_, i) => (
                  <div key={i} className="flex items-center justify-between py-2 border-b border-border/50">
                    <div className="space-y-1">
                      <Skeleton className="h-4 w-28" />
                      <Skeleton className="h-3 w-16" />
                    </div>
                    <Skeleton className="h-6 w-14 rounded-full" />
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Sessions Table Skeleton */}
          <SkeletonTable rows={4} />
        </div>
      </div>
    </div>
  );
}
