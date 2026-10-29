import { ListTodo } from "lucide-react";
import { PageHeader } from "@/components/PageHeader";
import { Badge } from "@/components/ui/badge";
import { Skeleton, SkeletonTable } from "@/components/ui/skeleton";

export function ViewSessionsPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="View Sessions"
        description="Browse, search, duplicate, and analyze historical test execution sessions."
        badge={
          <Badge variant="outline" className="border-brand-500/30 text-brand-700 dark:text-brand-300 bg-brand-50/50 dark:bg-brand-900/20 font-semibold">
            Phase 4
          </Badge>
        }
      />

      <div className="relative">
        {/* Prominent Overlay Card */}
        <div className="absolute inset-0 z-10 flex items-center justify-center p-4">
          <div className="max-w-md w-full rounded-card border border-border bg-surface/95 backdrop-blur-md p-6 sm:p-8 text-center elevation-lg space-y-4">
            <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-primary/15 text-primary elevation-xs">
              <ListTodo className="h-7 w-7" />
            </div>
            <div className="space-y-2">
              <h2 className="text-xl font-bold tracking-tight text-foreground">
                Coming in Phase 4
              </h2>
              <p className="text-sm text-muted-foreground leading-relaxed">
                The paginated test session catalog, environment filtering, session duplication, and read-only execution viewer will arrive in Phase 4.
              </p>
            </div>
          </div>
        </div>

        {/* Static Dimmed Skeleton Layout */}
        <div className="space-y-6 opacity-40 select-none pointer-events-none filter blur-[0.5px]">
          {/* Filter Bar Skeleton */}
          <div className="rounded-card border border-border bg-card p-4 flex flex-wrap items-center justify-between gap-4">
            <Skeleton className="h-9 w-64" />
            <div className="flex items-center gap-2">
              <Skeleton className="h-9 w-28" />
              <Skeleton className="h-9 w-28" />
            </div>
          </div>

          <SkeletonTable rows={6} />
        </div>
      </div>
    </div>
  );
}
